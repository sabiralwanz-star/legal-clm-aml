import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

APP_TITLE = "Legal CLM + AML Compliance System"
DB_PATH = Path("clm_aml_database.db")

CONTRACT_STATUSES = [
    "Business Request", "Legal Intake", "Risk Analysis", "Drafting", "Negotiation",
    "Final Legal Approval", "Management Approval", "Client Signature Pending",
    "Client Signed", "CEO Signature Pending", "Fully Executed", "Final Legal Check",
    "Stored in Repository", "Active Contract", "Renewal Monitoring", "Closed / Expired / Terminated"
]

AML_STATUSES = [
    "Client Request", "Initial AML Screening", "Sumsub Link Sent", "KYC/KYB Pending",
    "Verification Under Review", "Additional Documents Required", "EDD / Risk Review",
    "AML Matrix Review", "Compliance Approval", "Contract Preparation", "Client Signature Pending",
    "CEO Signature Pending", "Agreement Fully Executed", "Final Legal Check", "Service Release Approval",
    "Service Onboarded", "Transaction Monitoring", "Ongoing EDD / RFI", "Periodic Review", "Closed / Offboarded", "Rejected"
]

RISK_LEVELS = ["Low", "Medium", "High", "Escalated", "Rejected"]
KYC_OPTIONS = ["Not Started", "Pending", "Submitted", "Verified", "Rejected", "Additional Documents Required"]
CHECK_OPTIONS = ["Not Started", "Clear", "Potential Match", "Escalated", "Rejected"]
YES_NO = ["No", "Yes"]
SERVICES = [
    "Crypto IBAN", "Fiat IBAN", "Crypto Payment Processing", "Fiat Payment Processing",
    "Remittance", "Foreign Exchange", "Virtual Currency Service", "Other"
]
CONTRACT_TYPES = [
    "NDA", "Client Services Agreement", "Crypto IBAN Agreement", "Fiat IBAN Agreement",
    "Payment Processing Agreement", "Virtual Currency Services Agreement", "Amendment", "Annexure", "Addendum", "Other"
]


def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            client_name TEXT NOT NULL,
            client_type TEXT,
            country TEXT,
            registered_address TEXT,
            website TEXT,
            ubo_name TEXT,
            ubo_count INTEGER,
            service_requested TEXT,
            business_owner TEXT,
            legal_owner TEXT,
            compliance_owner TEXT,
            risk_rating TEXT,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT UNIQUE,
            client_id TEXT,
            client_name TEXT,
            contract_type TEXT,
            status TEXT,
            legal_owner TEXT,
            business_owner TEXT,
            contract_value REAL,
            currency TEXT,
            governing_law TEXT,
            jurisdiction TEXT,
            risk_rating TEXT,
            signature_status TEXT,
            approval_status TEXT,
            draft_word_link TEXT,
            final_pdf_link TEXT,
            client_signed_link TEXT,
            ceo_signed_link TEXT,
            fully_executed_link TEXT,
            annexure_link TEXT,
            amendment_link TEXT,
            execution_date TEXT,
            effective_date TEXT,
            expiry_date TEXT,
            renewal_date TEXT,
            notice_period INTEGER,
            repository_location TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS aml (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE,
            client_id TEXT,
            client_name TEXT,
            status TEXT,
            sumsub_link TEXT,
            sumsub_link_sent TEXT,
            kyc_status TEXT,
            kyb_status TEXT,
            additional_documents_required TEXT,
            missing_documents TEXT,
            aml_matrix_completed TEXT,
            screening_status TEXT,
            sanctions_check TEXT,
            pep_check TEXT,
            adverse_media_check TEXT,
            edd_required TEXT,
            rfi_required TEXT,
            transaction_monitoring_status TEXT,
            next_periodic_review_date TEXT,
            last_review_date TEXT,
            compliance_owner TEXT,
            service_release_status TEXT,
            final_legal_check TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linked_to TEXT,
            linked_id TEXT,
            client_name TEXT,
            document_type TEXT,
            document_name TEXT,
            document_link TEXT,
            version TEXT,
            notes TEXT,
            uploaded_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_title TEXT,
            linked_to TEXT,
            linked_id TEXT,
            client_name TEXT,
            owner TEXT,
            due_date TEXT,
            priority TEXT,
            status TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def load_df(table):
    conn = connect()
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


def insert_record(table, data):
    conn = connect()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


def update_record(table, record_id, data):
    conn = connect()
    assignments = ", ".join([f"{k}=?" for k in data.keys()])
    conn.execute(f"UPDATE {table} SET {assignments} WHERE id=?", list(data.values()) + [record_id])
    conn.commit()
    conn.close()


def generate_id(prefix, existing_count):
    return f"{prefix}-{existing_count + 1:04d}"


def safe_date(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def sidebar():
    st.sidebar.title("Legal CLM + AML")
    return st.sidebar.radio(
        "Go to",
        [
            "Dashboard", "Client Master", "Contract CLM", "AML / KYC / KYB",
            "Risk & Service Release", "Documents", "Tasks & Reminders", "Reports Export", "Setup Guide"
        ]
    )


def dashboard():
    st.title("Dashboard")
    clients = load_df("clients")
    contracts = load_df("contracts")
    aml = load_df("aml")
    tasks = load_df("tasks")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clients", len(clients))
    col2.metric("Contracts", len(contracts))
    col3.metric("AML Cases", len(aml))
    overdue = 0
    if not tasks.empty:
        overdue = len(tasks[(tasks["status"] != "Completed") & (pd.to_datetime(tasks["due_date"], errors="coerce").dt.date < date.today())])
    col4.metric("Overdue Tasks", overdue)

    st.subheader("Important Alerts")
    alerts = []
    if not contracts.empty:
        alerts.append(("Client Signature Pending", len(contracts[contracts["status"] == "Client Signature Pending"])))
        alerts.append(("CEO Signature Pending", len(contracts[contracts["status"] == "CEO Signature Pending"])))
        alerts.append(("High / Escalated Contract Risk", len(contracts[contracts["risk_rating"].isin(["High", "Escalated"])])))
        expiring = contracts[pd.to_datetime(contracts["expiry_date"], errors="coerce").dt.date.between(date.today(), date.today() + timedelta(days=90), inclusive="both")]
        alerts.append(("Contracts Expiring in 90 Days", len(expiring)))
    if not aml.empty:
        alerts.append(("KYC Pending", len(aml[aml["kyc_status"].isin(["Pending", "Not Started", "Additional Documents Required"])])))
        alerts.append(("KYB Pending", len(aml[aml["kyb_status"].isin(["Pending", "Not Started", "Additional Documents Required"])])))
        alerts.append(("Service Release Pending", len(aml[aml["status"] == "Service Release Approval"])))
        alerts.append(("EDD / RFI Required", len(aml[(aml["edd_required"] == "Yes") | (aml["rfi_required"] == "Yes")])) )
    if alerts:
        st.dataframe(pd.DataFrame(alerts, columns=["Alert", "Count"]), use_container_width=True)
    else:
        st.info("No records yet. Start by adding a client.")

    st.subheader("Recent Contracts")
    st.dataframe(contracts.tail(10), use_container_width=True)
    st.subheader("Recent AML Cases")
    st.dataframe(aml.tail(10), use_container_width=True)


def client_master():
    st.title("Client Master")
    clients = load_df("clients")
    with st.expander("Add New Client", expanded=True):
        with st.form("client_form"):
            c1, c2 = st.columns(2)
            client_name = c1.text_input("Client Name *")
            client_type = c2.selectbox("Client Type", ["Company", "Individual", "Partnership", "Trust", "Other"])
            country = c1.text_input("Country of Incorporation")
            website = c2.text_input("Website")
            registered_address = st.text_area("Registered Address")
            ubo_name = c1.text_input("UBO Name")
            ubo_count = c2.number_input("UBO Count", min_value=0, step=1)
            service_requested = st.multiselect("Service Requested", SERVICES)
            business_owner = c1.text_input("Business Owner")
            legal_owner = c2.text_input("Legal Owner")
            compliance_owner = c1.text_input("Compliance Owner")
            risk_rating = c2.selectbox("Client Risk Rating", RISK_LEVELS)
            submitted = st.form_submit_button("Save Client")
            if submitted:
                if not client_name:
                    st.error("Client Name is required.")
                else:
                    insert_record("clients", {
                        "client_id": generate_id("CL", len(clients)),
                        "client_name": client_name,
                        "client_type": client_type,
                        "country": country,
                        "registered_address": registered_address,
                        "website": website,
                        "ubo_name": ubo_name,
                        "ubo_count": int(ubo_count),
                        "service_requested": ", ".join(service_requested),
                        "business_owner": business_owner,
                        "legal_owner": legal_owner,
                        "compliance_owner": compliance_owner,
                        "risk_rating": risk_rating,
                        "created_at": datetime.now().isoformat(timespec="seconds")
                    })
                    st.success("Client saved. Refresh page if table does not update immediately.")
    st.subheader("All Clients")
    st.dataframe(load_df("clients"), use_container_width=True)


def contract_clm():
    st.title("Contract CLM")
    clients = load_df("clients")
    contracts = load_df("contracts")
    client_options = [""] + clients["client_name"].tolist() if not clients.empty else [""]

    with st.expander("Add New Contract", expanded=True):
        with st.form("contract_form"):
            c1, c2 = st.columns(2)
            client_name = c1.selectbox("Client Name", client_options)
            client_id = ""
            if client_name and not clients.empty:
                row = clients[clients["client_name"] == client_name].iloc[0]
                client_id = row["client_id"]
            contract_type = c2.selectbox("Contract Type", CONTRACT_TYPES)
            status = c1.selectbox("Workflow Status", CONTRACT_STATUSES)
            risk_rating = c2.selectbox("Risk Rating", RISK_LEVELS)
            legal_owner = c1.text_input("Legal Owner")
            business_owner = c2.text_input("Business Owner")
            contract_value = c1.number_input("Contract Value", min_value=0.0, step=100.0)
            currency = c2.text_input("Currency", value="USD")
            governing_law = c1.text_input("Governing Law")
            jurisdiction = c2.text_input("Jurisdiction")
            signature_status = c1.selectbox("Signature Status", ["Not Sent", "Sent to Client", "Client Signature Pending", "Client Signed", "Sent to CEO", "CEO Signature Pending", "Fully Executed"])
            approval_status = c2.selectbox("Approval Status", ["Not Started", "Legal Approved", "Compliance Approved", "Management Approved", "Rejected"])
            st.markdown("#### Document Links")
            draft_word_link = st.text_input("Draft Word Link")
            final_pdf_link = st.text_input("Final PDF Link")
            client_signed_link = st.text_input("Client Signed Agreement Link")
            ceo_signed_link = st.text_input("CEO Signed Agreement Link")
            fully_executed_link = st.text_input("Fully Executed Agreement Link")
            annexure_link = st.text_input("Annexure Link")
            amendment_link = st.text_input("Amendment Link")
            st.markdown("#### Dates")
            d1, d2, d3, d4 = st.columns(4)
            execution_date = d1.date_input("Execution Date", value=None)
            effective_date = d2.date_input("Effective Date", value=None)
            expiry_date = d3.date_input("Expiry Date", value=None)
            renewal_date = d4.date_input("Renewal Date", value=None)
            notice_period = st.number_input("Notice Period Days", min_value=0, step=1)
            repository_location = st.text_input("Repository Location")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save Contract")
            if submitted:
                insert_record("contracts", {
                    "contract_id": generate_id("CON", len(contracts)),
                    "client_id": client_id,
                    "client_name": client_name,
                    "contract_type": contract_type,
                    "status": status,
                    "legal_owner": legal_owner,
                    "business_owner": business_owner,
                    "contract_value": float(contract_value),
                    "currency": currency,
                    "governing_law": governing_law,
                    "jurisdiction": jurisdiction,
                    "risk_rating": risk_rating,
                    "signature_status": signature_status,
                    "approval_status": approval_status,
                    "draft_word_link": draft_word_link,
                    "final_pdf_link": final_pdf_link,
                    "client_signed_link": client_signed_link,
                    "ceo_signed_link": ceo_signed_link,
                    "fully_executed_link": fully_executed_link,
                    "annexure_link": annexure_link,
                    "amendment_link": amendment_link,
                    "execution_date": str(execution_date) if execution_date else "",
                    "effective_date": str(effective_date) if effective_date else "",
                    "expiry_date": str(expiry_date) if expiry_date else "",
                    "renewal_date": str(renewal_date) if renewal_date else "",
                    "notice_period": int(notice_period),
                    "repository_location": repository_location,
                    "notes": notes,
                    "created_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("Contract saved.")
    st.subheader("All Contracts")
    st.dataframe(load_df("contracts"), use_container_width=True)


def aml_page():
    st.title("AML / KYC / KYB")
    clients = load_df("clients")
    aml_cases = load_df("aml")
    client_options = [""] + clients["client_name"].tolist() if not clients.empty else [""]
    with st.expander("Add New AML Case", expanded=True):
        with st.form("aml_form"):
            c1, c2 = st.columns(2)
            client_name = c1.selectbox("Client Name", client_options)
            client_id = ""
            if client_name and not clients.empty:
                row = clients[clients["client_name"] == client_name].iloc[0]
                client_id = row["client_id"]
            status = c2.selectbox("AML Workflow Status", AML_STATUSES)
            sumsub_link = st.text_input("Sumsub Link")
            sumsub_link_sent = c1.selectbox("Sumsub Link Sent", YES_NO)
            kyc_status = c2.selectbox("KYC Status", KYC_OPTIONS)
            kyb_status = c1.selectbox("KYB Status", KYC_OPTIONS)
            additional_documents_required = c2.selectbox("Additional Documents Required", YES_NO)
            missing_documents = st.text_area("Missing Documents")
            aml_matrix_completed = c1.selectbox("AML Matrix Completed", YES_NO)
            screening_status = c2.selectbox("Screening Status", CHECK_OPTIONS)
            sanctions_check = c1.selectbox("Sanctions Check", CHECK_OPTIONS)
            pep_check = c2.selectbox("PEP Check", CHECK_OPTIONS)
            adverse_media_check = c1.selectbox("Adverse Media Check", CHECK_OPTIONS)
            edd_required = c2.selectbox("EDD Required", YES_NO)
            rfi_required = c1.selectbox("RFI Required", YES_NO)
            transaction_monitoring_status = c2.selectbox("Transaction Monitoring Status", ["Not Started", "Active", "Alert Raised", "RFI Sent", "EDD Required", "Cleared", "Suspended", "Closed"])
            compliance_owner = c1.text_input("Compliance Owner")
            service_release_status = c2.selectbox("Service Release Status", ["Not Started", "Pending Legal Check", "Pending Compliance Check", "Approved for Release", "Service Onboarded", "Hold", "Rejected"])
            final_legal_check = c1.selectbox("Final Legal Check Completed", YES_NO)
            d1, d2 = st.columns(2)
            next_periodic_review_date = d1.date_input("Next Periodic Review Date", value=None)
            last_review_date = d2.date_input("Last Review Date", value=None)
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save AML Case")
            if submitted:
                insert_record("aml", {
                    "case_id": generate_id("AML", len(aml_cases)),
                    "client_id": client_id,
                    "client_name": client_name,
                    "status": status,
                    "sumsub_link": sumsub_link,
                    "sumsub_link_sent": sumsub_link_sent,
                    "kyc_status": kyc_status,
                    "kyb_status": kyb_status,
                    "additional_documents_required": additional_documents_required,
                    "missing_documents": missing_documents,
                    "aml_matrix_completed": aml_matrix_completed,
                    "screening_status": screening_status,
                    "sanctions_check": sanctions_check,
                    "pep_check": pep_check,
                    "adverse_media_check": adverse_media_check,
                    "edd_required": edd_required,
                    "rfi_required": rfi_required,
                    "transaction_monitoring_status": transaction_monitoring_status,
                    "next_periodic_review_date": str(next_periodic_review_date) if next_periodic_review_date else "",
                    "last_review_date": str(last_review_date) if last_review_date else "",
                    "compliance_owner": compliance_owner,
                    "service_release_status": service_release_status,
                    "final_legal_check": final_legal_check,
                    "notes": notes,
                    "created_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("AML case saved.")
    st.subheader("All AML Cases")
    st.dataframe(load_df("aml"), use_container_width=True)


def risk_release():
    st.title("Risk & Service Release")
    aml = load_df("aml")
    contracts = load_df("contracts")
    st.subheader("Service Release Control")
    if aml.empty:
        st.info("No AML cases yet.")
    else:
        release = aml.copy()
        release["Release Allowed"] = release.apply(lambda r: "Yes" if (
            r["kyc_status"] == "Verified" and
            r["kyb_status"] == "Verified" and
            r["aml_matrix_completed"] == "Yes" and
            r["final_legal_check"] == "Yes" and
            r["service_release_status"] in ["Approved for Release", "Service Onboarded"]
        ) else "No", axis=1)
        st.dataframe(release[["case_id", "client_name", "status", "kyc_status", "kyb_status", "aml_matrix_completed", "final_legal_check", "service_release_status", "Release Allowed"]], use_container_width=True)
    st.subheader("High Risk Contracts")
    if not contracts.empty:
        st.dataframe(contracts[contracts["risk_rating"].isin(["High", "Escalated", "Rejected"])], use_container_width=True)


def documents_page():
    st.title("Document Repository")
    docs = load_df("documents")
    with st.expander("Add Document Link / Record", expanded=True):
        with st.form("doc_form"):
            c1, c2 = st.columns(2)
            linked_to = c1.selectbox("Linked To", ["Client", "Contract", "AML Case", "Amendment", "Annexure", "RFI", "EDD"])
            linked_id = c2.text_input("Linked ID / Reference")
            client_name = c1.text_input("Client Name")
            document_type = c2.selectbox("Document Type", ["Draft", "Redline", "Final PDF", "Client Signed", "CEO Signed", "Fully Executed", "KYC", "KYB", "UBO", "AML Matrix", "EDD", "RFI", "Annexure", "Amendment", "Other"])
            document_name = st.text_input("Document Name")
            document_link = st.text_input("Document Link")
            version = c1.text_input("Version", value="v1")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save Document Record")
            if submitted:
                insert_record("documents", {
                    "linked_to": linked_to,
                    "linked_id": linked_id,
                    "client_name": client_name,
                    "document_type": document_type,
                    "document_name": document_name,
                    "document_link": document_link,
                    "version": version,
                    "notes": notes,
                    "uploaded_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("Document record saved.")
    st.dataframe(load_df("documents"), use_container_width=True)


def tasks_page():
    st.title("Tasks & Reminders")
    tasks = load_df("tasks")
    with st.expander("Add Task / Reminder", expanded=True):
        with st.form("task_form"):
            c1, c2 = st.columns(2)
            task_title = st.text_input("Task Title")
            linked_to = c1.selectbox("Linked To", ["Client", "Contract", "AML Case", "Renewal", "Signature", "RFI", "EDD", "Other"])
            linked_id = c2.text_input("Linked ID / Reference")
            client_name = c1.text_input("Client Name")
            owner = c2.text_input("Owner")
            due_date = c1.date_input("Due Date")
            priority = c2.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            status = c1.selectbox("Status", ["Open", "In Progress", "Waiting", "Completed", "Cancelled"])
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save Task")
            if submitted:
                insert_record("tasks", {
                    "task_title": task_title,
                    "linked_to": linked_to,
                    "linked_id": linked_id,
                    "client_name": client_name,
                    "owner": owner,
                    "due_date": str(due_date),
                    "priority": priority,
                    "status": status,
                    "notes": notes,
                    "created_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("Task saved.")
    st.subheader("Open Tasks")
    df = load_df("tasks")
    if not df.empty:
        st.dataframe(df[df["status"] != "Completed"], use_container_width=True)
    else:
        st.info("No tasks yet.")


def reports_page():
    st.title("Reports Export")
    for table in ["clients", "contracts", "aml", "documents", "tasks"]:
        df = load_df(table)
        st.subheader(table.capitalize())
        st.dataframe(df, use_container_width=True)
        st.download_button(
            label=f"Download {table}.csv",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{table}.csv",
            mime="text/csv"
        )


def setup_guide():
    st.title("Setup Guide")
    st.markdown('''
### How to use this system

1. First create all clients in **Client Master**.
2. For every contract, go to **Contract CLM** and create a contract record.
3. For AML/KYC/KYB onboarding, go to **AML / KYC / KYB** and create an AML case.
4. Add document links in **Documents**.
5. Add follow-up reminders in **Tasks & Reminders**.
6. Check the **Dashboard** every morning.
7. Export reports from **Reports Export**.

### Rule to follow

- One client = one Client Master record.
- One agreement = one Contract CLM record.
- One onboarding = one AML case.
- One amendment or annexure = separate document record and task.
- One pending action = one task/reminder.

### Service release rule

Do not mark service as onboarded unless:

- KYC Status = Verified
- KYB Status = Verified
- AML Matrix Completed = Yes
- Final Legal Check Completed = Yes
- Service Release Status = Approved for Release or Service Onboarded

### Document naming format

ClientName_DocumentType_Version_Date

Example:
ABC_Ltd_ClientAgreement_Draft_v1_13-05-2026
''')


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    page = sidebar()
    if page == "Dashboard":
        dashboard()
    elif page == "Client Master":
        client_master()
    elif page == "Contract CLM":
        contract_clm()
    elif page == "AML / KYC / KYB":
        aml_page()
    elif page == "Risk & Service Release":
        risk_release()
    elif page == "Documents":
        documents_page()
    elif page == "Tasks & Reminders":
        tasks_page()
    elif page == "Reports Export":
        reports_page()
    elif page == "Setup Guide":
        setup_guide()

if __name__ == "__main__":
    main()
