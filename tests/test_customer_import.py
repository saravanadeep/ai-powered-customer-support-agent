import uuid

import pandas as pd
import pytest

from app.database import SessionLocal
from app.models import Customer
from app.services.customer_import_service import CustomerImportService


def unique_email(prefix="import"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def cleanup_email(email):

    with SessionLocal.begin() as db:

        db.query(Customer).filter(
            Customer.email == email
        ).delete(
            synchronize_session=False
        )


def test_import_csv(tmp_path):

    email1 = unique_email("csv1")
    email2 = unique_email("csv2")

    csv_file = tmp_path / "customers.csv"

    df = pd.DataFrame([
        {
            "name": "CSV User One",
            "email": email1,
            "phone": "9999999991",
            "company": "CSV Company",
            "status": "Active",
            "plan": "Basic"
        },
        {
            "name": "CSV User Two",
            "email": email2,
            "phone": "9999999992",
            "company": "CSV Company",
            "status": "Active",
            "plan": "Premium"
        }
    ])

    df.to_csv(
        csv_file,
        index=False
    )

    try:

        result = CustomerImportService.import_customers(
            str(csv_file)
        )

        assert result["success"] is True
        assert result["inserted"] == 2

    finally:

        cleanup_email(email1)
        cleanup_email(email2)


def test_import_xlsx(tmp_path):

    email = unique_email("xlsx")

    xlsx_file = tmp_path / "customers.xlsx"

    df = pd.DataFrame([
        {
            "name": "Excel User",
            "email": email,
            "phone": "8888888888",
            "company": "Excel Company",
            "status": "Active",
            "plan": "Basic"
        }
    ])

    df.to_excel(
        xlsx_file,
        index=False
    )

    try:

        result = CustomerImportService.import_customers(
            str(xlsx_file)
        )

        assert result["success"] is True
        assert result["inserted"] == 1

    finally:

        cleanup_email(email)


def test_import_missing_required_columns(tmp_path):

    csv_file = tmp_path / "invalid.csv"

    df = pd.DataFrame([
        {
            "name": "Missing Email"
        }
    ])

    df.to_csv(
        csv_file,
        index=False
    )

    result = CustomerImportService.import_customers(
        str(csv_file)
    )

    assert result["success"] is False
    assert "Missing required columns" in result["message"]


def test_import_unsupported_file_type(tmp_path):

    file = tmp_path / "customers.pdf"

    file.write_text(
        "not a valid import file"
    )

    result = CustomerImportService.import_customers(
        str(file)
    )

    assert result["success"] is False
    assert "Unsupported file type" in result["message"]


def test_duplicate_emails_inside_file(tmp_path):

    email = unique_email("duplicate")

    csv_file = tmp_path / "duplicates.csv"

    df = pd.DataFrame([
        {
            "name": "User One",
            "email": email
        },
        {
            "name": "User Two",
            "email": email
        }
    ])

    df.to_csv(
        csv_file,
        index=False
    )

    try:

        result = CustomerImportService.import_customers(
            str(csv_file)
        )

        assert result["success"] is True
        assert result["inserted"] == 1
        assert result["duplicates_in_file"] == 1

    finally:

        cleanup_email(email)


def test_existing_customer_email(tmp_path):

    email = unique_email("existing")

    with SessionLocal.begin() as db:

        customer = Customer(
            name="Existing Customer",
            email=email,
            phone="7777777777",
            company="Existing Company",
            status="Active",
            plan="Basic"
        )

        db.add(customer)

    csv_file = tmp_path / "existing.csv"

    df = pd.DataFrame([
        {
            "name": "Existing Customer",
            "email": email
        }
    ])

    df.to_csv(
        csv_file,
        index=False
    )

    try:

        result = CustomerImportService.import_customers(
            str(csv_file)
        )

        assert result["success"] is True
        assert result["inserted"] == 0
        assert result["already_existing"] == 1

    finally:

        cleanup_email(email)


def test_invalid_rows(tmp_path):

    email = unique_email("valid")

    csv_file = tmp_path / "invalid_rows.csv"

    df = pd.DataFrame([
        {
            "name": "Valid User",
            "email": email
        },
        {
            "name": None,
            "email": "invalid@example.com"
        },
        {
            "name": "No Email",
            "email": None
        }
    ])

    df.to_csv(
        csv_file,
        index=False
    )

    try:

        result = CustomerImportService.import_customers(
            str(csv_file)
        )

        assert result["success"] is True
        assert result["inserted"] == 1
        assert result["invalid"] == 2

    finally:

        cleanup_email(email)