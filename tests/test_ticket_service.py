import uuid

import pytest

from app.database import SessionLocal
from app.models import Customer, Ticket
from app.services.customer_service import CustomerService
from app.services.ticket_service import TicketService


def unique_email():
    return f"ticket_test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def test_customer():

    result = CustomerService.create_customer(
        name="Ticket Test Customer",
        email=unique_email(),
        phone="9999999999",
        company="Ticket Company",
        plan="Basic"
    )

    assert result["success"] is True

    customer_id = result["customer_id"]

    yield customer_id

    with SessionLocal.begin() as db:

        db.query(Ticket).filter(
            Ticket.customer_id == customer_id
        ).delete(
            synchronize_session=False
        )

        db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).delete(
            synchronize_session=False
        )


def test_create_ticket(test_customer):

    result = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Unable to login",
        priority="High"
    )

    assert result["success"] is True
    assert result["customer_id"] == test_customer
    assert result["priority"] == "High"
    assert result["status"] == "Open"


def test_create_ticket_default_priority(test_customer):

    result = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Password reset required"
    )

    assert result["success"] is True
    assert result["priority"] == "Medium"


def test_create_ticket_invalid_priority(test_customer):

    result = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Test issue",
        priority="Critical"
    )

    assert result["success"] is False
    assert "Invalid priority" in result["message"]


def test_create_ticket_customer_not_found():

    result = TicketService.create_ticket(
        customer_id=999999999,
        issue="Test issue",
        priority="High"
    )

    assert result["success"] is False
    assert result["message"] == "Customer not found."


def test_get_ticket(test_customer):

    created = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Test ticket",
        priority="Medium"
    )

    ticket_id = created["ticket_id"]

    result = TicketService.get_ticket(
        ticket_id
    )

    assert result["success"] is True
    assert result["ticket"]["ticket_id"] == ticket_id
    assert result["ticket"]["customer_id"] == test_customer


def test_get_ticket_not_found():

    result = TicketService.get_ticket(
        999999999
    )

    assert result["success"] is False
    assert result["message"] == "Ticket not found."


def test_get_tickets(test_customer):

    TicketService.create_ticket(
        customer_id=test_customer,
        issue="Ticket one",
        priority="Low"
    )

    TicketService.create_ticket(
        customer_id=test_customer,
        issue="Ticket two",
        priority="High"
    )

    result = TicketService.get_tickets()

    assert result["success"] is True
    assert result["count"] >= 2


def test_update_ticket(test_customer):

    created = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Original issue",
        priority="Medium"
    )

    ticket_id = created["ticket_id"]

    result = TicketService.update_ticket(
        ticket_id=ticket_id,
        issue="Updated issue",
        priority="High",
        status="Closed"
    )

    assert result["success"] is True

    ticket = result["ticket"]

    assert ticket["issue"] == "Updated issue"
    assert ticket["priority"] == "High"
    assert ticket["status"] == "Closed"


def test_update_ticket_invalid_priority(test_customer):

    created = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Test issue",
        priority="Medium"
    )

    result = TicketService.update_ticket(
        ticket_id=created["ticket_id"],
        priority="Critical"
    )

    assert result["success"] is False
    assert "Invalid priority" in result["message"]


def test_update_ticket_invalid_status(test_customer):

    created = TicketService.create_ticket(
        customer_id=test_customer,
        issue="Test issue",
        priority="Medium"
    )

    result = TicketService.update_ticket(
        ticket_id=created["ticket_id"],
        status="Pending"
    )

    assert result["success"] is False
    assert "Invalid status" in result["message"]


def test_update_ticket_not_found():

    result = TicketService.update_ticket(
        ticket_id=999999999,
        status="Closed"
    )

    assert result["success"] is False
    assert result["message"] == "Ticket not found."