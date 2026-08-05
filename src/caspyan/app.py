from __future__ import annotations

import logging
import secrets
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from .attributes import create_attributes_service
from .protocol import (
    login_get,
    login_post,
    logout_get,
    logout_post,
    p3_proxy_validate,
    p3_service_validate,
    proxy_validate,
    service_validate,
)
from .tickets import TicketService

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app() -> Starlette:
    ticket_service = TicketService()
    attributes_service = create_attributes_service()
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    routes = [
        Route("/cas/login", login_get, methods=["GET"]),
        Route("/cas/login", login_post, methods=["POST"]),
        Route("/cas/logout", logout_get, methods=["GET"]),
        Route("/cas/logout", logout_post, methods=["POST"]),
        Route("/cas/serviceValidate", service_validate, methods=["GET"]),
        Route("/cas/proxyValidate", proxy_validate, methods=["GET"]),
        Route("/cas/p3/serviceValidate", p3_service_validate, methods=["GET"]),
        Route("/cas/p3/proxyValidate", p3_proxy_validate, methods=["GET"]),
    ]

    app = Starlette(
        debug=False,
        routes=routes,
        middleware=[
            Middleware(
                SessionMiddleware,
                secret_key=secrets.token_urlsafe(32),
                session_cookie="JSESSIONID",
                max_age=1800,
            ),
        ],
    )

    app.state.ticket_service = ticket_service
    app.state.attributes_service = attributes_service
    app.state.templates = templates

    return app


app = create_app()
