#        AI-Powered Customer Support & CRM Platform

<p align="center">
  <strong>An intelligent customer support platform powered by Generative AI, Hybrid RAG, and Agentic AI.</strong>
</p>

<p align="center">
  <a href="https://smart-support-ai.duckdns.org">Live Application</a> •
  <a href="https://ai-powered-customer-support-agent.onrender.com/docs">API Documentation</a> •
  <a href="DEPLOYMENT.md">Deployment Guide</a>
</p>

---

## Overview

The **AI-Powered Customer Support & CRM Platform** is an intelligent customer relationship management system designed to streamline customer interactions, ticket management, and AI-powered support operations.

The platform combines a Streamlit frontend, FastAPI backend, PostgreSQL database, Retrieval-Augmented Generation (RAG), and Agentic AI to provide an integrated customer support experience.

It enables users to manage customers and support tickets, interact with an AI support assistant, and retrieve relevant information from uploaded knowledge documents.

## Live Deployment

| Component | URL |
|---|---|
| Live Application | https://smart-support-ai.duckdns.org |
| FastAPI Backend | https://ai-powered-customer-support-agent.onrender.com |
| Swagger API Docs | https://ai-powered-customer-support-agent.onrender.com/docs |
| GitHub Repository | https://github.com/saravanadeep/ai-powered-customer-support-agent |

## Key Features

### 1. Customer Relationship Management
- Create and manage customer records.
- Search and retrieve customer information.
- Organize customer information through the CRM interface.

### 2. Ticket Management
- Create and manage customer support tickets.
- Retrieve and track ticket information.
- Integrate ticket operations with customer records.

### 3. AI-Powered Customer Support
- Interactive AI support assistant.
- LLM-powered responses using Groq.
- Context-aware assistance through knowledge retrieval.

### 4. Hybrid Retrieval-Augmented Generation
- Retrieve relevant information from knowledge documents.
- Combine retrieval capabilities with LLM-based response generation.
- Support document-based question answering.

### 5. Document Management
- Upload knowledge documents through the application.
- Use document content as a knowledge source for AI-powered responses.
- Integrate document processing with the RAG pipeline.

### 6. Authentication and Administration
- User authentication.
- JWT-based authentication configuration.
- Administrative user management.
- User role and account status management.

## System Architecture

The application follows a distributed frontend-backend architecture.

```text
                  USER
                   |
                   v
              WEB BROWSER
                   |
                HTTPS
                   |
                   v
             DUCKDNS DOMAIN
                   |
                   v
              AWS EC2
             UBUNTU 24.04
                   |
                   v
                 NGINX
                   |
                   v
           STREAMLIT FRONTEND
             (Port 8501)
                   |
              HTTPS API
                   |
                   v
            RENDER PLATFORM
             FASTAPI BACKEND
                   |
          +--------+--------+
          |        |        |
          v        v        v
       NEON DB   GROQ AI  OBJECT STORAGE
     PostgreSQL   LLMs     Documents
```

### Architecture Components

| Component | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Interactive CRM interface |
| Backend | FastAPI | REST API and business logic |
| Database | Neon PostgreSQL | Relational data storage |
| LLM | Groq | AI-powered responses |
| AI Framework | LangChain | LLM and retrieval integration |
| RAG | Hybrid RAG | Knowledge retrieval |
| Embeddings | Hugging Face | Document embeddings |
| Vector Storage | ChromaDB / configured retrieval storage | Knowledge retrieval |
| Object Storage | S3-compatible storage | Document storage |
| Web Server | Nginx | Reverse proxy |
| Frontend Hosting | AWS EC2 | Streamlit hosting |
| Backend Hosting | Render | FastAPI hosting |
| Domain | DuckDNS | Public application domain |
| SSL | Let's Encrypt | HTTPS security |

## Technology Stack

**Programming Languages**
- Python
- SQL

**Frontend**
- Streamlit

**Backend**
- FastAPI
- REST APIs

**Artificial Intelligence**
- Generative AI
- Large Language Models
- Retrieval-Augmented Generation
- Hybrid RAG
- Agentic AI
- LangChain
- Groq
- Hugging Face Embeddings

**Database and Storage**
- PostgreSQL
- Neon
- ChromaDB
- S3-compatible Object Storage

**Cloud and Deployment**
- AWS EC2
- Render
- Nginx
- Ubuntu Linux
- DuckDNS
- Let's Encrypt
- Certbot
- Git and GitHub

## Project Structure

```text
ai-powered-customer-support-agent/
│
├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── ...
│
├── app_ui.py
├── main.py
├── requirements.txt
├── requirements-render.txt
├── requirements-local.txt
├── create_admin.py
├── tests/
├── .gitignore
├── README.md
└── DEPLOYMENT.md
```

*Note: The exact internal folders depend on the current repository version.*

## Local Installation and Setup

### 1. Clone the repository

```bash
git clone -b feature/hybrid-rag \
https://github.com/saravanadeep/ai-powered-customer-support-agent.git

cd ai-powered-customer-support-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

### 3. Activate the environment

macOS / Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

Use the appropriate requirements file for your local development environment:

```bash
pip install -r requirements-local.txt
```

### 5. Configure environment variables

Create a `.env` file using the variable names required by the backend configuration.

Configure the necessary database, authentication, AI provider, and storage credentials.

**Never commit `.env` files or actual credentials to GitHub.**

### 6. Start the application

Start the FastAPI backend using the project's configured entry point:

```bash
uvicorn main:app --reload
```

Start the Streamlit frontend in a separate terminal:

```bash
streamlit run app_ui.py
```

Refer to the backend configuration and `DEPLOYMENT.md` for environment-specific setup details.

## Deployment

The application is deployed using a distributed cloud architecture:

- **AWS EC2:** Hosts the Streamlit frontend.
- **Nginx:** Handles reverse proxy and HTTPS traffic.
- **Render:** Hosts the FastAPI backend.
- **Neon:** Provides PostgreSQL database services.
- **DuckDNS:** Provides the public domain.
- **Let's Encrypt:** Provides SSL certificates.

### Frontend Deployment

The frontend is deployed on AWS EC2 and managed through a systemd service.

A deployment script is available:

```bash
~/deploy-frontend.sh
```

This script fetches the latest code from GitHub, performs a fast-forward-only update, restarts Streamlit, and checks the service status.

### Backend Deployment

The FastAPI backend is deployed separately on Render.

Backend environment variables are configured through the Render dashboard.

For complete deployment instructions, service management, HTTPS configuration, and recovery procedures, see:

**[DEPLOYMENT.md](DEPLOYMENT.md)**

## Application Screenshots

Screenshots of the application can be added here to demonstrate:

- CRM Dashboard
- Customer Management
- Ticket Management
- AI Support Chat
- Knowledge Document Upload
- Administrative Dashboard

## Future Improvements

Potential areas for future development include:

- Real-time customer support analytics.
- Advanced ticket classification and prioritization.
- Improved multi-agent workflows.
- Voice-based AI customer support.
- Automated customer sentiment analysis.
- Enhanced monitoring and observability.

## Deployment Verification

The deployed application has been tested for:

- Frontend and backend connectivity.
- Customer and ticket management.
- AI support chat.
- Document upload.
- Authentication and administrative functionality.
- HTTPS access.
- Automatic service startup.
- EC2 reboot recovery.

The Let's Encrypt staging renewal dry-run connection issue remains a maintenance item; the currently installed production certificate is valid.

## Author

**K. R. Saravanadeep**

B.Tech – Computer Science and Engineering

**Areas of Interest**
- Artificial Intelligence
- Machine Learning
- Data Science
- Generative AI
- Agentic AI
- Backend Development

**Connect with me**

- GitHub: https://github.com/saravanadeep
- LinkedIn: https://www.linkedin.com/in/k-r-saravanadeep-40249b306

---

<p align="center">
  <strong>Built with Python, AI, and a passion for solving real-world problems.</strong>
</p>
