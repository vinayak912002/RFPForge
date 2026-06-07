import streamlit as st
import requests
import datetime

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

# ============================
# HELPER FUNCTIONS
# ============================

def validate_response(response, operation_name: str):
    """
    Validate API response and handle errors gracefully.
    Returns: (success: bool, data: dict or None, error_msg: str or None)
    """
    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_data = response.json()
            if "detail" in error_data:
                error_detail = str(error_data["detail"])
        except:
            pass
        return False, None, f"{operation_name} failed: {response.status_code} - {error_detail}"
    
    try:
        data = response.json()
        return True, data, None
    except:
        return False, None, f"{operation_name} returned invalid JSON"


def load_questions_from_backend(rfp_id: str):
    """
    Fetch questions from backend and populate session state.
    """
    try:
        res = requests.get(f"{API_URL}/rfp/{rfp_id}/questions")
        success, data, error = validate_response(res, "Fetch questions")
        
        if not success:
            st.error(f"❌ {error}")
            return
        
        # Clear existing questions
        st.session_state.questions = {}
        
        # Populate from backend
        if "questions" in data:
            for q in data["questions"]:
                q_id = q.get("question_id")
                if q_id:
                    st.session_state.questions[q_id] = {
                        "text": q.get("question_text", ""),
                        "answer": None
                    }
        
        if st.session_state.questions:
            st.success(f"✅ Loaded {len(st.session_state.questions)} questions from backend")
        else:
            st.info("No questions found in this RFP")
            
    except Exception as e:
        st.error(f"❌ Error loading questions: {e}")


# ============================
# SIDEBAR - CREATE RFP & FILE UPLOAD
# ============================

st.sidebar.markdown("### 🔌 Backend Test")

if st.sidebar.button("Test Backend Connection"):
    try:
        res = requests.get(f"{API_URL}/")
        st.sidebar.success("✅ Connected")
        st.sidebar.json(res.json())
    except Exception as e:
        st.sidebar.error(f"❌ Failed: {e}")

# ----
# CREATE RFP
# ----

with st.sidebar:
    st.title("🚀 RFPilot")

    col1, col2 = st.columns(2)
    
    with col1:
        client = st.text_input("Client Name")
    with col2:
        deadline = st.date_input("Deadline", value=datetime.date.today())

    # File upload in sidebar
    uploaded_file = st.file_uploader("Upload RFP file (PDF)", type=["pdf"])

    if st.button("Create RFP"):
        if not client:
            st.error("Please enter a client name")
        else:
            try:
                # Prepare form data
                form_data = {
                    "client_name": client,
                    "deadline": str(deadline)
                }
                
                # If file is uploaded, include it in the POST request
                if uploaded_file:
                    files = {"rfp_file": uploaded_file}
                    res = requests.post(
                        f"{API_URL}/rfp",
                        data=form_data,
                        files=files
                    )
                else:
                    res = requests.post(
                        f"{API_URL}/rfp",
                        data=form_data
                    )
                
                success, data, error = validate_response(res, "Create RFP")
                
                if not success:
                    st.error(f"❌ {error}")
                else:
                    st.session_state.rfp_id = data.get("rfp_id") or data.get("id")
                    st.session_state.questions = {}
                    
                    st.success("✅ RFP Created!")
                    st.json(data)
                    
                    # If questions were extracted from file, load them
                    if uploaded_file:
                        st.info("Loading extracted questions...")
                        load_questions_from_backend(st.session_state.rfp_id)

            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.button("Reset RFP"):
        st.session_state.rfp_id = None
        st.session_state.questions = {}
        st.success("✅ Reset complete")

# ============================
# MAIN UI
# ============================

st.title("AI-Powered RFP Automation")

rfp_id = st.session_state.rfp_id

if not rfp_id:
    st.info("👈 Create an RFP first using the sidebar")
    st.stop()

st.success(f"Active RFP ID: {rfp_id}")

# ============================
# REFRESH QUESTIONS
# ============================

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh Questions from Backend"):
        load_questions_from_backend(rfp_id)
        st.rerun()

with col2:
    if st.button("ℹ️ RFP Info"):
        try:
            res = requests.get(f"{API_URL}/rfp/{rfp_id}")
            success, data, error = validate_response(res, "Get RFP info")
            if success:
                st.json(data)
            else:
                st.error(f"❌ {error}")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ============================
# MANUAL QUESTION INPUT
# ============================

st.subheader("✍️ Add Question Manually")

col1, col2 = st.columns([4, 1])

with col1:
    question_text = st.text_input("Enter a question")

with col2:
    add_btn = st.button("Add", use_container_width=True)

if add_btn:
    if not question_text.strip():
        st.error("Please enter a question")
    else:
        try:
            res = requests.post(
                f"{API_URL}/rfp/{rfp_id}/question",
                json={"question_text": question_text}
            )

            success, data, error = validate_response(res, "Add question")
            
            if not success:
                st.error(f"❌ {error}")
            else:
                q_id = data.get("question_id")
                if not q_id:
                    st.error("❌ Server response missing question_id")
                else:
                    st.session_state.questions[q_id] = {
                        "text": question_text,
                        "answer": None
                    }
                    st.success("✅ Question added!")
                    st.json(data)
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")

# ============================
# DISPLAY & MANAGE QUESTIONS
# ============================

st.header("📋 Questions")

if not st.session_state.questions:
    st.info("No questions yet. Upload an RFP or add a question manually.")
else:
    st.info(f"Total questions: {len(st.session_state.questions)}")

for q_id, q_data in list(st.session_state.questions.items()):
    if q_id is None:
        st.warning("⚠️ Skipping question with invalid ID (None)")
        continue

    with st.expander(f"❓ {q_data['text']}"):

        # -------- GENERATE --------
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ Generate Response", key=f"gen_{q_id}"):
                try:
                    res = requests.post(
                        f"{API_URL}/rfp/{rfp_id}/question/{q_id}/draft"
                    )

                    success, data, error = validate_response(res, "Generate draft")
                    
                    if not success:
                        st.error(f"❌ {error}")
                    else:
                        answer_text = data.get("answer_text", "")
                        if not answer_text:
                            st.error("❌ Server returned empty answer")
                        else:
                            st.session_state.questions[q_id]["answer"] = answer_text
                            st.success("✅ Response generated!")
                            st.json(data)
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

        with col2:
            if st.button("🔄 Regenerate", key=f"regen_{q_id}"):
                try:
                    res = requests.post(
                        f"{API_URL}/rfp/{rfp_id}/question/{q_id}/regenerate"
                    )

                    success, data, error = validate_response(res, "Regenerate response")
                    
                    if not success:
                        st.error(f"❌ {error}")
                    else:
                        answer_text = data.get("answer_text", "")
                        if not answer_text:
                            st.error("❌ Server returned empty answer")
                        else:
                            st.session_state.questions[q_id]["answer"] = answer_text
                            st.success("✅ Response regenerated!")
                            st.json(data)
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

        with col3:
            if st.button("🗑️ Delete", key=f"del_{q_id}"):
                del st.session_state.questions[q_id]
                st.success("✅ Question removed")
                st.rerun()

        # -------- DISPLAY ANSWER --------
        if q_data["answer"]:
            st.markdown("### 📝 Answer:")
            st.text_area(
                "Answer",
                value=q_data["answer"],
                height=200,
                key=f"ans_{q_id}",
                disabled=True
            )
        else:
            st.info("No response generated yet")