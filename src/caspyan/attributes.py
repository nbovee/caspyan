import json
import logging
import os
from collections import OrderedDict
from typing import Any
from urllib.request import urlopen

logger = logging.getLogger(__name__)

ATTRIBUTES_JSON_URL_ENV = "ATTRIBUTES_JSON_URL"
DEFAULT_FALLBACK_ENV = "CAS_ATTRIBUTES_DEFAULT_FALLBACK"
MERGE_DEFAULT_ENV = "CAS_ATTRIBUTES_MERGE_DEFAULT"

DEFAULT_USER_KEY = "DEFAULT"


class AttributeValue:
    """A named attribute with a value."""

    def __init__(self, name: str, value: object) -> None:
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return f"AttributeValue({self.name!r}={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AttributeValue):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))


class AttributesService:
    """Provides user attributes from a JSON data source."""

    def __init__(
        self,
        data: dict[str, Any],
        *,
        default_fallback: bool = False,
        merge_default: bool = False,
    ) -> None:
        self._data = data
        self._default_fallback = default_fallback
        self._merge_default = merge_default

    def get_attributes(self, username: str) -> list[AttributeValue]:
        """Get attributes for a user, resolving inheritance."""
        result: OrderedDict[str, list[AttributeValue]] = OrderedDict()

        if (
            self._merge_default
            and username != DEFAULT_USER_KEY
            and DEFAULT_USER_KEY in self._data
        ):
            self._collect_into(DEFAULT_USER_KEY, set(), result)

        self._collect_into(username, set(), result)
        return [attr for attrs in result.values() for attr in attrs]

    def _collect_into(
        self,
        username: str,
        seen: set[str],
        output: OrderedDict[str, list[AttributeValue]],
    ) -> None:
        if username in seen:
            raise ValueError(f"circular inherit detected for user {username!r}")
        seen.add(username)

        user_entry = self._data.get(username)
        if user_entry is None:
            if (
                self._default_fallback
                and username != DEFAULT_USER_KEY
                and DEFAULT_USER_KEY in self._data
            ):
                self._collect_into(DEFAULT_USER_KEY, seen, output)
            return

        inherit_from = user_entry.get("inherit")
        if inherit_from is not None:
            if isinstance(inherit_from, list):
                for parent in inherit_from:
                    self._collect_into(str(parent), seen, output)
            else:
                self._collect_into(str(inherit_from), seen, output)

        attrs = user_entry.get("attributes")
        if isinstance(attrs, dict):
            for name, value in attrs.items():
                if isinstance(value, list):
                    output[name] = [AttributeValue(name, item) for item in value]
                elif value is not None:
                    output[name] = [AttributeValue(name, value)]


def _env_bool(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in ("1", "true", "yes", "on")


def create_attributes_service() -> AttributesService | None:
    """Create an AttributesService if ATTRIBUTES_JSON_URL is configured."""
    url = os.environ.get(ATTRIBUTES_JSON_URL_ENV)
    if not url:
        return None

    try:
        with urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        logger.exception("failed to load attributes JSON from %s", url)
        return None

    if not isinstance(data, dict):
        logger.warning("attributes JSON from %s is not a JSON object", url)
        return None

    default_fallback = _env_bool(DEFAULT_FALLBACK_ENV)
    merge_default = _env_bool(MERGE_DEFAULT_ENV)

    logger.info("loaded attributes for %d users from %s", len(data), url)
    logger.info("default_fallback=%s merge_default=%s", default_fallback, merge_default)
    return AttributesService(
        data, default_fallback=default_fallback, merge_default=merge_default
    )
