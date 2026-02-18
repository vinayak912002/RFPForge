  # Streamlit demo
import streamlit as st
import datetime
import uuid
import pandas as pd
from typing import List
from dataclasses import dataclass
from docx import Document
from PyPDF2 import PdfReader

# =============================================================================
# SAFE SESSION STATE HANDLING
# =============================================================================
def get_rfp_state():
    if "rfp_data" not in st.session_state:
        st.session_state["rfp_data"] = {
            "rfp_sessions": {},
            "current_rfp_id": None,
            "edit_mode": None
        }
    return st.session_state["rfp_data"]

rfp_data = get_rfp_state()

st.set_page_config(page_title="AI RFP Tool", layout="wide")

# =============================================================================
# DATA CLASSES
# =============================================================================
@dataclass
class Source:
    doc_type: str
    filename: str
    section: str
    snippet: str

@dataclass
class Draft:
    content: str
    sources: List[Source]
    version: int

# =============================================================================
# MOCK AI GENERATOR
# =============================================================================
def generate_draft(question: str, version: int = 1):
    sources = [
        Source(
            "knowledge",
            "Security_Policy_v2.pdf",
            "Encryption",
            "AES-256 encryption for data at rest"
        )
    ]

    answer = f"""
### Response to: "{question}"

We use AES-256 encryption for all stored data.
Backups are encrypted using secure key management systems.
"""

    return Draft(content=answer, sources=sources, version=version)

# =============================================================================
# QUESTION EXTRACTION
# =============================================================================
def extract_questions_from_text(text):
    lines = text.split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        if len(line) > 20 and (
            line.endswith("?")
            or line.lower().startswith(("describe", "what", "how", "provide", "explain"))
        ):
            questions.append(line)
    return questions

def parse_docx(file):
    doc = Document(file)
    full_text = "\n".join([p.text for p in doc.paragraphs])
    return extract_questions_from_text(full_text)

def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return extract_questions_from_text(text)

def parse_excel(file):
    df = pd.read_excel(file)
    questions = []
    for col in df.columns:
        for val in df[col]:
            if isinstance(val, str) and len(val) > 20:
                questions.append(val)
    return questions

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.title("🏢 RFP Workspaces")

    st.markdown("### ➕ Create New RFP")

    client = st.text_input("Client Name")
    deadline = st.date_input("Deadline", value=datetime.date.today())

    if st.button("CREATE RFP", type="primary"):
        if client.strip():
            rfp_id = str(uuid.uuid4())[:8].upper()

            rfp_data["rfp_sessions"][rfp_id] = {
                "client": client,
                "deadline": str(deadline),
                "questions": {}
            }

            rfp_data["current_rfp_id"] = rfp_id
            st.success("RFP Created")
        else:
            st.warning("Enter client name")

    st.markdown("### 📋 Existing RFPs")

    for r_id, info in rfp_data["rfp_sessions"].items():
        if st.button(info["client"], key=f"select_{r_id}"):
            rfp_data["current_rfp_id"] = r_id

# =============================================================================
# MAIN
# =============================================================================
st.title("✨ AI-Powered RFP Response Tool")

rfp_id = rfp_data.get("current_rfp_id")

if not rfp_id:
    st.info("👈 Create or select an RFP from sidebar")
else:
    rfp = rfp_data["rfp_sessions"][rfp_id]

    col1, col2 = st.columns(2)
    col1.metric("Client", rfp["client"])
    col2.metric("Deadline", rfp["deadline"])

    st.markdown("---")

    # ================= Upload =================
    st.header("📤 Upload RFP Document")

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX or Excel",
        type=["pdf", "docx", "xlsx"]
    )

    if uploaded_file:
        st.info("Extracting questions...")

        questions = []

        if uploaded_file.type == "application/pdf":
            questions = parse_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            questions = parse_docx(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            questions = parse_excel(uploaded_file)

        if questions:
            for q in questions:
                q_id = str(uuid.uuid4())[:8].upper()
                rfp["questions"][q_id] = {
                    "question": q,
                    "drafts": []
                }
            st.success(f"{len(questions)} questions extracted!")
        else:
            st.warning("No questions detected.")

    st.markdown("---")

    # ================= Questions =================
    st.header("📋 Questions")

    for q_id, q_data in rfp["questions"].items():

        with st.expander(q_data["question"][:100]):

            # Generate draft
            if not q_data["drafts"]:
                if st.button("Generate Draft", key=f"gen_{q_id}"):
                    draft = generate_draft(q_data["question"], 1)
                    q_data["drafts"].append(draft)

            # If draft exists
            if q_data["drafts"]:

                latest = q_data["drafts"][-1]

                st.markdown(f"### Draft v{latest.version}")
                st.markdown(latest.content)

                col1, col2 = st.columns(2)

                # Edit
                if col1.button("✏️ Edit", key=f"edit_{q_id}"):
                    rfp_data["edit_mode"] = q_id

                # Regenerate
                if col2.button("🔄 Regenerate", key=f"regen_{q_id}"):
                    new_version = latest.version + 1
                    new_draft = generate_draft(q_data["question"], new_version)
                    q_data["drafts"].append(new_draft)

                # Edit mode
                if rfp_data.get("edit_mode") == q_id:
                    edited_text = st.text_area(
                        "Edit Draft",
                        value=latest.content,
                        key=f"edit_text_{q_id}"
                    )

                    save_col, cancel_col = st.columns(2)

                    if save_col.button("💾 Save", key=f"save_{q_id}"):
                        latest.content = edited_text
                        rfp_data["edit_mode"] = None

                    if cancel_col.button("❌ Cancel", key=f"cancel_{q_id}"):
                        rfp_data["edit_mode"] = None

                # Sources
                st.markdown("#### 📚 Sources")
                for src in latest.sources:
                    st.markdown(f"• {src.filename} — {src.snippet}")

    st.markdown("---")
    st.caption("✅ Upload • Auto Extract • Generate • Edit • Regenerate • Fully Stable")



