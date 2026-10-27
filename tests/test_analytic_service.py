import uuid

import pytest

from app.database import SessionLocal
from app.models import Customer, Ticket
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_test_data():

    email = f"analytics_{uuid.uuid4().hex[:8]}@example.com"

    with SessionLocal.begin() as db:

        customer = Customer(
            name="Analytics Test Customer",
            email=email,
            phone="9999999999",
            company="Analytics Company",
            status="Active",
            plan="Premium"
        )

        db.add(customer)
        db.flush()

        ticket1 = Ticket(
            customer_id=customer.customer_id,
            issue="High priority issue",
            priority="High",
            status="Open"
        )

        ticket2 = Ticket(
            customer_id=customer.customer_id,
            issue="Medium priority issue",
            priority="Medium",
            status="Closed"
        )

        ticket3 = Ticket(
            customer_id=customer.customer_id,
            issue="Low priority issue",
            priority="Low",
            status="Open"
        )

        db.add_all([
            ticket1,
            ticket2,
            ticket3
        ])

        customer_id = customer.customer_id

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


def test_ticket_overview(analytics_test_data):

    result = AnalyticsService.get_ticket_overview()

    assert result["success"] is True

    assert "total_tickets" in result
    assert "open_tickets" in result
    assert "closed_tickets" in result
    assert "high_priority_tickets" in result

    assert result["total_tickets"] >= 3
    assert result["open_tickets"] >= 2
    assert result["closed_tickets"] >= 1
    assert result["high_priority_tickets"] >= 1


def test_ticket_status_summary(analytics_test_data):

    result = AnalyticsService.get_ticket_status_summary()

    assert result["success"] is True

    statuses = {
        row["status"]
        for row in result["summary"]
    }

    assert "open" in statuses
    assert "closed" in statuses


def test_ticket_priority_summary(analytics_test_data):

    result = AnalyticsService.get_ticket_priority_summary()

    assert result["success"] is True

    priorities = {
        row["priority"]
        for row in result["summary"]
    }

    assert "high" in priorities
    assert "medium" in priorities
    assert "low" in priorities


def test_high_priority_open_tickets(
    analytics_test_data
):

    result = (
        AnalyticsService
        .get_high_priority_open_tickets()
    )

    assert result["success"] is True
    assert result["count"] >= 1

    for ticket in result["tickets"]:

        assert ticket["priority"].lower() == "high"
        assert ticket["status"].lower() == "open"


def test_customer_ticket_summary(
    analytics_test_data
):

    result = (
        AnalyticsService
        .get_customer_ticket_summary()
    )

    assert result["success"] is True

    customer_ids = {
        row["customer_id"]
        for row in result["summary"]
    }

    assert analytics_test_data in customer_ids