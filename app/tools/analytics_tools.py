from langchain.tools import tool

from app.services.analytics_service import AnalyticsService


@tool
def get_ticket_overview():
    """
    Get total, open, closed, and high-priority ticket counts.
    """

    return AnalyticsService.get_ticket_overview()


@tool
def get_ticket_status_summary():
    """
    Get ticket count grouped by status.
    """

    return AnalyticsService.get_ticket_status_summary()


@tool
def get_ticket_priority_summary():
    """
    Get ticket count grouped by priority.
    """

    return AnalyticsService.get_ticket_priority_summary()


@tool
def get_customer_ticket_summary():
    """
    Get the number of tickets for each customer.
    """

    return AnalyticsService.get_customer_ticket_summary()


@tool
def get_high_priority_open_tickets():
    """
    Get all currently open high-priority tickets.
    """

    return AnalyticsService.get_high_priority_open_tickets()