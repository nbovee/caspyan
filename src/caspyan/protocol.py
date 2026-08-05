from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import Response

from . import session

if TYPE_CHECKING:
    from .attributes import AttributesService
    from .tickets import TicketService

CAS_NAMESPACE = "http://www.yale.edu/tp/cas"

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'

SUCCESS_TEMPLATE = (
    XML_DECLARATION
    + '<cas:serviceResponse xmlns:cas="{ns}">\n'
    + "  <cas:authenticationSuccess>\n"
    + "    <cas:user>{user}</cas:user>\n"
    + "{attributes}"
    + "  </cas:authenticationSuccess>\n"
    + "</cas:serviceResponse>"
)

FAILURE_TEMPLATE = (
    XML_DECLARATION
    + '<cas:serviceResponse xmlns:cas="{ns}">\n'
    + '  <cas:authenticationFailure code="{code}">'
    + "{message}</cas:authenticationFailure>\n"
    + "</cas:serviceResponse>"
)

ATTRIBUTE_TEMPLATE = "    <cas:{name}>{value}</cas:{name}>\n"


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_attributes_xml(
    attributes_service: AttributesService | None, username: str
) -> str:
    if attributes_service is None:
        return ""
    attrs = attributes_service.get_attributes(username)
    if not attrs:
        return ""
    parts = ["    <cas:attributes>\n"]
    for attr in attrs:
        name = _escape_xml(attr.name)
        value = _escape_xml(str(attr.value))
        parts.append(ATTRIBUTE_TEMPLATE.format(name=name, value=value))
    parts.append("    </cas:attributes>\n")
    return "".join(parts)


def _build_success_response(
    username: str, attributes_service: AttributesService | None = None
) -> str:
    return SUCCESS_TEMPLATE.format(
        ns=CAS_NAMESPACE,
        user=_escape_xml(username),
        attributes=_build_attributes_xml(attributes_service, username),
    )


def _build_failure_response(code: str, message: str) -> str:
    return FAILURE_TEMPLATE.format(
        ns=CAS_NAMESPACE,
        code=_escape_xml(code),
        message=_escape_xml(message),
    )


async def service_validate(request: Request) -> Response:
    return await _handle_validate(request)


async def proxy_validate(request: Request) -> Response:
    return await _handle_validate(request)


async def _handle_validate(request: Request) -> Response:
    ticket_service: TicketService = request.app.state.ticket_service
    attributes_service: AttributesService | None = getattr(
        request.app.state, "attributes_service", None
    )

    ticket_id = request.query_params.get("ticket")
    service = request.query_params.get("service")

    if not ticket_id:
        body = _build_failure_response(
            "INVALID_REQUEST", "ticket parameter is required"
        )
        return Response(body, media_type="application/xml", status_code=200)

    if not service:
        body = _build_failure_response(
            "INVALID_REQUEST", "service parameter is required"
        )
        return Response(body, media_type="application/xml", status_code=200)

    state = ticket_service.validate(ticket_id)

    if state is None:
        body = _build_failure_response(
            "INVALID_TICKET", f"ticket {_escape_xml(ticket_id)} not recognized"
        )
        return Response(body, media_type="application/xml", status_code=200)

    body = _build_success_response(state.username, attributes_service)
    return Response(body, media_type="application/xml", status_code=200)


async def login_get(request: Request) -> Response:
    """GET /cas/login — show login form or redirect if already authenticated."""
    from starlette.responses import RedirectResponse
    from starlette.templating import Jinja2Templates

    templates: Jinja2Templates = request.app.state.templates
    ticket_service: TicketService = request.app.state.ticket_service

    if session.is_authenticated(request.session):
        service = request.query_params.get("service")
        if not service:
            return Response("service parameter is required", status_code=400)
        username = session.get_authenticated_username(request.session)
        ticket = ticket_service.issue(username)
        return RedirectResponse(f"{service}?ticket={ticket}", status_code=302)

    login_url = str(request.url)
    return templates.TemplateResponse(request, "login.html", {"login_url": login_url})


async def login_post(request: Request) -> Response:
    """POST /cas/login — process login form submission."""
    from starlette.responses import RedirectResponse

    from .auth import AuthenticationError, NotAuthenticError, authenticate

    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if isinstance(username, str):
        username = username.strip() or None
    else:
        username = None

    if isinstance(password, str):
        password = password or None
    else:
        password = None

    try:
        authenticated_user = authenticate(username, password)
    except NotAuthenticError:
        return Response("Unauthorized\n", status_code=401, media_type="text/plain")
    except AuthenticationError:
        return Response("Unauthorized\n", status_code=401, media_type="text/plain")

    session.set_authenticated_username(request.session, authenticated_user)

    query = str(request.url.query)
    redirect_url = str(request.url.path) if not query else f"{request.url.path}?{query}"
    return RedirectResponse(redirect_url, status_code=302)


async def logout_get(request: Request) -> Response:
    """GET /cas/logout — show logout page."""
    from starlette.templating import Jinja2Templates

    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "logout.html", {})


async def logout_post(request: Request) -> Response:
    """POST /cas/logout — perform logout."""
    from starlette.responses import RedirectResponse

    session.clear_authentication(request.session)
    return RedirectResponse("/cas/logout", status_code=302)


async def p3_service_validate(request: Request) -> Response:
    return await _handle_validate(request)


async def p3_proxy_validate(request: Request) -> Response:
    return await _handle_validate(request)
