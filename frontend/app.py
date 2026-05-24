import streamlit as st
import requests
import datetime
from pypdf import PdfReader

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(page_title="RFPilot", layout="wide")
API_URL = "http://127.0.0.1:8000"

# -----------------------------
# SESSION STATE
# -----------------------------

if "rfp_id" not in st.session_state:
    st.session_state.rfp_id = None
if "questions" not in st.session_state:
    st.session_state.questions = {}

# -----------------------------
# 🔌 BACKEND CONNECTION TEST
# -----------------------------

st.sidebar.markdown("### 🔌 Backend Test")

if st.sidebar.button("Test Backend Connection"):
    try:
        res = requests.get(f"{API_URL}/")
        st.sidebar.success("✅ Connected")
        st.sidebar.json(res.json())
    except Exception as e:
        st.sidebar.error(f"❌ Failed: {e}")

# -----------------------------
# SIDEBAR - CREATE RFP
# -----------------------------

with st.sidebar:
    st.title("🚀 RFPilot")

    client = st.text_input("Client Name")
    deadline = st.date_input("Deadline", value=datetime.date.today())

    if st.button("Create RFP"):
        if client:
            try:
                res = requests.post(
                    f"{API_URL}/rfp",
                    data={
                        "client_name": client,
                        "deadline": str(deadline)
                    }
                )
                data = res.json()

                st.session_state.rfp_id = data.get("rfp_id") or data.get("id")
                st.session_state.questions = {}

                st.success("RFP Created!")
                st.json(data)

            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("Reset RFP"):
        st.session_state.rfp_id = None
        st.session_state.questions = {}

# -----------------------------
# MAIN UI
# -----------------------------

st.title("AI-Powered RFP Automation")

rfp_id = st.session_state.rfp_id

if not rfp_id:
    st.info("Create an RFP first")
    st.stop()

st.success(f"Active RFP ID: {rfp_id}")

# -----------------------------
# 📄 FILE UPLOAD + EXTRACTION
# -----------------------------

st.subheader("📄 Upload RFP (PDF)")

uploaded_file = st.file_uploader("Upload RFP file", type=["pdf"])

def extract_questions_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    lines = text.split("\n")
    questions = []

    for line in lines:
        line = line.strip()
        if len(line) > 20 and "?" in line:
            questions.append(line)

    return questions

if uploaded_file:
    st.success("File uploaded!")

    if st.button("Extract Questions from File"):
        questions = extract_questions_from_pdf(uploaded_file)

        if not questions:
            st.warning("No questions detected")
        else:
            st.write("Extracted Questions:", questions)

        for q in questions:
            try:
                res = requests.post(
                    f"{API_URL}/rfp/{rfp_id}/question",
                    json={"question_text": q}
                )

                data = res.json()
                q_id = data.get("question_id") or data.get("id")

                st.session_state.questions[q_id] = {
                    "text": q,
                    "answer": None
                }

            except Exception as e:
                st.error(f"Error adding question: {e}")

        st.success("Questions added to backend!")

# -----------------------------
# MANUAL QUESTION INPUT
# -----------------------------

st.subheader("✍️ Add Question Manually")

question_text = st.text_input("Enter a question")

if st.button("Add Question"):
    try:
        res = requests.post(
            f"{API_URL}/rfp/{rfp_id}/question",
            json={"question_text": question_text}
        )

        data = res.json()
        q_id = data.get("question_id") or data.get("id")

        st.session_state.questions[q_id] = {
            "text": question_text,
            "answer": None
        }

        st.success("Question added!")
        st.json(data)

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------
# SHOW QUESTIONS
# -----------------------------

st.header("Questions")

for q_id, q_data in st.session_state.questions.items():

    with st.expander(q_data["text"]):

        # -------- GENERATE --------
        if st.button("Generate Response", key=f"gen_{q_id}"):
            try:
                res = requests.post(
                    f"{API_URL}/rfp/{rfp_id}/question/{q_id}/draft"
                )

                data = res.json()
                st.session_state.questions[q_id]["answer"] = data.get("answer_text", "No response")

                st.json(data)

            except Exception as e:
                st.error(f"Error: {e}")

        # -------- DISPLAY --------
        if q_data["answer"]:
            st.text_area(
                "Answer",
                value=q_data["answer"],
                height=200,
                key=f"ans_{q_id}"
            )

        # -------- REGENERATE --------
        if st.button("Regenerate", key=f"regen_{q_id}"):
            try:
                res = requests.post(
                    f"{API_URL}/question/{q_id}/regenerate"
                )

                data = res.json()
                st.session_state.questions[q_id]["answer"] = data.get("answer_text", "No response")

                st.json(data)

            except Exception as e:
                st.error(f"Error: {e}")