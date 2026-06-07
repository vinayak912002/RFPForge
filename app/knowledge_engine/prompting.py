# draft prompts


def build_question_extraction_prompt(document_text: str) -> str:
    return f"""
You are an expert document analyst.

Extract all actionable questions, response requirements, information requests, missing-information items, and implied clarifications from the document text.

The document may be an RFP, questionnaire, spreadsheet, meeting note, scope document, email, checklist, or any other business document. Questions may not be clearly written with a question mark.

Extract items written as:
- direct questions
- implied questions
- unclear or missing information that needs clarification
- action items that require an answer
- requirements that require a response
- instructions
- checklist items
- evaluation criteria
- "Describe...", "Provide...", "Explain...", "Confirm...", "Submit...", "Clarify..."
- numbered or bulleted response prompts
- table rows or fields asking for information

Return ONLY valid JSON in this exact format:

{{
  "questions": [
    "clear standalone question or response requirement 1",
    "clear standalone question or response requirement 2"
  ]
}}

Rules:
- Preserve the meaning of the original document text.
- Convert fragments into clear standalone questions or response requirements when needed.
- Return complete, self-contained items. Do not end items with ellipses or leave them unfinished.
- If the text is a requirement or instruction, rewrite it as a clear standalone response requirement.
- If the text is a question, preserve it as a clear question.
- Do not include section headings, labels, page footers, headers, or boilerplate unless they require a response.
- Do not include duplicates.
- Do not invent facts.
- Prefer one concise item per requirement.
- If no questions are found, return {{"questions": []}}.

DOCUMENT TEXT:
{document_text}
"""


def build_rfp_prompt(question: str, context: list[str], user_style: str = None):
    context_text = "\n\n".join(context)

    prompt = f"""
You are an expert RFP assistant.

Answer the question ONLY using the provided context.
If the answer is not present, respond with "NOT FOUND".

CONTEXT:
{context_text}

QUESTION:
{question}

Provide a clear and professional answer.
"""

    if user_style:
        prompt += f"\n\nStyle:\n{user_style}"

    return prompt


# compatibility with old code
def build_draft_prompt(question: str, context_chunks: list):
    return build_rfp_prompt(question, context_chunks)
