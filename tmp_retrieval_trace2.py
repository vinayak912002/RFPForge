from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore
from app.knowledge_engine.retrieval import RetrievalService

questions = [
    "What is the recommended use of a response workbook for RFPs?",
    "If not using a response workbook, what information should proposers submit in its place?"
]
emb = EmbeddingService()
vs = VectorStore()
service = RetrievalService(embedding_service=emb, vector_store_service=vs, rerank=False)

for question in questions:
    print('QUESTION:', question)
    print('collection health:', vs.health_check(vs.collection_name))
    print('search results:')
    results = service.search(query=question, top_k=5)
    for i, r in enumerate(results, 1):
        print('--- result', i, 'score={:.4f}'.format(r['score']), 'metadata=', r['metadata'])
        print(r['content'][:300].replace('\n', ' '))
        print()
    print('==========\n')
