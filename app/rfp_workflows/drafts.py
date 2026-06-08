 # draft versioning & edits
import uuid
from sqlalchemy.orm import Session
from app.rfp_workflows.models import Draft, Question
from app.rfp_workflows.sessions import add_draft, get_latest_draft
from app.knowledge_engine.prompting import build_draft_prompt
from app.utils.logging import get_logger

logger = get_logger("workflow.drafts")

def generate_first_draft(db: Session, question_id: str, retrieval_service, llm_service):
    
    # 1. Get question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        logger.error(f"Draft generation failed: Question ID {question_id} not found.")
        raise ValueError("Question not found")

    question_text = question.question_text
    display_text = question_text if len(question_text) <= 120 else question_text[:120] + "..."
    logger.info(f"Generating draft for question: '{display_text}'")

    # 2. Retrieve context
    logger.info("Step 1: Retrieving relevant context from vector store...")
    results = retrieval_service.search(query=question_text, top_k=10)

    context_chunks = []
    sources = []

    if results:
        logger.info(f"Step 2: Found {len(results)} relevant context chunks.")
        for r in results:
            context_chunks.append(r["content"])
            sources.append(r["metadata"])
    else:
        logger.warning("Step 2: No relevant context found in knowledge base.")

    # 3. Build prompt
    prompt = build_draft_prompt(question_text, context_chunks)

    # 4. Generate answer
    logger.info("Step 3: Sending prompt to LLM...")
    answer = llm_service.generate(prompt)
    logger.info("Step 4: LLM response received.")

    # 5. Versioning
    latest = get_latest_draft(db, question_id)
    if latest:
        version = latest.version + 1
    else:
        version = 1
    logger.info(f"Step 5: Creating draft version {version}")

    # 6. Store draft
    draft = add_draft(
        db=db,
        question_id=question_id,
        answer_text=answer,
        version=version,
        sources_json=sources
    )

    logger.info("Draft generation workflow completed.")
    return draft
