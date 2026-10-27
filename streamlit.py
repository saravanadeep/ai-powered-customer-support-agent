import requests

import pandas as pd

import streamlit as st

# =====================================================

# CONFIGURATION

# =====================================================

API_URL = "http://127.0.0.1:8000"

st.set_page_config(

    page_title="Customer Support CRM",

    page_icon="🤖",

    layout="wide"

)

# =====================================================

# SIDEBAR STYLING

# =====================================================

st.markdown(

    """

    <style>

    /* =================================================

       SIDEBAR WIDTH

       ================================================= */

    [data-testid="stSidebar"] {

        min-width: 280px;

        max-width: 280px;

    }

    /* =================================================

       SIDEBAR TITLE

       ================================================= */

    [data-testid="stSidebar"] h1 {

        font-size: 28px !important;

        font-weight: 700 !important;

    }

    /* =================================================

       RADIO CONTAINER

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] > div {

        gap: 8px !important;

    }

    /* =================================================

       NAVIGATION ITEM

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] label {

        font-size: 19px !important;

        font-weight: 600 !important;

        padding: 12px 14px !important;

        margin: 4px 0 !important;

        border-radius: 20px !important;

        width: 120% !important;

        transition: all 0.3s ease-in-out;

    }

    /* =================================================

       HIDE RADIO CIRCLE

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {

        display: none !important;

    }

    /* =================================================

       HOVER EFFECT

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {

        background-color: rgba(49, 51, 63, 0.12) !important;

    }

    /* =================================================

       SELECTED NAVIGATION ITEM

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(

        input:checked

    ) {

        background-color: #1E3A8A !important;

        color: white !important;

        font-weight: 700 !important;

    }

    /* =================================================

       SELECTED TEXT

       ================================================= */

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(

        input:checked

    ) p {

        color: white !important;

    }

    /* =================================================

       CAPTION

       ================================================= */

    [data-testid="stSidebar"] .stCaption {

        font-size: 14px !important;

    }

    </style>

    """,

    unsafe_allow_html=True

)

# =====================================================

# =====================================================
# AUTHENTICATION
# =====================================================

def auth_headers():
    """Return the Bearer token header for authenticated API requests."""
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def normalize_user_data(payload):
    """Normalize flat or nested user data returned by the authentication API."""
    if not isinstance(payload, dict):
        return {}

    for key in ("user", "current_user", "data"):
        if isinstance(payload.get(key), dict):
            payload = payload[key]
            break

    return {
        "user_id": payload.get("user_id", payload.get("id")),
        "username": payload.get("username", payload.get("name")),
        "email": payload.get("email"),
        "role": payload.get("role", payload.get("user_role")),
    }

# Keep the token in Streamlit session state and validate it with FastAPI.
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state.get("access_token"):
    try:
        me_response = requests.get(
            f"{API_URL}/auth/me",
            headers=auth_headers(),
            timeout=10,
        )
    except requests.exceptions.RequestException:
        st.error(
            "Cannot connect to the FastAPI server. Start the backend and try again."
        )
        st.stop()

    if me_response.status_code == 200:
        st.session_state["user"] = normalize_user_data(me_response.json())
    elif me_response.status_code == 401:
        # Expired or invalid token: clear the session and ask the user to log in again.
        st.session_state["access_token"] = None
        st.session_state["user"] = None
    else:
        st.error(
            f"Unable to validate your session ({me_response.status_code}). "
            "Please check the FastAPI backend."
        )
        st.stop()

if not st.session_state.get("access_token"):
    st.title("🔐 Customer Support CRM")
    st.subheader("Sign in")
    st.caption("Log in with the account created by your CRM administrator.")

    with st.form("login_form", clear_on_submit=False):
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input(
            "Password", type="password", key="login_password"
        )
        login_submitted = st.form_submit_button(
            "Log in", type="primary", use_container_width=True
        )

    if login_submitted:
        if not login_username.strip() or not login_password:
            st.warning("Enter both your username and password.")
        else:
            try:
                login_response = requests.post(
                    f"{API_URL}/auth/login",
                    json={
                        "username": login_username.strip(),
                        "password": login_password,
                    },
                    timeout=15,
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data.get("access_token")

                    if not access_token:
                        st.error("Login response did not contain an access token.")
                    else:
                        st.session_state["access_token"] = access_token
                        st.session_state["user"] = normalize_user_data(login_data.get("user", login_data))
                        st.rerun()
                elif login_response.status_code in (401, 403):
                    try:
                        error_detail = login_response.json().get(
                            "detail", "Invalid username or password."
                        )
                    except ValueError:
                        error_detail = "Invalid username or password."
                    st.error(str(error_detail))
                else:
                    st.error(
                        f"Login failed ({login_response.status_code}). "
                        "Please try again."
                    )
            except requests.exceptions.RequestException:
                st.error(
                    "Cannot connect to FastAPI. Make sure the backend is running."
                )

    st.stop()

# CUSTOMER API FUNCTIONS

# =====================================================

def customer_api_get(endpoint, params=None):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Customer request failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def customer_api_post(

    endpoint,

    data=None,

    files=None

):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=data if files is None else None,
            files=files,
            headers=auth_headers(),
            timeout=30,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Customer request failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def customer_api_put(endpoint, data):

    try:

        response = requests.put(
            f"{API_URL}{endpoint}",
            json=data,
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Customer update failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def customer_api_delete(endpoint):

    try:

        response = requests.delete(
            f"{API_URL}{endpoint}",
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Customer deletion failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

# =====================================================

# TICKET API FUNCTIONS

# =====================================================

def ticket_api_get(endpoint, params=None):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Ticket request failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def ticket_api_post(endpoint, data):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=data,
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Ticket creation failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def ticket_api_put(endpoint, data):

    try:

        response = requests.put(
            f"{API_URL}{endpoint}",
            json=data,
            headers=auth_headers(),
            timeout=15,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Ticket update failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

# =====================================================

# AI AGENT API

# =====================================================

def agent_api_chat(question):

    try:

        response = requests.post(
            f"{API_URL}/chat",
            json={"question": question},
            headers=auth_headers(),
            timeout=60,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Agent request failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

# =====================================================

# KNOWLEDGE BASE API

# =====================================================

def knowledge_api_upload(uploaded_file):

    try:

        files = {

            "file": (

                uploaded_file.name,

                uploaded_file.getvalue(),

                uploaded_file.type

            )

        }

        response = requests.post(
            f"{API_URL}/knowledge/upload",
            files=files,
            headers=auth_headers(),
            timeout=60,
        )

        if response.status_code in [200, 201]:

            return response.json()

        try:

            error_data = response.json()

            if isinstance(error_data, dict):

                return {

                    "success": False,

                    "message": error_data.get(

                        "detail",

                        "Knowledge upload failed."

                    )

                }

        except Exception:

            pass

        return {

            "success": False,

            "message": response.text

        }

    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }

def api_get(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=auth_headers(),
            timeout=15,
        )

        return response

    except requests.exceptions.RequestException as e:

        st.error(

            f"❌ API connection error: {e}"

        )

        return None

# =====================================================

# SIDEBAR

# =====================================================

st.sidebar.title("🤖 Customer Support CRM")

current_user = st.session_state.get("user") or {}
current_role = str(current_user.get("role") or "").strip().lower()
current_username = current_user.get("username") or current_user.get("email") or "Unknown user"
role_label = current_user.get("role") or "Unknown role"

is_admin = current_role == "admin"
can_operate = current_role in {"admin", "support agent"}
is_viewer = current_role == "viewer"

st.sidebar.markdown(f"**Signed in:** {current_username}")
st.sidebar.markdown(f"**Role:** {role_label}")

if st.sidebar.button("Log out", use_container_width=True, key="logout_button"):
    st.session_state["access_token"] = None
    st.session_state["user"] = None
    st.session_state["messages"] = []
    st.session_state["navigation_page"] = "🏠 Dashboard"
    st.session_state["sidebar_navigation"] = "🏠 Dashboard"
    st.rerun()

st.sidebar.markdown("---")

all_navigation_options = [
    "🏠 Dashboard",
    "🤖 AI Support",
    "👥 Customers",
    "🎫 Tickets",
    "📊 Analytics",
    "📚 Knowledge Base",
]

# User management is visible only to Admins.
if is_admin:
    navigation_options = all_navigation_options + ["👤 User Management"]
elif can_operate:
    navigation_options = all_navigation_options
else:
    navigation_options = [
        "🏠 Dashboard",
        "👥 Customers",
        "🎫 Tickets",
        "📊 Analytics",
    ]

if "navigation_page" not in st.session_state:
    st.session_state["navigation_page"] = "🏠 Dashboard"
if "sidebar_navigation" not in st.session_state:
    st.session_state["sidebar_navigation"] = st.session_state["navigation_page"]

# If a user's role changes, do not leave them on a page they can no longer access.
if st.session_state["navigation_page"] not in navigation_options:
    st.session_state["navigation_page"] = "🏠 Dashboard"
if st.session_state["sidebar_navigation"] not in navigation_options:
    st.session_state["sidebar_navigation"] = st.session_state["navigation_page"]

def sync_navigation():
    st.session_state["navigation_page"] = st.session_state["sidebar_navigation"]

page = st.sidebar.radio(
    "Navigation",
    navigation_options,
    key="sidebar_navigation",
    on_change=sync_navigation,
)
st.session_state["navigation_page"] = page

st.sidebar.markdown("---")
st.sidebar.caption("Agentic AI Customer Support & CRM")

# =====================================================

# DASHBOARD

# =====================================================

def go_to_page(page_name):
    """Navigate only to pages allowed for the current role."""
    if page_name not in navigation_options:
        st.warning("Your role does not have access to that page.")
        return
    st.session_state["navigation_page"] = page_name
    st.session_state["sidebar_navigation"] = page_name

if page == "🏠 Dashboard":

    # =================================================

    # HEADER

    # =================================================

    st.title("🏠 Customer Support CRM")

    st.caption(

        "Welcome to your AI-powered Customer Support & CRM"

    )

    st.divider()

    # =================================================

    # FETCH BASIC DATA

    # =================================================

    overview_response = api_get(

        "/analytics/ticket-overview"

    )

    customer_response = customer_api_get(

        "/customers",

        params={"query": ""}

    )

    # =================================================

    # DEFAULT VALUES

    # =================================================

    total_customers = 0

    total_tickets = 0

    open_tickets = 0

    high_priority_tickets = 0

    # =================================================

    # CUSTOMER COUNT

    # =================================================

    if isinstance(customer_response, list):

        total_customers = len(

            customer_response

        )

    elif isinstance(customer_response, dict):

        customers = customer_response.get(

            "customers",

            customer_response.get(

                "data",

                []

            )

        )

        if isinstance(customers, list):

            total_customers = len(

                customers

            )

    # =================================================

    # TICKET OVERVIEW

    # =================================================

    if (

        overview_response

        and overview_response.status_code == 200

    ):

        overview = overview_response.json()

        total_tickets = overview.get(

            "total_tickets",

            0

        )

        open_tickets = overview.get(

            "open_tickets",

            0

        )

        high_priority_tickets = overview.get(

            "high_priority_tickets",

            0

        )

    # =================================================

    # KPI CARDS

    # =================================================

    st.subheader("📌 CRM Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(

            "👥 Customers",

            total_customers

        )

    with col2:

        st.metric(

            "🎫 Total Tickets",

            total_tickets

        )

    with col3:

        st.metric(

            "🟢 Open Tickets",

            open_tickets

        )

    with col4:

        st.metric(

            "🔥 High Priority",

            high_priority_tickets

        )

    st.divider()

    # =================================================

    # QUICK ACTIONS

    # =================================================

    if can_operate:
        st.subheader("⚡ Quick Actions")
        action1, action2, action3, action4 = st.columns(4)

        with action1:
            st.button(
                "➕ Create Customer",
                use_container_width=True,
                key="dashboard_create_customer",
                on_click=go_to_page,
                args=("👥 Customers",),
            )

        with action2:
            st.button(
                "🎫 Create Ticket",
                use_container_width=True,
                key="dashboard_create_ticket",
                on_click=go_to_page,
                args=("🎫 Tickets",),
            )

        with action3:
            st.button(
                "🤖 Ask AI Agent",
                use_container_width=True,
                key="dashboard_ai_support",
                on_click=go_to_page,
                args=("🤖 AI Support",),
            )

        with action4:
            st.button(
                "📚 Knowledge Base",
                use_container_width=True,
                key="dashboard_knowledge",
                on_click=go_to_page,
                args=("📚 Knowledge Base",),
            )
    else:
        st.info("Your Viewer role has read-only access to CRM records and analytics.")

    st.divider()

    # AI ASSISTANT

    # =================================================

    st.subheader("🤖 AI Customer Support")

    ai_col1, ai_col2 = st.columns(

        [2, 1]

    )

    with ai_col1:

        st.markdown(

            """

            ### Your AI Support Agent

            Use the AI agent to:

            - 🔍 Search customer information

            - 🎫 Manage support tickets

            - 📚 Search the knowledge base

            - 🌐 Search the web when required

            - 📊 Analyze CRM information

            """

        )

    with ai_col2:

        st.info(

            "💡 Your AI agent can work with "

            "CRM data, documents and external web information."

        )

    st.divider()

    # =================================================

    # PRIORITY ATTENTION

    # =================================================

    st.subheader("🚨 Priority Attention")

    high_priority_response = api_get(

        "/analytics/high-priority-open"

    )

    if (

        high_priority_response

        and high_priority_response.status_code == 200

    ):

        high_priority_data = (

            high_priority_response.json()

        )

        high_priority_rows = (

            high_priority_data.get(

                "tickets",

                []

            )

        )

        if high_priority_rows:

            st.warning(

                f"⚠️ {len(high_priority_rows)} "

                "high-priority ticket(s) need attention."

            )

            priority_df = pd.DataFrame(

                high_priority_rows

            )

            st.dataframe(

                priority_df,

                use_container_width=True,

                hide_index=True

            )

        else:

            st.success(

                "🎉 No high-priority open tickets."

            )

    else:

        st.error(

            "Unable to load priority information."

        )

    st.divider()

    # =================================================

    # SYSTEM STATUS

    # =================================================

    st.subheader("🖥️ System Status")

    status1, status2, status3 = st.columns(3)

    # -------------------------------------------------

    # CRM API

    # -------------------------------------------------

    with status1:

        try:

            if (

                overview_response

                and overview_response.status_code == 200

            ):

                st.success(

                    "🟢 CRM API\n\nOnline"

                )

            else:

                st.error(

                    "🔴 CRM API\n\nUnavailable"

                )

        except Exception:

            st.error(

                "🔴 CRM API\n\nUnavailable"

            )

    # -------------------------------------------------

    # AI AGENT

    # -------------------------------------------------

    with status2:

        st.success(

            "🟢 AI Agent\n\nReady"

        )

    # -------------------------------------------------

    # KNOWLEDGE BASE

    # -------------------------------------------------

    with status3:

        st.success(

            "🟢 Knowledge Base\n\nReady"

        )

# =====================================================

# AI SUPPORT

# =====================================================

elif page == "🤖 AI Support":

    st.title("🤖 AI Customer Support")

    if "messages" not in st.session_state:

        st.session_state.messages = []

    # Display previous messages

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            # Show tools and sources for assistant messages

            if message["role"] == "assistant":

                tools_used = message.get(

                    "tools_used",

                    []

                )

                sources = message.get(

                    "sources",

                    []

                )

                if tools_used:

                    with st.expander("🛠️ Tools Used"):

                        for tool in tools_used:

                            st.write(

                                f"🔧 `{tool}`"

                            )

                if sources:

                    with st.expander("📚 Retrieved Sources"):

                        for source in sources:

                            name = source.get(

                                "name",

                                "Unknown source"

                            )

                            page_number = source.get(

                                "page"

                            )

                            if page_number:

                                st.write(

                                    f"📄 {name} — Page {page_number}"

                                )

                            else:

                                st.write(

                                    f"📄 {name}"

                                )

    question = st.chat_input(

        "Ask the Customer Support Agent..."

    )

    if question:

        # Add user message

        st.session_state.messages.append(

            {

                "role": "user",

                "content": question

            }

        )

        with st.chat_message("user"):

            st.markdown(question)

        # Call backend agent

        result = agent_api_chat(

            question

        )

        if result:

            # Agent error

            if result.get("success") is False:

                st.error(

                    f"❌ Agent error: "

                    f"{result.get('message', 'Something went wrong.')}"

                )

            else:

                # Get response

                answer = result.get(

                    "answer",

                    "No response received from the agent."

                )

                # Get tools

                tools_used = result.get(

                    "tools_used",

                    []

                )

                # Get sources

                sources = result.get(

                    "sources",

                    []

                )

                # Save complete assistant message

                st.session_state.messages.append(

                    {

                        "role": "assistant",

                        "content": answer,

                        "tools_used": tools_used,

                        "sources": sources

                    }

                )

                # Display assistant response

                with st.chat_message("assistant"):

                    st.markdown(answer)

                    # Tools Used

                    if tools_used:

                        with st.expander(

                            "🛠️ Tools Used"

                        ):

                            for tool in tools_used:

                                st.write(

                                    f"🔧 `{tool}`"

                                )

                    # Retrieved Sources

                    if sources:

                        with st.expander(

                            "📚 Retrieved Sources"

                        ):

                            for source in sources:

                                name = source.get(

                                    "name",

                                    "Unknown source"

                                )

                                page_number = source.get(

                                    "page"

                                )

                                if page_number:

                                    st.write(

                                        f"📄 {name} "

                                        f"— Page {page_number}"

                                    )

                                else:

                                    st.write(

                                        f"📄 {name}"

                                    )

# =====================================================

# CUSTOMERS

# =====================================================

elif page == "👥 Customers":

    st.title("👥 Customer Management")

    # =================================================

    # SEARCH CUSTOMERS

    # =================================================

    st.subheader("🔍 Search Customers")

    search_query = st.text_input(

        "Search by name, email or company",

        placeholder="Example: Rahul",

        key="customer_search"

    )

    if st.button(

        "Search Customers",

        key="search_customer_button"

    ):

        result = customer_api_get(

            "/customers",

            params={

                "query": search_query

            }

        )

        if isinstance(

            result,

            dict

        ) and result.get("success") is False:

            st.error(

                f"❌ {result.get('message', 'Unable to search customers.')}"

            )

        else:

            customers = result

            if isinstance(result, dict):

                customers = result.get(

                    "customers",

                    result.get(

                        "data",

                        []

                    )

                )

            if customers:

                df = pd.DataFrame(

                    customers

                )

                st.dataframe(

                    df,

                    use_container_width=True,

                    hide_index=True

                )

            else:

                st.info(

                    "No customers found."

                )

    st.markdown("---")

    # =================================================

    if can_operate:
        # CREATE CUSTOMER

        # =================================================

        st.subheader("➕ Create Customer")

        with st.form(

            "create_customer_form"

        ):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(

                    "Name"

                )

                email = st.text_input(

                    "Email"

                )

                phone = st.text_input(

                    "Phone"

                )

            with col2:

                company = st.text_input(

                    "Company"

                )

                plan = st.selectbox(

                    "Plan",

                    [

                        "Basic",

                        "Premium"

                    ]

                )

            create_button = st.form_submit_button(

                "Create Customer"

            )

            if create_button:

                if not name.strip():

                    st.warning(

                        "Please enter customer name."

                    )

                elif not email.strip():

                    st.warning(

                        "Please enter customer email."

                    )

                else:

                    result = customer_api_post(

                        "/customers",

                        data={

                            "name": name,

                            "email": email,

                            "phone": phone,

                            "company": company,

                            "plan": plan

                        }

                    )

                    if result:

                        if result.get("success") is False:

                            st.error(

                                f"❌ {result.get('message', 'Unable to create customer.')}"

                            )

                        else:

                            st.success(

                                "✅ Customer created successfully!"

                            )

                            customer = result.get(

                                "data",

                                result.get(

                                    "customer",

                                    result

                                )

                            )

                            if isinstance(

                                customer,

                                dict

                            ):

                                if customer.get(

                                    "customer_id"

                                ) is not None:

                                    st.write(

                                        f"👤 **Customer ID:** "

                                        f"{customer['customer_id']}"

                                    )

                                if customer.get(

                                    "name"

                                ):

                                    st.write(

                                        f"**Name:** "

                                        f"{customer['name']}"

                                    )

                                if customer.get(

                                    "email"

                                ):

                                    st.write(

                                        f"**Email:** "

                                        f"{customer['email']}"

                                    )

        st.markdown("---")

        # =================================================

    if can_operate:
        # UPDATE CUSTOMER

        # =================================================

        st.subheader("✏️ Update Customer")

        customer_id = st.number_input(

            "Customer ID",

            min_value=1,

            step=1,

            key="update_customer_id"

        )

        with st.form(

            "update_customer_form"

        ):

            col1, col2 = st.columns(2)

            with col1:

                update_name = st.text_input(

                    "Name",

                    key="update_name"

                )

                update_email = st.text_input(

                    "Email",

                    key="update_email"

                )

                update_phone = st.text_input(

                    "Phone",

                    key="update_phone"

                )

            with col2:

                update_company = st.text_input(

                    "Company",

                    key="update_company"

                )

                update_plan = st.selectbox(

                    "Plan",

                    [

                        "Basic",

                        "Premium"

                    ],

                    key="update_plan"

                )

                update_status = st.selectbox(

                    "Status",

                    [

                        "Active",

                        "Inactive"

                    ],

                    key="update_status"

                )

            update_button = st.form_submit_button(

                "Update Customer"

            )

            if update_button:

                data = {

                    "name": update_name or None,

                    "email": update_email or None,

                    "phone": update_phone or None,

                    "company": update_company or None,

                    "plan": update_plan,

                    "status": update_status

                }

                result = customer_api_put(

                    f"/customers/{customer_id}",

                    data

                )

                if result:

                    if result.get("success") is False:

                        st.error(

                            f"❌ {result.get('message', 'Unable to update customer.')}"

                        )

                    else:

                        st.success(

                            "✅ Customer updated successfully!"

                        )

        st.markdown("---")

        # =================================================

    if is_admin:
        # DELETE CUSTOMER

        # =================================================

        st.subheader("🗑️ Delete Customer")

        delete_id = st.number_input(

            "Customer ID to delete",

            min_value=1,

            step=1,

            key="delete_customer_id"

        )

        if st.button(

            "Delete Customer",

            type="primary",

            key="delete_customer_button"

        ):

            result = customer_api_delete(

                f"/customers/{delete_id}"

            )

            if result:

                if result.get("success") is False:

                    st.error(

                        f"❌ {result.get('message', 'Unable to delete customer.')}"

                    )

                else:

                    st.success(

                        "✅ Customer deleted successfully!"

                    )

        st.markdown("---")

        # =================================================

    if can_operate:
        # IMPORT CUSTOMERS

        # =================================================

        st.subheader("📥 Import Customers")

        st.write(

            "Upload a CSV or Excel file to import "

            "multiple customers into the CRM."

        )

        customer_file = st.file_uploader(

            "Choose CSV or Excel file",

            type=[

                "csv",

                "xlsx"

            ],

            key="customer_import"

        )

        if customer_file:

            st.write(

                f"📄 Selected file: "

                f"**{customer_file.name}**"

            )

            if st.button(

                "Import Customers",

                type="primary",

                key="import_customer_button"

            ):

                files = {

                    "file": (

                        customer_file.name,

                        customer_file.getvalue(),

                        customer_file.type

                    )

                }

                result = customer_api_post(

                    "/customers/import",

                    files=files

                )

                if result:

                    if result.get("success"):

                        st.success(

                            result.get(

                                "message",

                                "Import completed successfully."

                            )

                        )

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric(

                            "Total Rows",

                            result.get(

                                "total_rows",

                                0

                            )

                        )

                        col2.metric(

                            "Inserted",

                            result.get(

                                "inserted",

                                0

                            )

                        )

                        col3.metric(

                            "Duplicates",

                            result.get(

                                "duplicates_in_file",

                                0

                            )

                        )

                        col4.metric(

                            "Already Existing",

                            result.get(

                                "already_existing",

                                0

                            )

                        )

                    else:

                        st.error(

                            f"❌ {result.get('message', 'Import failed.')}"

                        )

# =====================================================

# TICKETS

# =====================================================

elif page == "🎫 Tickets":

    st.title("🎫 Ticket Management")

    # =================================================

    if can_operate:
        # CREATE TICKET

        # =================================================

        st.subheader("➕ Create New Ticket")

        with st.form(

            "create_ticket_form"

        ):

            customer_id = st.number_input(

                "Customer ID",

                min_value=1,

                step=1

            )

            issue = st.text_area(

                "Issue",

                placeholder="Describe the customer's issue..."

            )

            priority = st.selectbox(

                "Priority",

                [

                    "Low",

                    "Medium",

                    "High"

                ]

            )

            create_ticket_button = st.form_submit_button(

                "Create Ticket"

            )

            if create_ticket_button:

                if not issue.strip():

                    st.warning(

                        "Please enter the ticket issue."

                    )

                else:

                    result = ticket_api_post(

                        "/tickets",

                        {

                            "customer_id": customer_id,

                            "issue": issue,

                            "priority": priority

                        }

                    )

                    if result:

                        if result.get("success") is False:

                            st.error(

                                f"❌ {result.get('message', 'Unable to create ticket.')}"

                            )

                        else:

                            st.success(

                                "✅ Ticket created successfully!"

                            )

                            if result.get(

                                "ticket_id"

                            ) is not None:

                                st.write(

                                    f"🎫 **Ticket ID:** "

                                    f"{result['ticket_id']}"

                                )

        st.divider()

        # =================================================

    # ALL TICKETS

    # =================================================

    st.subheader("📋 All Tickets")

    tickets = ticket_api_get(

        "/tickets"

    )

    if tickets:

        if (

            isinstance(

                tickets,

                dict

            )

            and tickets.get("success") is False

        ):

            st.error(

                f"❌ {tickets.get('message', 'Unable to load tickets.')}"

            )

        else:

            if isinstance(

                tickets,

                dict

            ):

                ticket_data = tickets.get(

                    "tickets",

                    tickets.get(

                        "data",

                        []

                    )

                )

            else:

                ticket_data = tickets

            if ticket_data:

                df = pd.DataFrame(

                    ticket_data

                )

                st.dataframe(

                    df,

                    use_container_width=True,

                    hide_index=True

                )

            else:

                st.info(

                    "No tickets found."

                )

    else:

        st.info(

            "No tickets available."

        )

    st.divider()

    # =================================================

    # SEARCH TICKET

    # =================================================

    st.subheader("🔎 Search Ticket")

    search_ticket_id = st.number_input(

        "Enter Ticket ID",

        min_value=1,

        step=1,

        key="search_ticket_id"

    )

    if st.button(

        "Search Ticket",

        key="search_ticket_button"

    ):

        result = ticket_api_get(

            f"/tickets/{search_ticket_id}"

        )

        if result:

            if result.get(

                "success"

            ) is False:

                st.error(

                    f"❌ {result.get('message', 'Ticket not found.')}"

                )

            else:

                st.success(

                    "✅ Ticket found"

                )

                ticket = result.get(

                    "data",

                    result.get(

                        "ticket",

                        result

                    )

                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(

                        f"🎫 **Ticket ID:** "

                        f"{ticket.get('ticket_id', '-')}"

                    )

                    st.write(

                        f"👤 **Customer ID:** "

                        f"{ticket.get('customer_id', '-')}"

                    )

                    st.write(

                        f"📌 **Status:** "

                        f"{ticket.get('status', '-')}"

                    )

                with col2:

                    st.write(

                        f"🔥 **Priority:** "

                        f"{ticket.get('priority', '-')}"

                    )

                    st.write(

                        f"📝 **Issue:** "

                        f"{ticket.get('issue', '-')}"

                    )

    st.divider()

    # =================================================

    # UPDATE TICKET

    # =================================================

    if can_operate:
        st.subheader("✏️ Update Ticket")

        update_ticket_id = st.number_input(

            "Ticket ID",

            min_value=1,

            step=1,

            key="update_ticket_id"

        )

        update_col1, update_col2 = st.columns(2)

        with update_col1:

            new_status = st.selectbox(

                "Status",

                [

                    "No Change",

                    "Open",

                    "Closed"

                ],

                key="ticket_status"

            )

        with update_col2:

            new_priority = st.selectbox(

                "Priority",

                [

                    "No Change",

                    "Low",

                    "Medium",

                    "High"

                ],

                key="ticket_priority"

            )

        new_issue = st.text_area(

            "New Issue",

            placeholder=(

                "Leave empty if you don't want "

                "to change the issue."

            ),

            key="new_ticket_issue"

        )

        if st.button(

            "Update Ticket",

            key="update_ticket_button"

        ):

            data = {}

            if new_status != "No Change":

                data["status"] = new_status

            if new_priority != "No Change":

                data["priority"] = new_priority

            if new_issue.strip():

                data["issue"] = new_issue

            if not data:

                st.warning(

                    "Please select or enter at least "

                    "one field to update."

                )

            else:

                result = ticket_api_put(

                    f"/tickets/{update_ticket_id}",

                    data

                )

                if result:

                    if result.get(

                        "success"

                    ) is False:

                        st.error(

                            f"❌ {result.get('message', 'Unable to update ticket.')}"

                        )

                    else:

                        st.success(

                            "✅ Ticket updated successfully!"

                        )

                        # Fetch latest ticket

                        updated_ticket = ticket_api_get(

                            f"/tickets/{update_ticket_id}"

                        )

                        if updated_ticket:

                            if updated_ticket.get(

                                "success"

                            ) is False:

                                st.error(

                                    f"❌ {updated_ticket.get('message', 'Unable to fetch updated ticket.')}"

                                )

                            else:

                                ticket = updated_ticket.get(

                                    "data",

                                    updated_ticket.get(

                                        "ticket",

                                        updated_ticket

                                    )

                                )

                                col1, col2 = st.columns(2)

                                with col1:

                                    st.write(

                                        f"🎫 **Ticket ID:** "

                                        f"{ticket.get('ticket_id', '-')}"

                                    )

                                    st.write(

                                        f"👤 **Customer ID:** "

                                        f"{ticket.get('customer_id', '-')}"

                                    )

                                    st.write(

                                        f"📌 **Status:** "

                                        f"{ticket.get('status', '-')}"

                                    )

                                with col2:

                                    st.write(

                                        f"🔥 **Priority:** "

                                        f"{ticket.get('priority', '-')}"

                                    )

                                    st.write(

                                        f"📝 **Issue:** "

                                        f"{ticket.get('issue', '-')}"

                                    )

## =====================================================

# ANALYTICS

# =====================================================

elif page == "📊 Analytics":

    st.title("📊 Analytics Dashboard")

    st.caption(

        "Customer Support CRM analytics and ticket insights"

    )

    # =================================================

    # FETCH ANALYTICS DATA

    # =================================================

    overview_response = api_get(

        "/analytics/ticket-overview"

    )

    status_response = api_get(

        "/analytics/ticket-status"

    )

    priority_response = api_get(

        "/analytics/ticket-priority"

    )

    high_priority_response = api_get(

        "/analytics/high-priority-open"

    )

    customer_summary_response = api_get(

        "/analytics/customer-ticket-summary"

    )

    # =================================================

    # CHECK API RESPONSE

    # =================================================

    if not overview_response:

        st.error(

            "❌ Unable to connect to Analytics API."

        )

    elif overview_response.status_code != 200:

        st.error(

            f"❌ Analytics API error: "

            f"{overview_response.text}"

        )

    else:

        overview = overview_response.json()

        # =================================================

        # KPI CARDS

        # =================================================

        st.subheader("📌 Ticket Overview")

        total_tickets = overview.get(

            "total_tickets",

            0

        )

        open_tickets = overview.get(

            "open_tickets",

            0

        )

        closed_tickets = overview.get(

            "closed_tickets",

            0

        )

        high_priority_tickets = overview.get(

            "high_priority_tickets",

            0

        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(

                "🎫 Total Tickets",

                total_tickets

            )

        with col2:

            st.metric(

                "🟢 Open Tickets",

                open_tickets

            )

        with col3:

            st.metric(

                "🔴 Closed Tickets",

                closed_tickets

            )

        with col4:

            st.metric(

                "🔥 High Priority",

                high_priority_tickets

            )

        st.divider()

        # =================================================

        # STATUS + PRIORITY

        # =================================================

        col1, col2 = st.columns(2)

        # -------------------------------------------------

        # TICKET STATUS

        # -------------------------------------------------

        with col1:

            st.subheader("🎫 Ticket Status")

            if (

                status_response

                and status_response.status_code == 200

            ):

                status_data = status_response.json()

                # API returns "summary"

                status_rows = status_data.get(

                    "summary",

                    []

                )

                if status_rows:

                    import pandas as pd

                    status_df = pd.DataFrame(

                        status_rows

                    )

                    st.bar_chart(

                        status_df.set_index(

                            "status"

                        )

                    )

                else:

                    st.info(

                        "No ticket status data available."

                    )

            else:

                st.error(

                    "Unable to load ticket status data."

                )

        # -------------------------------------------------

        # TICKET PRIORITY

        # -------------------------------------------------

        with col2:

            st.subheader("🔥 Ticket Priority")

            if (

                priority_response

                and priority_response.status_code == 200

            ):

                priority_data = priority_response.json()

                # API returns "summary"

                priority_rows = priority_data.get(

                    "summary",

                    []

                )

                if priority_rows:

                    import pandas as pd

                    priority_df = pd.DataFrame(

                        priority_rows

                    )

                    st.bar_chart(

                        priority_df.set_index(

                            "priority"

                        )

                    )

                else:

                    st.info(

                        "No ticket priority data available."

                    )

            else:

                st.error(

                    "Unable to load ticket priority data."

                )

        st.divider()

        # =================================================

        # HIGH PRIORITY OPEN TICKETS

        # =================================================

        st.subheader(

            "🔥 High Priority Open Tickets"

        )

        if (

            high_priority_response

            and high_priority_response.status_code == 200

        ):

            high_priority_data = (

                high_priority_response.json()

            )

            # API returns "tickets"

            high_priority_rows = (

                high_priority_data.get(

                    "tickets",

                    []

                )

            )

            if high_priority_rows:

                import pandas as pd

                high_priority_df = pd.DataFrame(

                    high_priority_rows

                )

                st.dataframe(

                    high_priority_df,

                    use_container_width=True,

                    hide_index=True

                )

            else:

                st.success(

                    "🎉 No high-priority open tickets."

                )

        else:

            st.error(

                "Unable to load high-priority tickets."

            )

        st.divider()

        # =================================================

        # CUSTOMER TICKET SUMMARY

        # =================================================

        st.subheader(

            "👥 Customer Ticket Summary"

        )

        if (

            customer_summary_response

            and customer_summary_response.status_code == 200

        ):

            customer_summary_data = (

                customer_summary_response.json()

            )

            # API returns "summary"

            customer_rows = (

                customer_summary_data.get(

                    "summary",

                    []

                )

            )

            if customer_rows:

                import pandas as pd

                customer_df = pd.DataFrame(

                    customer_rows

                )

                st.dataframe(

                    customer_df,

                    use_container_width=True,

                    hide_index=True

                )

            else:

                st.info(

                    "No customer ticket data available."

                )

        else:

            st.error(

                "Unable to load customer ticket summary."

            )

# =====================================================

# KNOWLEDGE BASE

# =====================================================

elif page == "📚 Knowledge Base":

    st.title("📚 Knowledge Base")

    st.write(

        "Upload PDF, TXT or DOCX documents to add "

        "them to the AI knowledge base."

    )

    st.divider()

    # =================================================

    # UPLOAD DOCUMENT

    # =================================================

    st.subheader(

        "📤 Upload Knowledge Document"

    )

    uploaded_file = st.file_uploader(

        "Choose a document",

        type=[

            "pdf",

            "txt",

            "docx"

        ],

        help=(

            "Supported formats: "

            "PDF, TXT and DOCX"

        ),

        key="knowledge_upload"

    )

    if uploaded_file is not None:

        st.write(

            f"📄 **Selected file:** "

            f"{uploaded_file.name}"

        )

        if st.button(

            "Upload Document",

            key="upload_knowledge_button"

        ):

            result = knowledge_api_upload(

                uploaded_file

            )

            if result:

                if result.get(

                    "success"

                ) is False:

                    st.error(

                        f"❌ {result.get('message', 'Knowledge upload failed.')}"

                    )

                else:

                    st.success(

                        "✅ Document uploaded successfully!"

                    )

                    if result.get(

                        "filename"

                    ):

                        st.write(

                            f"📄 **File:** "

                            f"{result['filename']}"

                        )

                    if result.get(

                        "chunks"

                    ) is not None:

                        st.write(

                            f"🧩 **Chunks indexed:** "

                            f"{result['chunks']}"

                        )

                    if result.get(

                        "message"

                    ):

                        st.write(

                            f"💬 **Message:** "

                            f"{result['message']}"

                        )


# =====================================================
# ADMIN USER MANAGEMENT
# =====================================================

elif page == "👤 User Management":
    if not is_admin:
        st.error("You do not have permission to manage users.")
        st.stop()

    st.title("👤 Admin User Management")
    st.caption("Create accounts, review users, change roles, and activate or deactivate access.")

    def user_api_error(response):
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("detail") or data.get("message") or response.text
        except ValueError:
            pass
        return response.text or f"Request failed ({response.status_code})."

    def fetch_users():
        try:
            response = requests.get(
                f"{API_URL}/admin/users", headers=auth_headers(), timeout=15
            )
            if response.status_code == 200:
                payload = response.json()
                return payload.get("users", []), None
            return [], user_api_error(response)
        except requests.exceptions.RequestException as exc:
            return [], f"Could not connect to FastAPI: {exc}"

    users, users_error = fetch_users()
    if users_error:
        st.error(f"Unable to load users: {users_error}")
        st.info("Confirm that the backend has the /admin/users endpoints and restart FastAPI.")
    else:
        total_users = len(users)
        active_users = sum(bool(user.get("is_active")) for user in users)
        inactive_users = total_users - active_users
        metric_cols = st.columns(3)
        metric_cols[0].metric("Total users", total_users)
        metric_cols[1].metric("Active users", active_users)
        metric_cols[2].metric("Inactive users", inactive_users)

        with st.expander("➕ Create a user", expanded=True):
            with st.form("admin_create_user_form", clear_on_submit=True):
                new_username = st.text_input("Username", max_chars=50)
                new_email = st.text_input("Email")
                new_password = st.text_input("Temporary password (minimum 8 characters)", type="password")
                new_role = st.selectbox("Role", ["Support Agent", "Viewer", "Admin"])
                create_submitted = st.form_submit_button("Create user", type="primary")

            if create_submitted:
                if not new_username.strip() or not new_email.strip() or not new_password:
                    st.warning("Complete all fields before creating the user.")
                elif len(new_username.strip()) < 3:
                    st.warning("Username must contain at least 3 characters.")
                elif len(new_password) < 8:
                    st.warning("Password must contain at least 8 characters.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/admin/users",
                            headers=auth_headers(),
                            json={
                                "username": new_username.strip(),
                                "email": new_email.strip(),
                                "password": new_password,
                                "role": new_role,
                            },
                            timeout=15,
                        )
                        if response.status_code in (200, 201):
                            st.success("User created successfully.")
                            st.rerun()
                        else:
                            st.error(user_api_error(response))
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not connect to FastAPI: {exc}")

        st.subheader("👥 Existing users")
        if users:
            display_users = [
                {
                    "User ID": user.get("user_id"),
                    "Username": user.get("username"),
                    "Email": user.get("email"),
                    "Role": user.get("role"),
                    "Status": "Active" if user.get("is_active") else "Inactive",
                    "Created at": user.get("created_at"),
                }
                for user in users
            ]
            st.dataframe(display_users, use_container_width=True, hide_index=True)

            selectable_users = {
                f"{user.get('username')} (ID {user.get('user_id')})": user
                for user in users
            }
            selected_label = st.selectbox(
                "Select a user to manage", list(selectable_users.keys()), key="admin_selected_user"
            )
            selected_user = selectable_users[selected_label]
            st.caption(
                f"Selected: {selected_user.get('username')} · "
                f"Current role: {selected_user.get('role')} · "
                f"Status: {'Active' if selected_user.get('is_active') else 'Inactive'}"
            )

            left, right = st.columns(2)
            with left:
                with st.form("admin_change_role_form"):
                    role_options = ["Admin", "Support Agent", "Viewer"]
                    role_index = role_options.index(selected_user.get("role")) if selected_user.get("role") in role_options else 0
                    chosen_role = st.selectbox("New role", role_options, index=role_index)
                    role_submitted = st.form_submit_button("Update role")
                if role_submitted:
                    try:
                        response = requests.patch(
                            f"{API_URL}/admin/users/{selected_user.get('user_id')}/role",
                            headers=auth_headers(),
                            json={"role": chosen_role},
                            timeout=15,
                        )
                        if response.status_code == 200:
                            st.success("Role updated successfully.")
                            st.rerun()
                        else:
                            st.error(user_api_error(response))
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not connect to FastAPI: {exc}")

            with right:
                currently_active = bool(selected_user.get("is_active"))
                action_label = "Deactivate account" if currently_active else "Activate account"
                confirm_status = st.checkbox(
                    f"Confirm: {action_label.lower()} for {selected_user.get('username')}",
                    key=f"confirm_status_{selected_user.get('user_id')}_{currently_active}",
                )
                if st.button(action_label, type="primary" if currently_active else "secondary", disabled=not confirm_status):
                    try:
                        response = requests.patch(
                            f"{API_URL}/admin/users/{selected_user.get('user_id')}/status",
                            headers=auth_headers(),
                            json={"is_active": not currently_active},
                            timeout=15,
                        )
                        if response.status_code == 200:
                            st.success("Account status updated successfully.")
                            st.rerun()
                        else:
                            st.error(user_api_error(response))
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not connect to FastAPI: {exc}")
        else:
            st.info("No user accounts were returned by the API.")

