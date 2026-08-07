import pytest

from caspyan.auth import AuthenticationError, NotAuthenticError, authenticate


def test_authenticate_success():
    assert authenticate("john", "john") == "john"


def test_authenticate_empty_username():
    with pytest.raises(NotAuthenticError):
        authenticate("", "password")


def test_authenticate_empty_password():
    with pytest.raises(NotAuthenticError):
        authenticate("user", "")


def test_authenticate_none_username():
    with pytest.raises(NotAuthenticError):
        authenticate(None, "password")


def test_authenticate_none_password():
    with pytest.raises(NotAuthenticError):
        authenticate("user", None)


def test_authenticate_mismatch():
    with pytest.raises(NotAuthenticError):
        authenticate("john", "doe")


def test_authenticate_fail_password():
    with pytest.raises(AuthenticationError):
        authenticate("john", "fail")
