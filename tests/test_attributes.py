from unittest.mock import patch

from caspyan.attributes import (
    ATTRIBUTES_JSON_URL_ENV,
    AttributesService,
    AttributeValue,
    create_attributes_service,
)


def test_empty_attributes():
    service = AttributesService({})
    assert service.get_attributes("nonexistent") == []


def test_simple_attributes():
    data = {
        "user1": {
            "attributes": {
                "email": "user1@example.com",
                "role": "admin",
            }
        }
    }
    service = AttributesService(data)
    attrs = service.get_attributes("user1")

    assert AttributeValue("email", "user1@example.com") in attrs
    assert AttributeValue("role", "admin") in attrs


def test_inherit_attributes():
    data = {
        "DEFAULT": {
            "attributes": {
                "affiliation": "employee",
            }
        },
        "john": {
            "inherit": "DEFAULT",
            "attributes": {
                "displayName": "John Doe",
            },
        },
    }
    service = AttributesService(data)
    attrs = service.get_attributes("john")

    assert AttributeValue("affiliation", "employee") in attrs
    assert AttributeValue("displayName", "John Doe") in attrs
    assert len(attrs) == 2


def test_multi_valued_array():
    data = {
        "user1": {
            "attributes": {
                "groupMembership": ["admin", "power-user"],
            }
        }
    }
    service = AttributesService(data)
    attrs = service.get_attributes("user1")

    assert AttributeValue("groupMembership", "admin") in attrs
    assert AttributeValue("groupMembership", "power-user") in attrs
    assert len(attrs) == 2


def test_circular_inherit_detection():
    data = {
        "a": {"inherit": "b"},
        "b": {"inherit": "a"},
    }
    service = AttributesService(data)
    try:
        service.get_attributes("a")
        assert False, "should have raised"
    except ValueError as e:
        assert "circular" in str(e).lower()


def test_numeric_values():
    data = {
        "user1": {
            "attributes": {
                "uid": 42,
                "score": 3.14,
            }
        }
    }
    service = AttributesService(data)
    attrs = service.get_attributes("user1")

    assert AttributeValue("uid", 42) in attrs
    assert AttributeValue("score", 3.14) in attrs


def test_boolean_values():
    data = {
        "user1": {
            "attributes": {
                "active": True,
                "locked": False,
            }
        }
    }
    service = AttributesService(data)
    attrs = service.get_attributes("user1")

    assert AttributeValue("active", True) in attrs
    assert AttributeValue("locked", False) in attrs


def test_default_fallback_on_unknown_user_gets_default():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "john": {
                "attributes": {
                    "displayName": "John Doe",
                },
            },
        },
        default_fallback=True,
    )

    attrs = service.get_attributes("bob")
    assert attrs == [AttributeValue("affiliation", "employee")]


def test_default_fallback_off_unknown_user_gets_nothing():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
        },
        default_fallback=False,
    )

    attrs = service.get_attributes("bob")
    assert attrs == []


def test_default_fallback_on_listed_user_still_gets_own():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "alice": {
                "attributes": {
                    "role": "viewer",
                },
            },
        },
        default_fallback=True,
    )

    attrs = service.get_attributes("alice")
    assert attrs == [AttributeValue("role", "viewer")]


def test_default_fallback_off_listed_user_gets_own():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "alice": {
                "attributes": {
                    "role": "viewer",
                },
            },
        },
        default_fallback=False,
    )

    attrs = service.get_attributes("alice")
    assert attrs == [AttributeValue("role", "viewer")]


def test_no_default_key_fallback_returns_empty():
    service = AttributesService(
        {
            "alice": {"attributes": {"role": "admin"}},
        },
        default_fallback=True,
    )

    attrs = service.get_attributes("bob")
    assert attrs == []


def test_merge_default_listed_user_gets_default_baseline():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                    "groupMembership": "valid-user",
                }
            },
            "john": {
                "attributes": {
                    "displayName": "John Doe",
                },
            },
        },
        merge_default=True,
    )

    attrs = service.get_attributes("john")
    assert set(attrs) == {
        AttributeValue("affiliation", "employee"),
        AttributeValue("groupMembership", "valid-user"),
        AttributeValue("displayName", "John Doe"),
    }


def test_merge_default_user_overrides_default():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                    "groupMembership": ["valid-user"],
                }
            },
            "john": {
                "attributes": {
                    "affiliation": "faculty",
                    "displayName": "John Doe",
                },
            },
        },
        merge_default=True,
    )

    attrs = service.get_attributes("john")
    assert AttributeValue("affiliation", "faculty") in attrs
    assert AttributeValue("displayName", "John Doe") in attrs
    assert AttributeValue("groupMembership", "valid-user") in attrs
    assert len(attrs) == 3


def test_merge_default_with_explicit_inherit():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "ROLE_ADMIN": {
                "attributes": {
                    "role": "admin",
                }
            },
            "john": {
                "inherit": "ROLE_ADMIN",
                "attributes": {
                    "displayName": "John Doe",
                },
            },
        },
        merge_default=True,
    )

    attrs = service.get_attributes("john")
    assert set(attrs) == {
        AttributeValue("affiliation", "employee"),
        AttributeValue("role", "admin"),
        AttributeValue("displayName", "John Doe"),
    }


def test_merge_default_off_listed_user_no_default_baseline():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "john": {
                "attributes": {
                    "displayName": "John Doe",
                },
            },
        },
        merge_default=False,
    )

    attrs = service.get_attributes("john")
    assert attrs == [AttributeValue("displayName", "John Doe")]


def test_merge_default_with_default_fallback_on_unknown():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
            "john": {
                "attributes": {
                    "displayName": "John Doe",
                },
            },
        },
        default_fallback=True,
        merge_default=True,
    )

    attrs = service.get_attributes("bob")
    assert attrs == [AttributeValue("affiliation", "employee")]


def test_merge_default_on_user_is_default():
    service = AttributesService(
        {
            "DEFAULT": {
                "attributes": {
                    "affiliation": "employee",
                }
            },
        },
        merge_default=True,
    )

    attrs = service.get_attributes("DEFAULT")
    assert attrs == [AttributeValue("affiliation", "employee")]


def test_create_attributes_service_no_env():
    with patch("caspyan.attributes.os.environ", {}):
        svc = create_attributes_service()
        assert svc is None


def test_create_attributes_service_with_url():
    import json

    data = {"test": {"attributes": {"key": "val"}}}

    with (
        patch.dict(
            "caspyan.attributes.os.environ",
            {ATTRIBUTES_JSON_URL_ENV: "http://fake/attrs.json"},
        ),
        patch("caspyan.attributes.urlopen") as mock_open,
    ):
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
            data
        ).encode()
        mock_open.return_value.__enter__.return_value.status = 200
        svc = create_attributes_service()
        assert svc is not None
        attrs = svc.get_attributes("test")
        assert AttributeValue("key", "val") in attrs
