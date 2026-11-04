<h1 align="center">AI-Powered Customer Support & CRM Platform</h1>

<p align="center">
  <strong>An Agentic AI customer support and CRM platform built with FastAPI, Streamlit, PostgreSQL, LangChain, and Retrieval-Augmented Generation.</strong>
</p>

<p align="center">
  <a href="https://ai-powered-customer-support-agent.onrender.com/docs">API Documentation (Swagger UI)</a> •
  <a href="https://github.com/saravanadeep/ai-powered-customer-support-agent">GitHub Repository</a>
</p>

---

## Overview

The **AI-Powered Customer Support & CRM Agent** is a customer relationship management application that combines customer and ticket operations with an AI agent. The agent can select from available tools to work with CRM records, support tickets, internal knowledge, analytics, and external web information.

The application uses a Streamlit frontend and a FastAPI backend. Its agent is built with LangChain and a Groq-hosted language model.

## Key Features

### 1. Customer Relationship Management
- Create, search, retrieve, update, and delete customer records.
- Use CRM tools to access customer information.

### 2. Ticket Management
- Create, retrieve, and update customer support tickets.
- Access ticket information through agent tools.

### 3. Agentic AI Support
- Tool-using agent built with LangChain.
- Uses the configured Groq language model.
- Chooses relevant tools based on the user's request.
- Handles CRM, ticket, knowledge-base, analytics, and web-search tasks.

### 4. Knowledge Base and RAG
- Search internal support information and uploaded documents.
- Uses a knowledge-base search tool exposed to the agent.
- Supports retrieval-augmented answers grounded in retrieved content.

### 5. Analytics
- Ticket overview and status summaries.
- Ticket priority summaries.
- High-priority open ticket retrieval.
- Customer ticket summaries.

### 6. Customer Import
- Import customer records from supported files through the API.

### 7. Authentication and Administration
- Authentication endpoints and JWT-based access configuration.
- Role-based authorization for API operations.
- User management endpoints.

## Agent Tools

The LangChain agent is configured with tools in these areas:

| Tool area | Capabilities |
|---|---|
| Customer CRM | Create, search, retrieve, update, and delete customers |
| Tickets | Create, retrieve, and update tickets |
| Customer import | Import customer data |
| Knowledge base | Search internal documents through RAG |
| Web search | Retrieve current external information |
| Analytics | Retrieve ticket and customer-ticket summaries |

The agent instructions distinguish internal company knowledge from current external information and direct requests to the appropriate tool.

## Architecture

```text
                 USER
                  |
                  v
             STREAMLIT UI
                  |
              HTTP API
                  |
                  v
              FASTAPI
                  |
            LANGCHAIN AGENT
                  |
       +----------+-----------+
       |          |           |
       v          v           v
    CRM/Ticket  Knowledge   Analytics /
      Tools     Base (RAG)  Web Search
       |          |           |
       v          v           v
   PostgreSQL  RAG Backend  External Data
                  |
                  v
              GROQ LLM
```

## Technology Stack

| Area | Technologies |
|---|---|
| Language | Python, SQL |
| Frontend | Streamlit |
| Backend | FastAPI |
| Agent framework | LangChain |
| LLM provider | Groq |
| Retrieval | RAG knowledge-base search |
| Database | PostgreSQL, SQLAlchemy |
| External search | LangChain Tavily integration |
| Document processing | PyPDF, DOCX/TXT loaders |
| Authentication | JWT, pwdlib |
| Storage integration | Boto3 / S3-compatible storage |
| Testing | Pytest |

## Repository Structure

The main branch has its own code and dependency set. Refer to the repository tree for the current exact layout. Core application areas include:

- `app/agent.py` — agent instructions and registered tools.
- `app/api.py` — FastAPI application and API routes.
- `app/tools/` — CRM, RAG, analytics, and web-search tools.
- `app/services/` — business logic and supporting services.
- `app/models.py` — database models.
- `app/config.py` — environment-based configuration.
- `main.py` — application entry point.

## Local Setup

### 1. Clone the main branch

```bash
git clone -b main https://github.com/saravanadeep/ai-powered-customer-support-agent.git
cd ai-powered-customer-support-agent
```

### 2. Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```powershell
python -m venv venv
venv\\Scripts\\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file and provide the values required by `app/config.py` and the services you intend to use. These may include database, Groq, Tavily, authentication, and storage configuration.

Never commit real credentials, API keys, database URLs, or private keys to GitHub.

### 5. Run the application

The FastAPI application is exposed as `app` from `main.py`:

```bash
uvicorn main:app --reload
```

Run the Streamlit UI in a separate terminal using the Streamlit entry-point file present on the main branch:

```bash
streamlit run streamlit.py
```

API documentation is available locally at:

`http://127.0.0.1:8000/docs`

> Setup note: Verify required environment variables and any external services before starting the application. The main branch's requirements and entry-point filenames may differ from the deployment branch.

## Branches

This repository contains multiple development branches:

- **main** — the main development codebase. This README describes this branch.
- **feature/hybrid-rag** — a separate branch containing the currently documented deployment setup and its own README and `DEPLOYMENT.md`.

The feature branch README and deployment guide should be consulted for that branch's deployment-specific details. Do not assume its file names, dependencies, or deployment workflow apply to `main`.

## Author

**K. R. Saravanadeep**

B.Tech — Computer Science and Engineering

**Areas of Interest**
- Artificial Intelligence
- Machine Learning
- Data Science
- Generative AI
- Agentic AI
- Backend Development

**Connect**
- GitHub: https://github.com/saravanadeep
- LinkedIn: https://www.linkedin.com/in/k-r-saravanadeep-40249b306

---

<p align="center">
  <strong>Built with Python, AI, and a passion for solving real-world problems.</strong>
</p>
