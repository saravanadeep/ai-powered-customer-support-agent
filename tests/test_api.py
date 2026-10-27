import io

import uuid

import pandas as pd

import pytest

from fastapi.testclient import TestClient

from app.api import app

from app.database import SessionLocal
from app.auth import create_access_token, hash_password
from app.models import Customer, Ticket, User

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def authenticated_api_client():
    """Give legacy API tests a valid JWT without weakening endpoint security."""
    username = f"api_test_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"

    with SessionLocal() as db:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password("ApiTestPassword123!"),
            role="Support Agent",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.user_id

    token = create_access_token(user_id)
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield

    client.headers.pop("Authorization", None)
    with SessionLocal.begin() as db:
        db.query(User).filter(User.user_id == user_id).delete(
            synchronize_session=False
        )

def unique_email(prefix="api"):

    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

def cleanup_customer(customer_id):

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

# =====================================================

# BASIC API

# =====================================================

def test_home():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "Customer Support CRM Agent API" in data["message"]

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"

# =====================================================

# CUSTOMER API

# =====================================================

def test_create_customer_api():

    email = unique_email()

    response = client.post(

        "/customers",

        json={

            "name": "API Test User",

            "email": email,

            "phone": "9999999999",

            "company": "API Company",

            "plan": "Premium"

        }

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    customer_id = data["customer_id"]

    cleanup_customer(customer_id)

def test_create_customer_duplicate_email():

    email = unique_email("duplicate")

    first = client.post(

        "/customers",

        json={

            "name": "First User",

            "email": email

        }

    )

    assert first.status_code == 200

    customer_id = first.json()["customer_id"]

    try:

        second = client.post(

            "/customers",

            json={

                "name": "Second User",

                "email": email

            }

        )

        assert second.status_code == 400

        assert (

            "already exists"

            in second.json()["message"]

        )

    finally:

        cleanup_customer(customer_id)

def test_create_customer_invalid_request():

    response = client.post(

        "/customers",

        json={

            "email": "missing_name@example.com"

        }

    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False

def test_search_customers():

    response = client.get(

        "/customers",

        params={"query": "Rahul"}

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "customers" in data

def test_get_customer_not_found():

    response = client.get(

        "/customers/999999999"

    )

    assert response.status_code == 404

def test_update_customer_api():

    email = unique_email("update")

    create_response = client.post(

        "/customers",

        json={

            "name": "Update User",

            "email": email,

            "phone": "9999999999",

            "company": "Old Company",

            "plan": "Basic"

        }

    )

    customer_id = (

        create_response.json()["customer_id"]

    )

    try:

        response = client.put(

            f"/customers/{customer_id}",

            json={

                "name": "Updated User",

                "company": "New Company",

                "plan": "Premium"

            }

        )

        assert response.status_code == 200

        data = response.json()

        assert data["success"] is True

        assert data["customer"]["name"] == "Updated User"

    finally:

        cleanup_customer(customer_id)

def test_update_customer_not_found():

    response = client.put(

        "/customers/999999999",

        json={

            "name": "Unknown"

        }

    )

    assert response.status_code == 400

def test_delete_customer_not_found():

    response = client.delete(

        "/customers/999999999"

    )

    assert response.status_code == 403

def test_admin_delete_customer_not_found():

    from app.auth import create_access_token, hash_password
    from app.models import User

    username = f"admin_test_{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        admin = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=hash_password("TestAdmin123!"),
            role="Admin",
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        admin_id = admin.user_id

    try:
        token = create_access_token(admin_id)

        response = client.delete(
            "/customers/999999999",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        assert response.status_code == 400

    finally:
        with SessionLocal.begin() as db:
            db.query(User).filter(
                User.user_id == admin_id
            ).delete()

# =====================================================

# TICKET API

# =====================================================

def create_test_customer():

    email = unique_email("ticket")

    response = client.post(

        "/customers",

        json={

            "name": "Ticket API Customer",

            "email": email,

            "phone": "8888888888",

            "company": "Ticket API",

            "plan": "Basic"

        }

    )

    assert response.status_code == 200

    return response.json()["customer_id"]

def test_create_and_get_ticket():

    customer_id = create_test_customer()

    try:

        response = client.post(

            "/tickets",

            json={

                "customer_id": customer_id,

                "issue": "API test issue",

                "priority": "High"

            }

        )

        assert response.status_code == 200

        data = response.json()

        assert data["success"] is True

        ticket_id = data["ticket_id"]

        get_response = client.get(

            f"/tickets/{ticket_id}"

        )

        assert get_response.status_code == 200

        assert (

            get_response.json()["ticket"]["ticket_id"]

            == ticket_id

        )

    finally:

        cleanup_customer(customer_id)

def test_create_ticket_customer_not_found():

    response = client.post(

        "/tickets",

        json={

            "customer_id": 999999999,

            "issue": "Unknown customer",

            "priority": "High"

        }

    )

    assert response.status_code == 400

def test_create_ticket_invalid_priority():

    customer_id = create_test_customer()

    try:

        response = client.post(

            "/tickets",

            json={

                "customer_id": customer_id,

                "issue": "Invalid priority",

                "priority": "Critical"

            }

        )

        assert response.status_code == 400

    finally:

        cleanup_customer(customer_id)

def test_get_all_tickets():

    response = client.get("/tickets")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "tickets" in data

def test_ticket_not_found():

    response = client.get(

        "/tickets/999999999"

    )

    assert response.status_code == 404

def test_update_ticket_api():

    customer_id = create_test_customer()

    try:

        create_response = client.post(

            "/tickets",

            json={

                "customer_id": customer_id,

                "issue": "Original issue",

                "priority": "Medium"

            }

        )

        ticket_id = (

            create_response.json()["ticket_id"]

        )

        response = client.put(

            f"/tickets/{ticket_id}",

            json={

                "issue": "Updated issue",

                "priority": "High",

                "status": "Closed"

            }

        )

        assert response.status_code == 200

        data = response.json()

        assert data["success"] is True

        assert data["ticket"]["status"] == "Closed"

    finally:

        cleanup_customer(customer_id)

def test_update_ticket_not_found():

    response = client.put(

        "/tickets/999999999",

        json={

            "status": "Closed"

        }

    )

    assert response.status_code == 400

# =====================================================

# ANALYTICS API

# =====================================================

def test_analytics_ticket_overview():

    response = client.get(

        "/analytics/ticket-overview"

    )

    assert response.status_code == 200

    data = response.json()

    assert "total_tickets" in data

    assert "open_tickets" in data

    assert "closed_tickets" in data

    assert "high_priority_tickets" in data

def test_analytics_ticket_status():

    response = client.get(

        "/analytics/ticket-status"

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "summary" in data

def test_analytics_ticket_priority():

    response = client.get(

        "/analytics/ticket-priority"

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "summary" in data

def test_analytics_high_priority_open():

    response = client.get(

        "/analytics/high-priority-open"

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "tickets" in data

    assert "count" in data

def test_analytics_customer_summary():

    response = client.get(

        "/analytics/customer-ticket-summary"

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "summary" in data

# =====================================================

# CUSTOMER IMPORT API

# =====================================================

def test_customer_import_invalid_extension():

    response = client.post(

        "/customers/import",

        files={

            "file": (

                "customers.txt",

                b"invalid",

                "text/plain"

            )

        }

    )

    assert response.status_code == 400

def test_customer_import_csv():

    email = unique_email("csv_api")

    csv_content = (

        "name,email,phone,company,status,plan\n"

        f"API CSV User,{email},9999999999,"

        "API Company,Active,Basic\n"

    )

    try:

        response = client.post(

            "/customers/import",

            files={

                "file": (

                    "customers.csv",

                    csv_content.encode(),

                    "text/csv"

                )

            }

        )

        assert response.status_code == 200

        data = response.json()

        assert data["success"] is True

        assert data["inserted"] >= 1

    finally:

        with SessionLocal.begin() as db:

            db.query(Customer).filter(

                Customer.email == email

            ).delete(

                synchronize_session=False

            )

# =====================================================

# KNOWLEDGE BASE API

# =====================================================

def test_knowledge_upload_invalid_extension():

    response = client.post(

        "/knowledge/upload",

        files={

            "file": (

                "test.csv",

                b"invalid file",

                "text/csv"

            )

        }

    )

    assert response.status_code == 400

# =====================================================

# CHAT API

# =====================================================

def test_chat_validation_error():

    response = client.post(

        "/chat",

        json={}

    )

    assert response.status_code == 422

def test_chat_success(monkeypatch):

    class FakeMessage:

        def __init__(self):

            self.content = "Test AI response"

            self.tool_calls = []

    class FakeAgent:

        def invoke(self, payload):

            return {

                "messages": [

                    FakeMessage()

                ]

            }

    monkeypatch.setattr(

        "app.api.agent",

        FakeAgent()

    )

    response = client.post(

        "/chat",

        json={

            "question": "Hello"

        }

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["answer"] == "Test AI response"

    assert data["tools_used"] == []

def test_chat_with_tool(monkeypatch):

    class FakeMessage:

        def __init__(

            self,

            content="",

            tool_calls=None,

            name=None

        ):

            self.content = content

            self.tool_calls = (

                tool_calls or []

            )

            self.name = name

        @property

        def __class__(self):

            class FakeClass:

                __name__ = "ToolMessage"

            return FakeClass

    class FakeAgent:

        def invoke(self, payload):

            tool_message = FakeMessage(

                content=(

                    "SOURCE 1\n"

                    "File: refund_policy.pdf, page 3\n"

                    "Content:\nRefund information."

                ),

                name="search_knowledge_base"

            )

            assistant_message = FakeMessage(

                content="Refund policy answer.",

                tool_calls=[

                    {

                        "name":

                        "search_knowledge_base"

                    }

                ]

            )

            return {

                "messages": [

                    assistant_message,

                    tool_message

                ]

            }

    monkeypatch.setattr(

        "app.api.agent",

        FakeAgent()

    )

    response = client.post(

        "/chat",

        json={

            "question": "What is the refund policy?"

        }

    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert (

        "search_knowledge_base"

        in data["tools_used"]

    )

def test_chat_agent_error(monkeypatch):

    class FakeAgent:

        def invoke(self, payload):

            raise RuntimeError(

                "Test agent failure"

            )

    monkeypatch.setattr(

        "app.api.agent",

        FakeAgent()

    )

    response = client.post(

        "/chat",

        json={

            "question": "Test"

        }

    )

    assert response.status_code == 500

    data = response.json()

    assert data["success"] is False

    assert data["error"] == "HTTP Error"

    assert (

        data["message"]

        == "The AI agent is temporarily unavailable. Please try again."

    )
