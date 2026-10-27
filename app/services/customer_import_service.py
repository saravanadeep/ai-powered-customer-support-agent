from pathlib import Path

import pandas as pd
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Customer
from app.logging_config import get_logger


class CustomerImportService:

    logger = get_logger(__name__)

    REQUIRED_COLUMNS = {
        "name",
        "email"
    }

    OPTIONAL_COLUMNS = {
        "phone",
        "company",
        "status",
        "plan"
    }

    SUPPORTED_EXTENSIONS = {
        ".csv",
        ".xlsx"
    }

    @staticmethod
    def import_customers(file_path: str):

        path = Path(file_path)

        try:

            if path.suffix.lower() not in CustomerImportService.SUPPORTED_EXTENSIONS:

                CustomerImportService.logger.warning(
                    f"Unsupported customer import file type: "
                    f"{path.suffix}"
                )

                return {
                    "success": False,
                    "message": (
                        "Unsupported file type. "
                        "Only CSV and XLSX files are supported."
                    )
                }

            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path)

            else:
                df = pd.read_excel(path)

            CustomerImportService.logger.info(
                f"Customer import file loaded successfully. "
                f"file={path.name}, rows={len(df)}"
            )

            df.columns = [
                str(column).strip().lower()
                for column in df.columns
            ]

            missing_columns = (
                CustomerImportService.REQUIRED_COLUMNS
                - set(df.columns)
            )

            if missing_columns:

                CustomerImportService.logger.warning(
                    f"Customer import missing required columns: "
                    f"{missing_columns}"
                )

                return {
                    "success": False,
                    "message": (
                        "Missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    )
                }

            for column in CustomerImportService.OPTIONAL_COLUMNS:

                if column not in df.columns:
                    df[column] = None

            total_rows = len(df)

            df = df.dropna(
                subset=["name", "email"]
            )

            invalid_rows = total_rows - len(df)

            df["name"] = df["name"].astype(str).str.strip()
            df["email"] = df["email"].astype(str).str.strip().str.lower()

            before_duplicates = len(df)

            df = df.drop_duplicates(
                subset=["email"]
            )

            duplicates_in_file = (
                before_duplicates - len(df)
            )

            inserted = 0
            already_existing = 0

            with SessionLocal.begin() as db:

                for _, row in df.iterrows():

                    existing_customer = (
                        db.query(Customer)
                        .filter(
                            func.lower(Customer.email)
                            == row["email"].lower()
                        )
                        .first()
                    )

                    if existing_customer:

                        already_existing += 1
                        continue

                    customer = Customer(
                        name=row["name"],
                        email=row["email"],
                        phone=row["phone"],
                        company=row["company"],
                        status=(
                            row["status"]
                            if pd.notna(row["status"])
                            else "Active"
                        ),
                        plan=(
                            row["plan"]
                            if pd.notna(row["plan"])
                            else "Basic"
                        )
                    )

                    db.add(customer)
                    inserted += 1

            CustomerImportService.logger.info(
                f"Customer import completed successfully. "
                f"file={path.name}, "
                f"inserted={inserted}, "
                f"duplicates_in_file={duplicates_in_file}, "
                f"already_existing={already_existing}, "
                f"invalid={invalid_rows}"
            )

            return {
                "success": True,
                "message": "Customer import completed successfully.",
                "total_rows": total_rows,
                "inserted": inserted,
                "duplicates_in_file": duplicates_in_file,
                "already_existing": already_existing,
                "invalid": invalid_rows
            }

        except Exception:

            CustomerImportService.logger.exception(
                f"Customer import failed. file={path.name}"
            )

            raise