from app.llm.client import generate_response
from app.knowledge_engine.prompting import build_rfp_prompt


question = "What encryption standard do you use?"

context = [
    "We use AES-256 encryption for data at rest.",
    "TLS 1.3 is used for secure communication."
]


prompt = build_rfp_prompt(question, context)

response = generate_response(prompt)

print("\n===== RESPONSE =====\n")
print(response)