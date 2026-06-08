from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore
from app.knowledge_engine.retrieval import RetrievalService

question = "If not using a response workbook, what information should proposers submit in its place?"
emb = EmbeddingService()
vs = VectorStore()
service = RetrievalService(embedding_service=emb, vector_store_service=vs, rerank=False)

print('collection health:')
print(vs.health_check(vs.collection_name))
print('\nsearch results:')
results = service.search(query=question, top_k=10)
for i, r in enumerate(results, 1):
    print('--- result', i, 'score={:.4f}'.format(r['score']), 'metadata=', r['metadata'])
    print(r['content'][:400].replace('\n', ' '))
    print()
