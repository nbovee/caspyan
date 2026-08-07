import pytest
from httpx import ASGITransport, AsyncClient

from caspyan.app import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/cas/login?service=http://example.com")
    assert response.status_code == 200
    assert "CAS" in response.text
    assert "Username" in response.text


@pytest.mark.asyncio
async def test_login_post_bad_credentials(client):
    response = await client.post(
        "/cas/login?service=http://example.com",
        data={"username": "john", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_full_login_flow(client):
    # Login via POST
    response = await client.post(
        "/cas/login?service=http://example.com/home",
        data={"username": "john", "password": "john"},
        follow_redirects=False,
    )

    assert response.status_code == 302

    # Now re-GET login — should redirect with ticket
    cookies = response.cookies
    response = await client.get(
        "/cas/login?service=http://example.com/home",
        cookies=cookies,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "ticket=ST-" in location

    # Extract ticket
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    ticket_id = params["ticket"][0]

    # Validate the ticket
    response = await client.get(
        f"/cas/serviceValidate?ticket={ticket_id}&service=http://example.com/home",
    )
    assert response.status_code == 200
    assert "authenticationSuccess" in response.text
    assert "<cas:user>john</cas:user>" in response.text


@pytest.mark.asyncio
async def test_invalid_ticket_validation(client):
    response = await client.get(
        "/cas/serviceValidate?ticket=ST-fake&service=http://example.com",
    )
    assert response.status_code == 200
    assert "authenticationFailure" in response.text
    assert 'code="INVALID_TICKET"' in response.text


@pytest.mark.asyncio
async def test_service_validate_missing_params(client):
    response = await client.get("/cas/serviceValidate")
    assert response.status_code == 200
    assert "INVALID_REQUEST" in response.text


@pytest.mark.asyncio
async def test_p3_validate(client):
    response = await client.get(
        "/cas/p3/serviceValidate?ticket=ST-fake&service=http://example.com",
    )
    assert response.status_code == 200
    assert "authenticationFailure" in response.text


@pytest.mark.asyncio
async def test_login_with_existing_ticket_does_not_loop(client):
    # Login first, so the session is authenticated.
    response = await client.post(
        "/cas/login?service=http://example.com/home",
        data={"username": "john", "password": "john"},
        follow_redirects=False,
    )
    cookies = dict(response.cookies)

    # Service already carries a ticket. The server must not mint another one,
    # otherwise the authenticated redirect loops forever.
    response = await client.get(
        "/cas/login?service=http://example.com/home?ticket=ST-existing",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://example.com/home?ticket=ST-existing"


@pytest.mark.asyncio
async def test_login_redirect_joins_query_with_ampersand(client):
    response = await client.post(
        "/cas/login?service=http://example.com/home?next=%2F",
        data={"username": "john", "password": "john"},
        follow_redirects=False,
    )
    cookies = dict(response.cookies)

    response = await client.get(
        "/cas/login?service=http://example.com/home?next=%2F",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    # Existing query params must be preserved and joined with "&", not "?".
    assert "?next=/&ticket=ST-" in location


@pytest.mark.asyncio
async def test_logout_page(client):
    response = await client.get("/cas/logout")
    assert response.status_code == 200
    assert "Logout" in response.text


@pytest.mark.asyncio
async def _login(client) -> dict:
    response = await client.post(
        "/cas/login?service=http://example.com/home",
        data={"username": "john", "password": "john"},
        follow_redirects=False,
    )
    return dict(response.cookies)


@pytest.mark.asyncio
async def test_logout_get_redirects_to_service(client):
    cookies = await _login(client)
    response = await client.get(
        "/cas/logout?service=http://example.com/home",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://example.com/home"


@pytest.mark.asyncio
async def test_logout_post_redirects_to_service(client):
    cookies = await _login(client)
    response = await client.post(
        "/cas/logout?service=http://example.com/home",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://example.com/home"


@pytest.mark.asyncio
async def test_logout_redirects_to_next_param(client):
    cookies = await _login(client)
    response = await client.get(
        "/cas/logout?next=http://localhost/account/login/?next=%2F",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost/account/login/?next=/"


@pytest.mark.asyncio
async def test_logout_post_without_service_stays_on_page(client):
    cookies = await _login(client)
    response = await client.post("/cas/logout", cookies=cookies, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/cas/logout"


@pytest.mark.asyncio
async def test_logout_clears_session(client):
    cookies = await _login(client)
    logout = await client.get(
        "/cas/logout?service=http://example.com/home",
        cookies=cookies,
        follow_redirects=False,
    )
    cleared_cookies = dict(logout.cookies)
    # Session is cleared: an authenticated request would redirect with a ticket,
    # so hitting /cas/login now must render the login form (200), not redirect.
    response = await client.get(
        "/cas/login?service=http://example.com/home",
        cookies=cleared_cookies,
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Username" in response.text


@pytest.mark.asyncio
async def test_login_no_service(client):
    cookies: dict = {}
    # First login
    response = await client.post(
        "/cas/login?service=http://example.com",
        data={"username": "john", "password": "john"},
        follow_redirects=False,
    )
    cookies.update(dict(response.cookies))

    # Now hit /cas/login without service — should error since authenticated
    response = await client.get("/cas/login", cookies=cookies)
    assert response.status_code == 400
    assert "service parameter" in response.text
