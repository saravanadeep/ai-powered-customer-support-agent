from sqlalchemy import func

from app.database import SessionLocal
from app.models import Customer, Ticket
from app.logging_config import get_logger


class CustomerService:

    logger = get_logger(__name__)

    @staticmethod
    def create_customer(
        name,
        email,
        phone=None,
        company=None,
        plan="Basic"
    ):
        try:
            with SessionLocal.begin() as db:

                existing_customer = (
                    db.query(Customer)
                    .filter(func.lower(Customer.email) == email.lower())
                    .first()
                )

                if existing_customer:
                    CustomerService.logger.warning(
                        f"Customer creation failed. "
                        f"Email already exists: {email}"
                    )

                    return {
                        "success": False,
                        "message": "Customer with this email already exists."
                    }

                customer = Customer(
                    name=name,
                    email=email.lower(),
                    phone=phone,
                    company=company,
                    plan=plan,
                    status="Active"
                )

                db.add(customer)
                db.flush()

                CustomerService.logger.info(
                    f"Customer created successfully. "
                    f"customer_id={customer.customer_id}"
                )

                return {
                    "success": True,
                    "message": "Customer created successfully.",
                    "customer_id": customer.customer_id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "company": customer.company,
                    "status": customer.status,
                    "plan": customer.plan
                }

        except Exception:
            CustomerService.logger.exception(
                "Error while creating customer."
            )
            raise

    @staticmethod
    def get_customer(customer_id):

        try:
            with SessionLocal() as db:

                customer = (
                    db.query(Customer)
                    .filter(Customer.customer_id == customer_id)
                    .first()
                )

                if not customer:
                    CustomerService.logger.warning(
                        f"Customer not found. customer_id={customer_id}"
                    )

                    return {
                        "success": False,
                        "message": "Customer not found."
                    }

                CustomerService.logger.info(
                    f"Customer retrieved successfully. "
                    f"customer_id={customer_id}"
                )

                return {
                    "success": True,
                    "customer": {
                        "customer_id": customer.customer_id,
                        "name": customer.name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "company": customer.company,
                        "status": customer.status,
                        "plan": customer.plan,
                        "created_at": customer.created_at
                    }
                }

        except Exception:
            CustomerService.logger.exception(
                f"Error retrieving customer. customer_id={customer_id}"
            )
            raise

    @staticmethod
    def search_customers(query):

        try:
            with SessionLocal() as db:

                customers = (
                    db.query(Customer)
                    .filter(
                        (Customer.name.ilike(f"%{query}%")) |
                        (Customer.email.ilike(f"%{query}%")) |
                        (Customer.company.ilike(f"%{query}%"))
                    )
                    .all()
                )

                CustomerService.logger.info(
                    f"Customer search completed. "
                    f"query='{query}', results={len(customers)}"
                )

                return {
                    "success": True,
                    "count": len(customers),
                    "customers": [
                        {
                            "customer_id": customer.customer_id,
                            "name": customer.name,
                            "email": customer.email,
                            "phone": customer.phone,
                            "company": customer.company,
                            "status": customer.status,
                            "plan": customer.plan,
                            "created_at": customer.created_at
                        }
                        for customer in customers
                    ]
                }

        except Exception:
            CustomerService.logger.exception(
                f"Error searching customers. query='{query}'"
            )
            raise

    @staticmethod
    def update_customer(
        customer_id,
        name=None,
        email=None,
        phone=None,
        company=None,
        status=None,
        plan=None
    ):

        try:
            with SessionLocal.begin() as db:

                customer = (
                    db.query(Customer)
                    .filter(Customer.customer_id == customer_id)
                    .first()
                )

                if not customer:
                    CustomerService.logger.warning(
                        f"Customer update failed. "
                        f"Customer not found: customer_id={customer_id}"
                    )

                    return {
                        "success": False,
                        "message": "Customer not found."
                    }

                if email:

                    existing_customer = (
                        db.query(Customer)
                        .filter(
                            func.lower(Customer.email) == email.lower(),
                            Customer.customer_id != customer_id
                        )
                        .first()
                    )

                    if existing_customer:

                        CustomerService.logger.warning(
                            f"Customer update failed. "
                            f"Email already exists: {email}"
                        )

                        return {
                            "success": False,
                            "message": "Another customer with this email already exists."
                        }

                    customer.email = email.lower()

                if name is not None:
                    customer.name = name

                if phone is not None:
                    customer.phone = phone

                if company is not None:
                    customer.company = company

                if status is not None:
                    customer.status = status

                if plan is not None:
                    customer.plan = plan

                db.flush()

                CustomerService.logger.info(
                    f"Customer updated successfully. "
                    f"customer_id={customer_id}"
                )

                return {
                    "success": True,
                    "message": "Customer updated successfully.",
                    "customer": {
                        "customer_id": customer.customer_id,
                        "name": customer.name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "company": customer.company,
                        "status": customer.status,
                        "plan": customer.plan
                    }
                }

        except Exception:
            CustomerService.logger.exception(
                f"Error updating customer. customer_id={customer_id}"
            )
            raise

    @staticmethod
    def delete_customer(customer_id):

        try:
            with SessionLocal.begin() as db:

                customer = (
                    db.query(Customer)
                    .filter(Customer.customer_id == customer_id)
                    .first()
                )

                if not customer:

                    CustomerService.logger.warning(
                        f"Customer deletion failed. "
                        f"Customer not found: customer_id={customer_id}"
                    )

                    return {
                        "success": False,
                        "message": "Customer not found."
                    }

                open_tickets = (
                    db.query(Ticket)
                    .filter(
                        Ticket.customer_id == customer_id,
                        func.lower(Ticket.status) == "open"
                    )
                    .count()
                )

                if open_tickets > 0:

                    CustomerService.logger.warning(
                        f"Customer deletion blocked. "
                        f"customer_id={customer_id}, "
                        f"open_tickets={open_tickets}"
                    )

                    return {
                        "success": False,
                        "message": (
                            "Customer cannot be deleted because "
                            "they have open tickets."
                        )
                    }

                db.query(Ticket).filter(
                    Ticket.customer_id == customer_id
                ).delete(
                    synchronize_session=False
                )

                db.delete(customer)

                CustomerService.logger.info(
                    f"Customer deleted successfully. "
                    f"customer_id={customer_id}"
                )

                return {
                    "success": True,
                    "message": "Customer deleted successfully."
                }

        except Exception:
            CustomerService.logger.exception(
                f"Error deleting customer. customer_id={customer_id}"
            )
            raise