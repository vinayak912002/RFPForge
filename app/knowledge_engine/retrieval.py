# top-k + reranking 
query ="Here will be the users query"
search_results=vectorestore.similarity_search(query,k=2)
print(f"\nTop 2 most relevant chunks for the query:'{query}'\n")
for i, result in enumerate(search_results,1):
    print(f"Result {i}:")
    print(f"Source: {result.metadata.get('source','unknown')}")
    print(f"Content: {result.page_content}")
    print()