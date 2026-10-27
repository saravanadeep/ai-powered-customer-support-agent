from unittest.mock import patch

from app.services.analytics_service import AnalyticsService
from app.services.customer_service import CustomerService
from app.services.ticket_service import TicketService


# =====================================================
# ANALYTICS TOOLS
# =====================================================

def test_analytics_overview_tool():

    from app.tools.analytics_tools import (
        get_ticket_overview
    )

    with patch.object(
        AnalyticsService,
        "get_ticket_overview",
        return_value={
            "success": True,
            "total_tickets": 10
        }
    ):

        result = get_ticket_overview.invoke({})

        assert result["success"] is True
        assert result["total_tickets"] == 10


def test_analytics_status_tool():

    from app.tools.analytics_tools import (
        get_ticket_status_summary
    )

    with patch.object(
        AnalyticsService,
        "get_ticket_status_summary",
        return_value={
            "success": True,
            "summary": []
        }
    ):

        result = (
            get_ticket_status_summary
            .invoke({})
        )

        assert result["success"] is True


def test_analytics_priority_tool():

    from app.tools.analytics_tools import (
        get_ticket_priority_summary
    )

    with patch.object(
        AnalyticsService,
        "get_ticket_priority_summary",
        return_value={
            "success": True,
            "summary": []
        }
    ):

        result = (
            get_ticket_priority_summary
            .invoke({})
        )

        assert result["success"] is True


def test_analytics_customer_summary_tool():

    from app.tools.analytics_tools import (
        get_customer_ticket_summary
    )

    with patch.object(
        AnalyticsService,
        "get_customer_ticket_summary",
        return_value={
            "success": True,
            "summary": []
        }
    ):

        result = (
            get_customer_ticket_summary
            .invoke({})
        )

        assert result["success"] is True


def test_analytics_high_priority_tool():

    from app.tools.analytics_tools import (
        get_high_priority_open_tickets
    )

    with patch.object(
        AnalyticsService,
        "get_high_priority_open_tickets",
        return_value={
            "success": True,
            "tickets": [],
            "count": 0
        }
    ):

        result = (
            get_high_priority_open_tickets
            .invoke({})
        )

        assert result["success"] is True


# =====================================================
# CRM TOOL IMPORT
# =====================================================

def test_crm_tools_exist():

    from app.tools import crm_tools

    assert hasattr(
        crm_tools,
        "create_customer"
    )

    assert hasattr(
        crm_tools,
        "get_customer"
    )

    assert hasattr(
        crm_tools,
        "search_customers"
    )


# =====================================================
# RAG TOOL IMPORT
# =====================================================

def test_rag_tool_exists():

    from app.tools import rag_tools

    assert hasattr(
        rag_tools,
        "search_knowledge_base"
    )


# =====================================================
# WEB TOOL IMPORT
# =====================================================

def test_web_tool_exists():

    from app.tools import web_tools

    assert hasattr(
        web_tools,
        "web_search"
    )

def test_rag_tool_exists():

    from app.tools import rag_tools

    assert hasattr(
        rag_tools,
        "search_knowledge_base"
    )

# =====================================================
# RAG TOOL IMPORT
# =====================================================

def test_rag_tool_exists():

    from app.tools import rag_tools

    assert hasattr(
        rag_tools,
        "search_knowledge_base"
    )


# =====================================================
# RAG TOOL FUNCTION TESTS
# =====================================================

def test_rag_tool_no_documents():

    from app.tools import rag_tools

    with patch.object(
        rag_tools.rag_service,
        "search",
        return_value=[]
    ):

        result = rag_tools.search_knowledge_base.func(
            query="refund policy"
        )

        assert result == (
            "No relevant information found "
            "in the knowledge base."
        )


def test_rag_tool_with_documents():

    from app.tools import rag_tools

    class FakeDocument:

        def __init__(
            self,
            source,
            page,
            content
        ):
            self.metadata = {
                "source": source
            }

            if page is not None:
                self.metadata["page"] = page

            self.page_content = content

    documents = [
        FakeDocument(
            "/documents/refund_policy.pdf",
            0,
            "Refunds are available within 30 days."
        ),
        FakeDocument(
            "/documents/faq.txt",
            None,
            "Customers can contact support by email."
        )
    ]

    with patch.object(
        rag_tools.rag_service,
        "search",
        return_value=documents
    ):

        result = rag_tools.search_knowledge_base.func(
            query="refund policy"
        )

        assert "SOURCE 1" in result
        assert "refund_policy.pdf, page 1" in result
        assert "Refunds are available within 30 days." in result

        assert "SOURCE 2" in result
        assert "faq.txt" in result
        assert "Customers can contact support by email." in result