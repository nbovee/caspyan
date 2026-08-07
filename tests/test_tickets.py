from caspyan.tickets import TicketService


def test_issue_and_validate():
    service = TicketService()
    ticket = service.issue("testuser")
    ticket_id = str(ticket)

    assert ticket_id.startswith("ST-")
    assert ticket.username == "testuser"

    state = service.validate(ticket_id)
    assert state is not None
    assert state.username == "testuser"


def test_validate_unknown_ticket():
    service = TicketService()
    assert service.validate("ST-nonexistent") is None


def test_ticket_single_use():
    service = TicketService()
    ticket = service.issue("user1")
    ticket_id = str(ticket)

    first = service.validate(ticket_id)
    assert first is not None

    second = service.validate(ticket_id)
    assert second is None


def test_unique_tickets():
    service = TicketService()
    ids = set()

    for i in range(50):
        ticket = service.issue(f"user{i}")
        ids.add(str(ticket))

    assert len(ids) == 50


def test_ticket_value_equality():
    from caspyan.tickets import TicketValue

    a = TicketValue("ST-abc", "user")
    b = TicketValue("ST-abc", "user2")
    c = TicketValue("ST-xyz", "user")

    assert a == b
    assert a != c
    assert hash(a) == hash(b)
