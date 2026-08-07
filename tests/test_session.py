from caspyan.session import (
    clear_authentication,
    get_authenticated_username,
    is_authenticated,
    set_authenticated_username,
)


def test_authenticated_session():
    session: dict = {}
    assert not is_authenticated(session)
    assert get_authenticated_username(session) is None

    set_authenticated_username(session, "testuser")
    assert is_authenticated(session)
    assert get_authenticated_username(session) == "testuser"

    clear_authentication(session)
    assert not is_authenticated(session)
