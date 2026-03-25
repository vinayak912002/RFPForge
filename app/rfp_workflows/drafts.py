 # draft versioning & edits
from sqlalchemy.orm import Session
from app.rfp_workflows.models import Question
from app.rfp_workflows.drafts import add_draft, get_latest_draft
from app.knowledge_engine.prompting import build_draft_prompt


def generate_first_draft(db: Session, question_id: str, retrieval_service, llm_service):
    
    # 1. Get question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise ValueError("Question not found")

    question_text = question.question_text

    # 2. Retrieve context
    results = retrieval_service.search(query=question_text, top_k=10)

    context_chunks = []
    sources = []

    if results:
        for r in results:
            context_chunks.append(r["content"])
            sources.append(r["metadata"])

    # 3. Build prompt
    prompt = build_draft_prompt(question_text, context_chunks)

    # 4. Generate answer
    answer = llm_service.generate(prompt)

    # 5. Versioning
    latest = get_latest_draft(db, question_id)
    if latest:
        version = latest.version + 1
    else:
        version = 1

    # 6. Store draft
    draft = add_draft(
        db=db,
        question_id=question_id,
        answer_text=answer,
        version=version,
        sources_json=sources
    )

    return draft