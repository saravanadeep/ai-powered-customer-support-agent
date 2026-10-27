from app.database import SessionLocal
from app.models import Customer, Ticket
from app.logging_config import get_logger


class TicketService:

    logger = get_logger(__name__)

    @staticmethod
    def create_ticket(
        customer_id,
        issue,
        priority="Medium"
    ):

        try:

            if priority not in {"High", "Medium", "Low"}:

                TicketService.logger.warning(
                    f"Invalid ticket priority: {priority}"
                )

                return {
                    "success": False,
                    "message": (
                        "Invalid priority. "
                        "Priority must be High, Medium or Low."
                    )
                }

            with SessionLocal.begin() as db:

                customer = (
                    db.query(Customer)
                    .filter(Customer.customer_id == customer_id)
                    .first()
                )

                if not customer:

                    TicketService.logger.warning(
                        f"Ticket creation failed. "
                        f"Customer not found: customer_id={customer_id}"
                    )

                    return {
                        "success": False,
                        "message": "Customer not found."
                    }

                ticket = Ticket(
                    customer_id=customer_id,
                    issue=issue,
                    priority=priority,
                    status="Open"
                )

                db.add(ticket)
                db.flush()

                TicketService.logger.info(
                    f"Ticket created successfully. "
                    f"ticket_id={ticket.ticket_id}, "
                    f"customer_id={customer_id}"
                )

                return {
                    "success": True,
                    "message": "Ticket created successfully.",
                    "ticket_id": ticket.ticket_id,
                    "customer_id": ticket.customer_id,
                    "issue": ticket.issue,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "created_at": ticket.created_at
                }

        except Exception:
            TicketService.logger.exception(
                f"Error creating ticket. customer_id={customer_id}"
            )
            raise

    @staticmethod
    def get_ticket(ticket_id):

        try:

            with SessionLocal() as db:

                ticket = (
                    db.query(Ticket)
                    .filter(Ticket.ticket_id == ticket_id)
                    .first()
                )

                if not ticket:

                    TicketService.logger.warning(
                        f"Ticket not found. ticket_id={ticket_id}"
                    )

                    return {
                        "success": False,
                        "message": "Ticket not found."
                    }

                TicketService.logger.info(
                    f"Ticket retrieved successfully. "
                    f"ticket_id={ticket_id}"
                )

                return {
                    "success": True,
                    "ticket": {
                        "ticket_id": ticket.ticket_id,
                        "customer_id": ticket.customer_id,
                        "issue": ticket.issue,
                        "priority": ticket.priority,
                        "status": ticket.status,
                        "created_at": ticket.created_at
                    }
                }

        except Exception:
            TicketService.logger.exception(
                f"Error retrieving ticket. ticket_id={ticket_id}"
            )
            raise

    @staticmethod
    def get_tickets():

        try:

            with SessionLocal() as db:

                tickets = (
                    db.query(Ticket)
                    .order_by(Ticket.created_at.desc())
                    .all()
                )

                TicketService.logger.info(
                    f"Tickets retrieved successfully. "
                    f"count={len(tickets)}"
                )

                return {
                    "success": True,
                    "count": len(tickets),
                    "tickets": [
                        {
                            "ticket_id": ticket.ticket_id,
                            "customer_id": ticket.customer_id,
                            "issue": ticket.issue,
                            "priority": ticket.priority,
                            "status": ticket.status,
                            "created_at": ticket.created_at
                        }
                        for ticket in tickets
                    ]
                }

        except Exception:
            TicketService.logger.exception(
                "Error retrieving tickets."
            )
            raise

    @staticmethod
    def update_ticket(
        ticket_id,
        issue=None,
        priority=None,
        status=None
    ):

        try:

            if priority is not None and priority not in {
                "High",
                "Medium",
                "Low"
            }:

                TicketService.logger.warning(
                    f"Invalid ticket priority during update: {priority}"
                )

                return {
                    "success": False,
                    "message": (
                        "Invalid priority. "
                        "Priority must be High, Medium or Low."
                    )
                }

            if status is not None and status not in {
                "Open",
                "Closed"
            }:

                TicketService.logger.warning(
                    f"Invalid ticket status during update: {status}"
                )

                return {
                    "success": False,
                    "message": (
                        "Invalid status. "
                        "Status must be Open or Closed."
                    )
                }

            with SessionLocal.begin() as db:

                ticket = (
                    db.query(Ticket)
                    .filter(Ticket.ticket_id == ticket_id)
                    .first()
                )

                if not ticket:

                    TicketService.logger.warning(
                        f"Ticket update failed. "
                        f"Ticket not found: ticket_id={ticket_id}"
                    )

                    return {
                        "success": False,
                        "message": "Ticket not found."
                    }

                if issue is not None:
                    ticket.issue = issue

                if priority is not None:
                    ticket.priority = priority

                if status is not None:
                    ticket.status = status

                db.flush()

                TicketService.logger.info(
                    f"Ticket updated successfully. "
                    f"ticket_id={ticket_id}"
                )

                return {
                    "success": True,
                    "message": "Ticket updated successfully.",
                    "ticket": {
                        "ticket_id": ticket.ticket_id,
                        "customer_id": ticket.customer_id,
                        "issue": ticket.issue,
                        "priority": ticket.priority,
                        "status": ticket.status,
                        "created_at": ticket.created_at
                    }
                }

        except Exception:
            TicketService.logger.exception(
                f"Error updating ticket. ticket_id={ticket_id}"
            )
            raise