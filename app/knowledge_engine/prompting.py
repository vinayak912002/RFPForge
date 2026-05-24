# draft prompts

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