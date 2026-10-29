from pathlib import Path
import shutil
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Request
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pydantic import BaseModel


from app.agent import agent
from app.logging_config import get_logger

from app.services.customer_service import CustomerService
from app.services.ticket_service import TicketService
from app.services.customer_import_service import CustomerImportService
from app.services.rag_service import RAGService
from app.services.analytics_service import AnalyticsService

from app.auth_api import router as auth_router
from fastapi import Depends
from app.dependencies import require_role
from app.models import User
from app.user_api import router as user_management_router



# =====================================================
# FASTAPI APP
# =====================================================

logger = get_logger(__name__)

app = FastAPI(
    title="Customer Support CRM Agent API",
    description="Agentic AI Customer Support and CRM API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(user_management_router)

# =====================================================
# GLOBAL ERROR HANDLERS
# =====================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Invalid request data.",
            "details": exc.errors()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Error",
            "message": str(exc.detail)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
):
    print(f"Unhandled API error: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# =====================================================
# REQUEST MODELS
# =====================================================

class ChatRequest(BaseModel):
    question: str


class CustomerCreateRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    company: str = ""
    plan: str = "Basic"


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None


class TicketCreateRequest(BaseModel):
    customer_id: int
    issue: str
    priority: str = "Medium"


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    issue: Optional[str] = None


# =====================================================
# BASIC ENDPOINTS
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Customer Support CRM Agent API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =====================================================
# AI CHAT
# =====================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
   current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    try:

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.question
                    }
                ]
            }
        )

        messages = result.get("messages", [])

        # ==========================================
        # FINAL ANSWER
        # ==========================================

        answer = ""

        if messages:

            last_message = messages[-1]

            if hasattr(last_message, "content"):
                answer = last_message.content

        # ==========================================
        # TOOLS USED
        # ==========================================

        tools_used = []

        for message in messages:

            if hasattr(message, "tool_calls"):

                for tool_call in message.tool_calls:

                    tool_name = tool_call.get("name")

                    if tool_name:
                        tools_used.append(tool_name)

        # Remove duplicates
        tools_used = list(
            dict.fromkeys(tools_used)
        )

        # ==========================================
        # SOURCES
        # ==========================================

        sources = []

        for message in messages:

            # We only inspect tool results
            if message.__class__.__name__ == "ToolMessage":

                tool_name = getattr(
                    message,
                    "name",
                    None
                )

                tool_content = getattr(
                    message,
                    "content",
                    ""
                )

                # RAG source extraction
                if tool_name == "search_knowledge_base":

                    import re

                    matches = re.findall(
                        r"File:\s*(.+)",
                        str(tool_content)
                    )

                    for source in matches:

                        source = source.strip()

                        page = None

                        page_match = re.search(
                            r", page (\d+)",
                            source
                        )

                        if page_match:

                            page = int(
                                page_match.group(1)
                            )

                            source = re.sub(
                                r", page \d+",
                                "",
                                source
                            )

                        source_data = {
                            "type": "document",
                            "name": source
                        }

                        if page is not None:
                            source_data["page"] = page

                        if source_data not in sources:
                            sources.append(source_data)

        return {
            "success": True,
            "answer": answer,
            "tools_used": tools_used,
            "sources": sources
        }

    except Exception:
        logger.exception("AI agent request failed.")

        raise HTTPException(
            status_code=500,
            detail="The AI agent is temporarily unavailable. Please try again."
        )


# =====================================================
# CUSTOMER API
# =====================================================


# -----------------------------------------------------
# CREATE CUSTOMER
# -----------------------------------------------------


@app.post("/customers")
def create_customer(
    request: CustomerCreateRequest,
   current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    result = CustomerService.create_customer(
        name=request.name,
        email=request.email,
        phone=request.phone,
        company=request.company,
        plan=request.plan
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# -----------------------------------------------------
# GET / SEARCH CUSTOMERS
# -----------------------------------------------------

@app.get("/customers")
def search_customers(
    query: str = "",
   current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)
):

    result = CustomerService.search_customers(query)

    return result


# -----------------------------------------------------
# GET CUSTOMER BY ID
# -----------------------------------------------------

@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = CustomerService.get_customer(customer_id)

    if not result.get("success"):

        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return result


# -----------------------------------------------------
# UPDATE CUSTOMER
# -----------------------------------------------------

@app.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    request: CustomerUpdateRequest,
   current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    result = CustomerService.update_customer(
        customer_id=customer_id,
        name=request.name,
        email=request.email,
        phone=request.phone,
        company=request.company,
        status=request.status,
        plan=request.plan
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# -----------------------------------------------------
# DELETE CUSTOMER
# -----------------------------------------------------

@app.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(require_role("Admin"))
    ):

    result = CustomerService.delete_customer(customer_id)

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# =====================================================
# CUSTOMER IMPORT API
# =====================================================

@app.post("/customers/import")
def import_customers(
    file: UploadFile = File(...),
current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    allowed_extensions = {
        ".csv",
        ".xlsx"
    }

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported."
        )

    upload_dir = Path(
        "uploads/customers"
    )

    upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_filename = Path(file.filename or "upload").name
    file_path = upload_dir / safe_filename

    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        result = CustomerImportService.import_customers(
            str(file_path)
        )

        return result

    except Exception:
        logger.exception("Customer import API request failed.")

        raise HTTPException(
            status_code=500,
            detail="Customer import failed. Please check the file and try again."
        )

    finally:

        file.file.close()


# =====================================================
# TICKET API
# =====================================================


# -----------------------------------------------------
# CREATE TICKET
# -----------------------------------------------------

@app.post("/tickets")
def create_ticket(
    request: TicketCreateRequest,
    current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
    ):

    result = TicketService.create_ticket(
        customer_id=request.customer_id,
        issue=request.issue,
        priority=request.priority
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# -----------------------------------------------------
# GET ALL TICKETS
# -----------------------------------------------------

@app.get("/tickets")
def get_tickets(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = TicketService.get_tickets()

    return result


# -----------------------------------------------------
# GET TICKET BY ID
# -----------------------------------------------------

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int,
              current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = TicketService.get_ticket(ticket_id)

    if not result.get("success"):

        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return result


# -----------------------------------------------------
# UPDATE TICKET
# -----------------------------------------------------

@app.put("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: int,
    request: TicketUpdateRequest,
    current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    result = TicketService.update_ticket(
        ticket_id=ticket_id,
        status=request.status,
        priority=request.priority,
        issue=request.issue
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# =====================================================
# ANALYTICS API
# =====================================================


# -----------------------------------------------------
# TICKET OVERVIEW
# -----------------------------------------------------

@app.get("/analytics/ticket-overview")
def get_ticket_overview(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = AnalyticsService.get_ticket_overview()

    return result


# -----------------------------------------------------
# TICKET STATUS SUMMARY
# -----------------------------------------------------

@app.get("/analytics/ticket-status")
def get_ticket_status_summary(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = AnalyticsService.get_ticket_status_summary()

    return result


# -----------------------------------------------------
# TICKET PRIORITY SUMMARY
# -----------------------------------------------------

@app.get("/analytics/ticket-priority")
def get_ticket_priority_summary(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = AnalyticsService.get_ticket_priority_summary()

    return result


# -----------------------------------------------------
# HIGH PRIORITY OPEN TICKETS
# -----------------------------------------------------

@app.get("/analytics/high-priority-open")
def get_high_priority_open_tickets(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = AnalyticsService.get_high_priority_open_tickets()

    return result


# -----------------------------------------------------
# CUSTOMER TICKET SUMMARY
# -----------------------------------------------------

@app.get("/analytics/customer-ticket-summary")
def get_customer_ticket_summary(current_user: User = Depends(
    require_role("Admin", "Support Agent", "Viewer")
)):

    result = AnalyticsService.get_customer_ticket_summary()

    return result


# =====================================================
# RAG FILE UPLOAD
# =====================================================

rag_service = RAGService()


@app.post("/knowledge/upload")
def upload_knowledge_file(
    file: UploadFile = File(...),
   current_user: User = Depends(
    require_role("Admin", "Support Agent")
)
):

    allowed_extensions = {
        ".pdf",
        ".txt",
        ".docx"
    }

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF, TXT and DOCX files are supported."
            )
        )

    upload_dir = Path(
        "documents/uploads/knowledge"
    )

    upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_filename = Path(file.filename or "upload").name
    file_path = upload_dir / safe_filename

    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        result = rag_service.add_document(
            str(file_path)
        )

        return result

    except Exception:
        logger.exception("Knowledge base upload API request failed.")

        raise HTTPException(
            status_code=500,
            detail="Knowledge base upload failed. Please check the file and try again."
        )

    finally:

        file.file.close()