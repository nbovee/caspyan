class NotAuthenticError(Exception):
    """Raised when credentials are invalid."""


class AuthenticationError(Exception):
    """Raised when authentication fails for a reason other than bad credentials."""


def authenticate(username: str | None, password: str | None) -> str:
    """Authenticate a user. Returns the username on success.

    Rules (matching the original cas-mock-server):
    - username must be non-empty
    - password must be non-empty
    - password "fail" triggers an AuthenticationError
    - username must equal password

    Raises:
        NotAuthenticError: if credentials are not valid.
        AuthenticationError: if authentication fails for another reason.
    """
    if not username:
        raise NotAuthenticError("username is required")
    if not password:
        raise NotAuthenticError("password is required")
    if password == "fail":
        raise AuthenticationError("authentication failure")
    if password != username:
        raise NotAuthenticError("invalid credentials")
    return username
