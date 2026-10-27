from langchain.tools import tool

from app.services.customer_service import CustomerService

from app.services.ticket_service import TicketService

from app.services.customer_import_service import CustomerImportService


# =====================================================
# CUSTOMER TOOLS
# =====================================================

@tool
def create_customer(
    name: str,
    email: str,
    phone: str = "",
    company: str = "",
    plan: str = "Basic"
) -> str:
    """
    Create a new customer in the CRM.
    """

    result = CustomerService.create_customer(
        name=name,
        email=email,
        phone=phone,
        company=company,
        plan=plan
    )

    return str(result)


@tool
def get_customer(customer_id: int) -> str:
    """
    Get customer information using customer ID.
    """

    result = CustomerService.get_customer(customer_id)

    return str(result)


@tool
def search_customers(query: str) -> str:
    """
    Search customers by name, email or company.
    """

    result = CustomerService.search_customers(query)

    return str(result)


@tool
def update_customer(
    customer_id: int,
    name: str = None,
    email: str = None,
    phone: str = None,
    company: str = None,
    status: str = None,
    plan: str = None
) -> str:
    """
    Update an existing customer's information.
    """

    result = CustomerService.update_customer(
        customer_id=customer_id,
        name=name,
        email=email,
        phone=phone,
        company=company,
        status=status,
        plan=plan
    )

    return str(result)


@tool
def delete_customer(customer_id: int) -> str:
    """
    Delete a customer only if they have no open tickets.
    Closed tickets will also be deleted.
    """

    result = CustomerService.delete_customer(customer_id)

    return str(result)

# =====================================================
# TICKETS TOOLS
# =====================================================

@tool
def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "Medium"
) -> str:
    """
    Create a new support ticket for a customer.
    Priority can be High, Medium, or Low.
    """

    result = TicketService.create_ticket(
        customer_id=customer_id,
        issue=issue,
        priority=priority
    )

    return str(result)


@tool
def get_ticket(ticket_id: int) -> str:
    """
    Get ticket information using ticket ID.
    """

    result = TicketService.get_ticket(ticket_id)

    return str(result)


@tool
def get_tickets() -> str:
    """
    Get all support tickets from the CRM.
    """

    result = TicketService.get_tickets()

    return str(result)


@tool
def update_ticket(
    ticket_id: int,
    status: str = None,
    priority: str = None,
    issue: str = None
) -> str:
    """
    Update an existing support ticket.

    Status can be Open or Closed.
    Priority can be High, Medium, or Low.
    """

    result = TicketService.update_ticket(
        ticket_id=ticket_id,
        status=status,
        priority=priority,
        issue=issue
    )

    return str(result)

# =====================================================
# CUSTOMER FILE IMPORT TOOLS
# =====================================================

@tool
def import_customers(file_path: str) -> str:
    """
    Import customers from a CSV or Excel file into the CRM.

    The file must contain the required columns:
    name and email.

    Optional columns:
    phone, company, status, plan.
    """

    result = CustomerImportService.import_customers(file_path)

    return str(result)