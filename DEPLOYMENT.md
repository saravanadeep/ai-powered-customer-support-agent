# Deployment Documentation – AI-Powered Customer Support CRM

## 1. Project Overview

This document explains the deployment architecture, infrastructure configuration, deployment procedure, service management, and recovery process for the AI-Powered Customer Support CRM application.

The application uses a distributed deployment architecture, with the Streamlit frontend hosted on AWS EC2 and the FastAPI backend hosted on Render.

**Live Application:** https://smart-support-ai.duckdns.org

**Backend API:** https://ai-powered-customer-support-agent.onrender.com

**API Documentation:** https://ai-powered-customer-support-agent.onrender.com/docs

**GitHub Repository:** https://github.com/saravanadeep/ai-powered-customer-support-agent

**Deployment Branch:** `feature/hybrid-rag`

---

## 2. System Architecture

The application follows a frontend-backend architecture.

### Architecture Components

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | Streamlit | User interface and CRM dashboard |
| Web Server | Nginx | Reverse proxy and HTTPS termination |
| Frontend Hosting | AWS EC2 | Hosts the Streamlit application |
| Backend | FastAPI | API endpoints and business logic |
| Backend Hosting | Render | Hosts the FastAPI application |
| Database | Neon PostgreSQL | Stores application data |
| AI Integration | Groq / LangChain | LLM-powered customer support |
| Document Retrieval | RAG | Knowledge retrieval and document-based responses |
| Object Storage | S3-compatible storage | Stores uploaded documents |
| Domain | DuckDNS | Provides a public application hostname |
| SSL | Let's Encrypt / Certbot | HTTPS certificate management |
| Version Control | Git / GitHub | Source code management |

### Application Request Flow

1. Users access the application through the DuckDNS HTTPS domain.
2. Nginx receives incoming HTTP/HTTPS requests.
3. Nginx forwards application requests to Streamlit running locally on port 8501.
4. Streamlit communicates with the FastAPI backend hosted on Render.
5. FastAPI processes requests and interacts with PostgreSQL, AI services, RAG components, and object storage.
6. The backend returns responses to Streamlit, which displays them in the browser.

### Architecture Diagram

```text
                 USER BROWSER
                      |
                      | HTTPS
                      v
             DuckDNS Domain
                      |
                      v
              AWS EC2 INSTANCE
                Ubuntu 24.04
                      |
                      v
                   NGINX
                      |
                      v
              STREAMLIT FRONTEND
               127.0.0.1:8501
                      |
                      | HTTPS API Requests
                      v
               RENDER PLATFORM
                 FASTAPI BACKEND
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       NEON DB     GROQ / AI   OBJECT STORAGE
      PostgreSQL    SERVICES     Documents
```

---

## 3. AWS EC2 Infrastructure

### Instance Configuration

| Configuration | Value |
|---|---|
| Cloud Provider | AWS |
| Region | Mumbai (`ap-south-1`) |
| Operating System | Ubuntu 24.04 LTS |
| Instance Type | `t3.micro` |
| Storage | 8 GB gp3 |
| Application Port | 8501 (localhost only) |
| Web Server | Nginx |
| Frontend Service | Streamlit |

### Installed Software

- Python 3.12
- Git
- Nginx
- Streamlit
- Requests
- Pandas
- Certbot

### Connect to EC2

From the local Mac terminal:

```bash
ssh -i ~/aws-keys/customer-support-frontend-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Replace `YOUR_EC2_PUBLIC_IP` with the current EC2 public IP address.

### Project Directory

```text
/home/ubuntu/ai-powered-customer-support-agent/
│
├── app_ui.py
├── app/
├── requirements.txt
├── .gitignore
├── venv/
└── DEPLOYMENT.md
```

The frontend uses the deployed Render API:

```python
API_URL = "https://ai-powered-customer-support-agent.onrender.com"
```

---

## 4. Frontend Deployment

### Clone Repository

```bash
git clone -b feature/hybrid-rag \
https://github.com/saravanadeep/ai-powered-customer-support-agent.git
```

### Navigate to Project

```bash
cd ai-powered-customer-support-agent
```

### Create Virtual Environment

```bash
python3 -m venv venv
```

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Install Frontend Dependencies

```bash
pip install streamlit requests pandas
```

### Run Streamlit

For manual testing:

```bash
streamlit run app_ui.py --server.address 127.0.0.1 --server.port 8501
```

The production application runs through a systemd service.

---

## 5. Systemd Service Configuration

The Streamlit frontend is managed using systemd to ensure automatic startup and recovery.

**Service File:**

```text
/etc/systemd/system/customer-support-frontend.service
```

### Service Configuration

```ini
[Unit]
Description=Customer Support CRM Streamlit Frontend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ai-powered-customer-support-agent
ExecStart=/home/ubuntu/ai-powered-customer-support-agent/venv/bin/streamlit run /home/ubuntu/ai-powered-customer-support-agent/app_ui.py --server.address 127.0.0.1 --server.port 8501
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable customer-support-frontend
sudo systemctl start customer-support-frontend
```

### Service Management Commands

Check status:

```bash
sudo systemctl status customer-support-frontend
```

Restart:

```bash
sudo systemctl restart customer-support-frontend
```

Stop:

```bash
sudo systemctl stop customer-support-frontend
```

View logs:

```bash
sudo journalctl -u customer-support-frontend -f
```

---

## 6. Nginx Reverse Proxy Configuration

Nginx acts as a reverse proxy between the public internet and the Streamlit frontend.

**Configuration File:**

```text
/etc/nginx/sites-available/customer-support-frontend
```

The Nginx server:

- Accepts public HTTP and HTTPS traffic.
- Proxies requests to Streamlit on `127.0.0.1:8501`.
- Supports WebSocket connections.
- Handles HTTPS using Let's Encrypt certificates.

### Nginx Management

Check configuration:

```bash
sudo nginx -t
```

Restart:

```bash
sudo systemctl restart nginx
```

Reload:

```bash
sudo systemctl reload nginx
```

Check service:

```bash
sudo systemctl status nginx
```

---

## 7. Domain and HTTPS Configuration

### Domain

DuckDNS hostname:

```text
smart-support-ai.duckdns.org
```

The DNS A record points to the EC2 public IPv4 address.

### SSL Certificate

SSL certificates are managed using Let's Encrypt and Certbot.

Certificate directory:

```text
/etc/letsencrypt/live/smart-support-ai.duckdns.org/
```

Certificate verification:

```bash
sudo certbot certificates
```

Check automatic renewal timer:

```bash
sudo systemctl status certbot.timer
```

### HTTPS Renewal

Certbot is configured to run twice daily through a systemd timer.

A previous staging renewal dry run encountered a connection reset. The existing production certificate remained valid. Renewal should be tested and verified again before the certificate expires.

Certificate expiry should be monitored rather than assumed to renew successfully.

---

## 8. Backend Deployment – Render

The FastAPI backend is deployed separately on Render.

**Backend URL:**

```text
https://ai-powered-customer-support-agent.onrender.com
```

**Swagger Documentation:**

```text
https://ai-powered-customer-support-agent.onrender.com/docs
```

The backend handles:

- User authentication
- Customer management
- Ticket management
- AI-powered support
- Document upload
- Retrieval-Augmented Generation (RAG)
- Database operations
- Administrative operations

### Environment Variables

Backend environment variables are configured in the Render dashboard.

Examples of configured variable names:

```text
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
GROQ_API_KEY
GROQ_MODEL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_ENDPOINT_URL_S3
TAVILY_API_KEY
RAG_BACKEND
TFIDF_REMOTE_SYNC
```

**Security:** Never store actual API keys, passwords, JWT secrets, database URLs, or AWS credentials in GitHub or this documentation.

---

## 9. Database and Object Storage

### Neon PostgreSQL

Neon PostgreSQL provides the application's relational database.

The database connection string is configured through the backend's `DATABASE_URL` environment variable on Render.

### Object Storage

S3-compatible object storage is used for document storage.

The backend accesses storage through its configured environment variables.

Credentials must remain private and should have only the permissions required by the application.

---

## 10. GitHub Deployment Workflow

The frontend source code is maintained in GitHub.

**Repository:**

```text
https://github.com/saravanadeep/ai-powered-customer-support-agent
```

**Branch:**

```text
feature/hybrid-rag
```

### Push Local Changes

```bash
git add .
git commit -m "Describe your changes"
git push origin feature/hybrid-rag
```

### Deploy Latest Frontend Code to EC2

A deployment script is available:

```text
/home/ubuntu/deploy-frontend.sh
```

Run:

```bash
~/deploy-frontend.sh
```

The script:

1. Checks the Git working tree.
2. Fetches the latest branch from GitHub.
3. Performs a fast-forward-only pull.
4. Restarts the Streamlit service.
5. Verifies that the service is active.

The script intentionally stops if uncommitted or untracked files are present.

**Note:** This deployment script updates the EC2 frontend only. Backend changes must be deployed separately through the Render deployment workflow.

---

## 11. Restart and Recovery Procedures

### Restart Streamlit

```bash
sudo systemctl restart customer-support-frontend
```

### Restart Nginx

```bash
sudo systemctl restart nginx
```

### Check All Services

```bash
sudo systemctl is-active nginx
sudo systemctl is-active customer-support-frontend
sudo systemctl is-active certbot.timer
```

Expected result:

```text
active
active
active
```

### Check Listening Ports

```bash
sudo ss -tulnp
```

Expected application networking:

| Port | Service | Access |
|---|---|---|
| 22 | SSH | Restricted through AWS security group |
| 80 | Nginx | Public HTTP |
| 443 | Nginx | Public HTTPS |
| 8501 | Streamlit | Localhost only |

### EC2 Reboot Recovery

The Nginx service, Streamlit service, and Certbot timer are enabled to start automatically.

To reboot EC2:

```bash
sudo reboot
```

After the instance restarts:

1. Reconnect through SSH.
2. Check the status of Nginx.
3. Check the status of Streamlit.
4. Check the Certbot timer.
5. Open the public application URL.

The application has been tested after an EC2 reboot and the services recovered successfully.

### Troubleshooting Commands

Check Streamlit logs:

```bash
sudo journalctl -u customer-support-frontend -n 100
```

Check Nginx logs:

```bash
sudo tail -n 100 /var/log/nginx/error.log
```

Check disk usage:

```bash
df -h
```

Check RAM and swap:

```bash
free -h
```

Check CPU:

```bash
top
```

---

## 12. Security Configuration

The deployment follows these security practices:

- SSH access is restricted to the administrator's IP address.
- HTTP and HTTPS are publicly accessible through Nginx.
- Streamlit is bound to localhost instead of being exposed directly.
- Port 8501 is not publicly exposed in the EC2 security group.
- Backend credentials are configured in Render environment variables.
- `.env` files are excluded through `.gitignore`.
- SSH private keys are stored locally and are not committed to GitHub.
- HTTPS is enabled using Let's Encrypt.
- AWS credentials should use least-privilege IAM permissions.

---

## 13. Monitoring and Maintenance

Regular maintenance tasks include:

- Monitor EC2 CPU, RAM, swap, and disk usage.
- Monitor AWS billing and remaining credits.
- Verify that the Render backend is available.
- Monitor SSL certificate expiry and renewal.
- Keep GitHub synchronized with deployed frontend changes.
- Maintain backups of important application data.
- Review service logs when errors occur.

### Useful Monitoring Commands

```bash
free -h
df -h
top
sudo systemctl status nginx
sudo systemctl status customer-support-frontend
sudo systemctl status certbot.timer
```

---

## 14. Deployment Verification

The following deployment checks have been completed:

| Test | Result |
|---|---|
| EC2 frontend deployment | Successful |
| Render backend integration | Successful |
| DuckDNS domain | Working |
| HTTPS access | Working |
| Nginx reverse proxy | Working |
| Streamlit systemd service | Active |
| Automatic service startup | Verified |
| GitHub synchronization | Successful |
| Deployment script | Successful |
| CRM end-to-end testing | Successful |
| EC2 reboot recovery | Successful |
| RAM, CPU and disk checks | Completed |

The Let's Encrypt staging dry-run connection issue remains a follow-up maintenance item. The currently installed production certificate is valid.

---

## 15. Conclusion

The AI-Powered Customer Support CRM has been deployed using a distributed cloud architecture.

AWS EC2 hosts the Streamlit frontend, while Render hosts the FastAPI backend. Neon PostgreSQL provides database services, and object storage supports document management.

Nginx provides reverse proxy functionality, while DuckDNS and Let's Encrypt provide domain access and HTTPS.

The application has passed end-to-end functionality testing and EC2 reboot recovery testing.

This deployment demonstrates practical experience with cloud hosting, Linux administration, API integration, reverse proxies, HTTPS configuration, Git-based deployment, and production application management.
