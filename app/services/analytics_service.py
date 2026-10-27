from sqlalchemy import func

from app.database import SessionLocal
from app.models import Customer, Ticket
from app.logging_config import get_logger


class AnalyticsService:

    logger = get_logger(__name__)

    @staticmethod
    def get_ticket_overview():

        try:

            with SessionLocal() as db:

                total_tickets = (
                    db.query(Ticket)
                    .count()
                )

                open_tickets = (
                    db.query(Ticket)
                    .filter(
                        func.lower(Ticket.status) == "open"
                    )
                    .count()
                )

                closed_tickets = (
                    db.query(Ticket)
                    .filter(
                        func.lower(Ticket.status) == "closed"
                    )
                    .count()
                )

                high_priority_tickets = (
                    db.query(Ticket)
                    .filter(
                        func.lower(Ticket.priority) == "high"
                    )
                    .count()
                )

                AnalyticsService.logger.info(
                    "Ticket overview generated. "
                    f"total={total_tickets}, "
                    f"open={open_tickets}, "
                    f"closed={closed_tickets}, "
                    f"high_priority={high_priority_tickets}"
                )

                return {
                    "success": True,
                    "total_tickets": total_tickets,
                    "open_tickets": open_tickets,
                    "closed_tickets": closed_tickets,
                    "high_priority_tickets": high_priority_tickets
                }

        except Exception:

            AnalyticsService.logger.exception(
                "Error generating ticket overview."
            )

            raise

    @staticmethod
    def get_ticket_status_summary():

        try:

            with SessionLocal() as db:

                results = (
                    db.query(
                        func.lower(Ticket.status).label("status"),
                        func.count(Ticket.ticket_id).label("count")
                    )
                    .group_by(
                        func.lower(Ticket.status)
                    )
                    .order_by(
                        func.count(Ticket.ticket_id).desc()
                    )
                    .all()
                )

                AnalyticsService.logger.info(
                    f"Ticket status summary generated. "
                    f"categories={len(results)}"
                )

                return {
                    "success": True,
                    "summary": [
                        {
                            "status": row.status,
                            "count": row.count
                        }
                        for row in results
                    ]
                }

        except Exception:

            AnalyticsService.logger.exception(
                "Error generating ticket status summary."
            )

            raise

    @staticmethod
    def get_ticket_priority_summary():

        try:

            with SessionLocal() as db:

                results = (
                    db.query(
                        func.lower(Ticket.priority).label("priority"),
                        func.count(Ticket.ticket_id).label("count")
                    )
                    .group_by(
                        func.lower(Ticket.priority)
                    )
                    .order_by(
                        func.count(Ticket.ticket_id).desc()
                    )
                    .all()
                )

                AnalyticsService.logger.info(
                    f"Ticket priority summary generated. "
                    f"categories={len(results)}"
                )

                return {
                    "success": True,
                    "summary": [
                        {
                            "priority": row.priority,
                            "count": row.count
                        }
                        for row in results
                    ]
                }

        except Exception:

            AnalyticsService.logger.exception(
                "Error generating ticket priority summary."
            )

            raise

    @staticmethod
    def get_high_priority_open_tickets():

        try:

            with SessionLocal() as db:

                tickets = (
                    db.query(Ticket)
                    .filter(
                        func.lower(Ticket.priority) == "high",
                        func.lower(Ticket.status) == "open"
                    )
                    .order_by(
                        Ticket.created_at.desc()
                    )
                    .all()
                )

                AnalyticsService.logger.info(
                    f"High-priority open tickets retrieved. "
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

            AnalyticsService.logger.exception(
                "Error retrieving high-priority open tickets."
            )

            raise

    @staticmethod
    def get_customer_ticket_summary():

        try:

            with SessionLocal() as db:

                results = (
                    db.query(
                        Customer.customer_id,
                        Customer.name,
                        Customer.email,
                        func.count(Ticket.ticket_id).label(
                            "ticket_count"
                        )
                    )
                    .outerjoin(
                        Ticket,
                        Customer.customer_id == Ticket.customer_id
                    )
                    .group_by(
                        Customer.customer_id,
                        Customer.name,
                        Customer.email
                    )
                    .order_by(
                        func.count(Ticket.ticket_id).desc()
                    )
                    .all()
                )

                AnalyticsService.logger.info(
                    f"Customer ticket summary generated. "
                    f"customers={len(results)}"
                )

                return {
                    "success": True,
                    "summary": [
                        {
                            "customer_id": row.customer_id,
                            "name": row.name,
                            "email": row.email,
                            "ticket_count": row.ticket_count
                        }
                        for row in results
                    ]
                }

        except Exception:

            AnalyticsService.logger.exception(
                "Error generating customer ticket summary."
            )

            raise