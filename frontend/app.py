import streamlit as st
import datetime
import uuid
import pandas as pd
import time
from typing import List
from dataclasses import dataclass
from docx import Document
from pypdf import PdfReader

# -----------------------------
# PAGE CONFIG (MUST BE FIRST)
# -----------------------------
st.set_page_config(page_title="RFPilot", layout="wide")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "rfp_data" not in st.session_state:
    st.session_state["rfp_data"] = {
        "rfp_sessions": {},
        "current_rfp_id": None,
    }

rfp_data = st.session_state["rfp_data"]

# -----------------------------
# DATA CLASSES
# -----------------------------
@dataclass
class Source:
    doc_type: str
    filename: str
    section: str
    snippet: str
    full_chunk: str

@dataclass
class Draft:
    content: str
    sources: List[Source]
    version: int

# -----------------------------
# STREAMING GENERATOR
# -----------------------------
def stream_generate(question):
    full_text = f"""
### Response to: "{question}"

We use AES-256 encryption for all stored data.
Backups are encrypted using secure key management systems.
TLS 1.3 is enforced in transit.
SOC2 Type II compliant.
"""

    placeholder = st.empty()
    streamed_text = ""

    for char in full_text:
        streamed_text += char
        placeholder.markdown(streamed_text)
        time.sleep(0.005)

    return streamed_text


def generate_sources():
    return [
        Source(
            "knowledge",
            "Security_Policy_v2.pdf",
            "Encryption",
            "AES-256 encryption for data at rest",
            "Full chunk: We use AES-256 encryption with CMK management and key rotation."
        ),
        Source(
            "knowledge",
            "Compliance_Doc.pdf",
            "Certifications",
            "SOC2 Type II Certified",
            "Full chunk: Our organization maintains SOC2 Type II certification with annual audits."
        )
    ]

# -----------------------------
# FILE PARSING
# -----------------------------
def extract_questions(text):
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
    text = "\n".join([p.text for p in doc.paragraphs])
    return extract_questions(text)


def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return extract_questions(text)


def parse_excel(file):
    df = pd.read_excel(file)
    questions = []
    for col in df.columns:
        for val in df[col]:
            if isinstance(val, str) and len(val) > 20:
                questions.append(val)
    return questions

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("🚀 RFPilot")

    client = st.text_input("Client Name")
    deadline = st.date_input("Deadline", value=datetime.date.today())

    if st.button("Create RFP", type="primary"):
        if client:
            rfp_id = str(uuid.uuid4())[:8]
            rfp_data["rfp_sessions"][rfp_id] = {
                "client": client,
                "deadline": str(deadline),
                "questions": {}
            }
            rfp_data["current_rfp_id"] = rfp_id
            st.success("RFP Created")

    st.markdown("### Existing RFPs")
    for r_id, info in rfp_data["rfp_sessions"].items():
        if st.button(info["client"], key=r_id):
            rfp_data["current_rfp_id"] = r_id

# -----------------------------
# MAIN
# -----------------------------
st.title("AI-Powered RFP Automation")

rfp_id = rfp_data.get("current_rfp_id")

if not rfp_id:
    st.info("Create or select an RFP from sidebar.")
else:
    rfp = rfp_data["rfp_sessions"][rfp_id]

    col1, col2 = st.columns(2)
    col1.metric("Client", rfp["client"])
    col2.metric("Deadline", rfp["deadline"])

    st.markdown("---")

    # FILE UPLOAD
    uploaded_file = st.file_uploader("Upload RFP (PDF, DOCX, XLSX)")

    if uploaded_file:
        questions = []

        if uploaded_file.name.endswith(".pdf"):
            questions = parse_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            questions = parse_docx(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            questions = parse_excel(uploaded_file)

        for q in questions:
            q_id = str(uuid.uuid4())[:8]
            rfp["questions"][q_id] = {"question": q, "drafts": []}

        st.success(f"{len(questions)} questions extracted.")

    st.markdown("---")
    st.header("Questions")

    for q_id, q_data in rfp["questions"].items():

        with st.expander(q_data["question"][:120]):

            # Generate draft
            if not q_data["drafts"]:
                if st.button("Generate Response", key=f"gen_{q_id}"):
                    content = stream_generate(q_data["question"])
                    draft = Draft(
                        content=content,
                        sources=generate_sources(),
                        version=1
                    )
                    q_data["drafts"].append(draft)

            # If draft exists
            if q_data["drafts"]:
                latest = q_data["drafts"][-1]

                edited = st.text_area(
                    "Draft",
                    value=latest.content,
                    height=250,
                    key=f"text_{q_id}"
                )

                col1, col2 = st.columns(2)

                if col1.button("💾 Save", key=f"save_{q_id}"):
                    latest.content = edited
                    st.success("Saved successfully.")

                if col2.button("🔄 Regenerate", key=f"regen_{q_id}"):
                    content = stream_generate(q_data["question"])
                    new_draft = Draft(
                        content=content,
                        sources=generate_sources(),
                        version=latest.version + 1
                    )
                    q_data["drafts"].append(new_draft)

                # -----------------------------
                # SOURCES PANEL (NO NESTING)
                # -----------------------------
                st.markdown("### 📚 Sources")

                for i, src in enumerate(latest.sources):

                    st.markdown(f"**{src.filename} – {src.section}**")
                    st.write(src.snippet)

                    if st.button("View Full Chunk", key=f"chunk_{q_id}_{i}"):
                        st.info(src.full_chunk)

                    st.markdown("---")

    st.markdown("---")
    st.caption("Streaming • Editable • Versioned • Expandable • Stable")
