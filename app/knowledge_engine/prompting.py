# draft prompts
def build_draft_prompt(question: str, context_chunks: list):
    context = "\n\n".join(context_chunks)

    prompt = f"""
You are answering an RFP question.

Answer the question ONLY using the provided context.
If the answer is not present in the context, respond with: NOT FOUND.

Context:
{context}

Question:
{question}

Answer:
"""
    return prompt