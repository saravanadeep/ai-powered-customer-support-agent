import pytest

from app.database import SessionLocal
from app.models import Customer, Ticket
from app.services.customer_service import CustomerService


@pytest.fixture
def test_customer():
    """
    Create a temporary customer for testing.
    """

    result = CustomerService.create_customer(
        name="Test User",
        email="test_customer@example.com",
        phone="9999999999",
        company="Test Company",
        plan="Basic"
    )

    assert result["success"] is True

    customer_id = result["customer_id"]

    yield customer_id

    # Cleanup after test
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


def test_create_customer():

    email = "create_test@example.com"

    result = CustomerService.create_customer(
        name="Create Test",
        email=email,
        phone="9999999991",
        company="Test Company",
        plan="Basic"
    )

    assert result["success"] is True
    assert result["name"] == "Create Test"
    assert result["email"] == email

    customer_id = result["customer_id"]

    # Cleanup
    with SessionLocal.begin() as db:

        db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).delete(
            synchronize_session=False
        )


def test_duplicate_customer_email(test_customer):

    result = CustomerService.create_customer(
        name="Duplicate Test",
        email="test_customer@example.com",
        phone="8888888888",
        company="Another Company",
        plan="Premium"
    )

    assert result["success"] is False
    assert "already exists" in result["message"]


def test_get_customer(test_customer):

    result = CustomerService.get_customer(
        test_customer
    )

    assert result["success"] is True

    customer = result["customer"]

    assert customer["customer_id"] == test_customer
    assert customer["name"] == "Test User"
    assert customer["email"] == "test_customer@example.com"


def test_get_customer_not_found():

    result = CustomerService.get_customer(
        999999999
    )

    assert result["success"] is False
    assert result["message"] == "Customer not found."


def test_search_customer(test_customer):

    result = CustomerService.search_customers(
        "Test User"
    )

    assert result["success"] is True
    assert result["count"] >= 1

    customer_ids = [
        customer["customer_id"]
        for customer in result["customers"]
    ]

    assert test_customer in customer_ids


def test_update_customer(test_customer):

    result = CustomerService.update_customer(
        customer_id=test_customer,
        name="Updated Test User",
        phone="8888888888",
        company="Updated Company",
        plan="Premium"
    )

    assert result["success"] is True

    customer = result["customer"]

    assert customer["name"] == "Updated Test User"
    assert customer["phone"] == "8888888888"
    assert customer["company"] == "Updated Company"
    assert customer["plan"] == "Premium"


def test_update_customer_not_found():

    result = CustomerService.update_customer(
        customer_id=999999999,
        name="Unknown User"
    )

    assert result["success"] is False
    assert result["message"] == "Customer not found."


def test_update_customer_duplicate_email(test_customer):

    second_result = CustomerService.create_customer(
        name="Second Test",
        email="second_test@example.com",
        phone="7777777777",
        company="Second Company",
        plan="Basic"
    )

    assert second_result["success"] is True

    second_customer_id = second_result["customer_id"]

    try:

        result = CustomerService.update_customer(
            customer_id=test_customer,
            email="second_test@example.com"
        )

        assert result["success"] is False
        assert "already exists" in result["message"]

    finally:

        with SessionLocal.begin() as db:

            db.query(Customer).filter(
                Customer.customer_id == second_customer_id
            ).delete(
                synchronize_session=False
            )


def test_delete_customer_with_open_ticket(test_customer):

    with SessionLocal.begin() as db:

        ticket = Ticket(
            customer_id=test_customer,
            issue="Test open ticket",
            priority="High",
            status="Open"
        )

        db.add(ticket)

    result = CustomerService.delete_customer(
        test_customer
    )

    assert result["success"] is False
    assert "open tickets" in result["message"]


def test_delete_customer(test_customer):

    result = CustomerService.delete_customer(
        test_customer
    )

    assert result["success"] is True
    assert result["message"] == "Customer deleted successfully."

    # Prevent fixture cleanup from causing problems.
    with SessionLocal() as db:

        customer = db.query(Customer).filter(
            Customer.customer_id == test_customer
        ).first()

        assert customer is None