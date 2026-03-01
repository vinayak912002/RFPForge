## Loading 

### Document Loader Utility

The Document Loader Utility is a modular ingestion component designed for use in Retrieval-Augmented Generation (RAG) systems. It provides structured loading of supported document formats and converts them into LangChain-compatible Document objects.

This module is part of the knowledge ingestion layer in RFPForge and handles file-type detection, loader selection, error handling, and structured output generation.

### Purpose

Before embeddings and retrieval can occur in a RAG pipeline, raw documents must be parsed into structured text objects. This utility automates that process by:

- Detecting file type automatically
- Selecting the appropriate loader
- Handling errors gracefully
- Returning standardized Document objects
- Supporting both single-file and directory ingestion

It ensures clean separation between file parsing and downstream embedding logic.

### Supported File Types

The module currently supports:
- PDF (.pdf) using PyPDFLoader
- DOCX (.docx) using Docx2txtLoader
- DOC (.doc) using UnstructuredWordDocumentLoader

Loader selection is handled dynamically through a factory-style function.

### Architecture Overview

The design follows clean engineering principles:
- Single Responsibility Principle
- Factory Pattern for loader selection
- Clear separation of concerns
- Structured logging
- Explicit error handling

Core responsibilities are separated into:

- get_loader() – Selects the correct loader
- load_document() – Loads a single file
- load_directory() – Loads all supported files in a folder
This structure makes the module easy to extend and test.




## Chunking

We are handling the chunking of the loaded RFPs in this step the output of this step is small peices of the RFP document so that each chunk is semantically isolated.  
We follow the following sub-steps in order to perform this step:-  
1. Noise cleaning
2. Structure heuristic calculation
3. Adaptive Chunking mode selection
4. Chunk generation
5. Metadata Enrichment 

### 1. Noise Cleaning

Remove:  
- Repeated headers
- Page numbers
- Watermarks
- unnecessary text such as "For official use only"

### 2. Calculation of SStructural Heuristic

We detect common Structures using general Regex rules:  
- **Clause Pattern** - `\b\d{1,2}\.\d{1,2}(\.\d{1,2})*\b` - These represent hierarchical references inside formal documents like '.1', '.2'
- **Uppercase Header Pattern** - `r"\n[A-Z][A-Z\s]{4,}\n"` - Section titles written in ALL CAPITAL LETTERS like GLOSSARY, SCOPE OF WORK, ELIGIBILITY CRITERIA
- **Colon Header Pattern** - `(?m)^(?:[ \t]*)(([A-Z][A-Z\s]{3,}))\s*$` - Headers that end with a colon
- **Bullet Pattern** - `r"\n\s*[-•]\s+"` - Bullet points inside a document

we are using the number of these structural points that we can find to calculate the heuristic.  

### 3. Adaptive Chunking mode selection

There are three modes of chunking that we have implemented based on how structured the document in question is.  
-  Structured Chunking - Splits text based on explicit document structure such as headings, sections, clauses, or numbering hierarchies.
- Semi-Structured Chunking: Splits text using partial structural cues like formatting patterns, capitalization, delimiters, or layout hints when full hierarchy is not available.
- Unstructured Chunking: Splits text purely by length or token limits without relying on any document structure.

This adaptive approach ensures optimal chunking behavior across highly structured legal RFPs as well as loosely formatted documents.

### 4. Chunk Generation

Once the chunking mode is selected, chunks are generated as follows:

- In Structured Mode, text is segmented at detected section headers and clause boundaries. Each chunk typically represents a logical unit such as a section, subsection, or clause group.
- In Semi-Structured Mode, chunk boundaries are inferred using detected patterns such as uppercase headers, bullet clusters, and spacing heuristics, while also respecting maximum token thresholds.
- In Unstructured Mode, text is split into fixed-size token windows with optional overlap to preserve contextual continuity.

Additional rules applied during chunk generation:

- Maintain semantic integrity (avoid cutting mid-sentence when possible)
- Enforce minimum and maximum token thresholds
- Allow controlled overlap between chunks (for retrieval continuity)
- Preserve original ordering

The result is a list of logically coherent and retrieval-ready text chunks.

### 5. Metadata Enrichment

Each generated chunk is enriched with metadata to support traceability, retrieval accuracy, and downstream processing.

- `source` – Original document name
- `page_number` - Page from which chunk originated
- `chunk_id` - Unique identifier (UUID)
- `section_title` - Detected parent section (if available)
- `clauses` - Extracted clause references
- `structure_detected` - Boolean indicating structural presence
- `structure_score` - Heuristic score for the document

This metadata enables:  
- Hierarchical retrieval
- Clause-based search
- Section-aware question answering
- Document traceability
- Fine-grained filtering

### Final Output
The final output of the chunking pipeline is:
- A list of semantically coherent text chunks
- Each chunk enriched with contextual metadata
- A structure-aware segmentation optimized for downstream retrieval and AI processing

## Embedding

### Embedding Utility

The Embedding Utility is responsible for converting semantically coherent document chunks into dense vector representations suitable for similarity search and retrieval in a Retrieval-Augmented Generation (RAG) pipeline.

This module operates downstream of the chunking stage and transforms enriched `Document` objects into normalized embeddings while preserving metadata and generating operational metrics.

### Purpose

After documents are parsed and chunked, embeddings are required to enable semantic search, clustering, and retrieval. This utility automates that process by:

* Loading and configuring a SentenceTransformer model
* Generating embeddings in efficient batches
* Normalizing vectors for cosine similarity
* Caching embeddings to avoid redundant computation
* Preserving metadata alignment
* Producing embedding-level metrics

This ensures consistent, reproducible embeddings and efficient reuse across ingestion runs.

### Model Selection

The utility uses SentenceTransformers and defaults to:

* **Model**: `BAAI/bge-large-en-v1.5`
* **Embedding Dimension**: 1024
* **Similarity Metric**: Cosine (via normalized embeddings)

The model is automatically loaded onto GPU if available, otherwise CPU is used.

### Architecture Overview

The design emphasizes performance, determinism, and traceability:

* Deterministic hashing for cache keys
* On-disk embedding cache
* Batch-based encoding
* Separation of model loading, caching, and embedding logic
* Metric generation for observability

Core responsibilities are separated into:

* `load_embedding_model()` – Loads and configures the embedding model
* `embed_documents()` – Generates embeddings for a list of chunked documents
* Cache helpers – Handle embedding persistence and retrieval

### Embedding Workflow

The embedding pipeline follows these steps:

1. **Model Initialization**
   The SentenceTransformer model is loaded with automatic device selection (CUDA if available).

2. **Cache Key Generation**
   Each chunk is hashed using a deterministic SHA-256 key derived from:

   * Model name
   * Chunk text content

3. **Cache Lookup**
   If an embedding already exists on disk for the given key, it is reused instead of recomputed.

4. **Batch Embedding**
   Chunks without cached vectors are encoded in configurable batches. Embeddings are L2-normalized to ensure compatibility with cosine similarity search.

5. **Cache Persistence**
   Newly generated embeddings are serialized and stored for future reuse.

6. **Metric Collection**
   Embedding statistics are computed to support monitoring and validation.

### Input

The embedding utility expects:

* A list of LangChain-compatible `Document` objects
* Each document must contain:

  * `page_content` – The chunk text
  * `metadata` – Enriched metadata from the chunking stage

### Output

The output of the embedding step is a structured dictionary:

* `embeddings` – List of embedding vectors (`List[List[float]]`)
* `metadatas` – Corresponding metadata objects for each chunk
* `metrics` – Embedding-level statistics

### Metrics Generated

The following metrics are calculated automatically:

* `total_chunks` – Number of embedded chunks
* `avg_tokens_per_chunk` – Average token count per chunk
* `min_tokens` / `max_tokens` – Token range across chunks
* `embedding_dim` – Dimensionality of the embedding vectors
* `avg_vector_norm` – Mean L2 norm of embeddings (post-normalization)
* `cache_hit_ratio` – Percentage of chunks served from cache

These metrics provide insight into chunk quality, embedding consistency, and cache efficiency.

### Caching Strategy

To optimize performance and reduce cost:

* Embeddings are cached on disk using deterministic content-based hashes
* Cache keys are stable across runs for identical text and model combinations
* Only uncached chunks are re-embedded

This makes the embedding stage idempotent and scalable for large RFP corpora.

### Final Output

The final output of the embedding pipeline is:

* A vector representation for each document chunk
* Metadata preserved for downstream indexing and retrieval
* Operational metrics for observability

These embeddings are ready to be ingested into a vector store or retrieval index for semantic search and RAG-based question answering.




## Retrieval & Reranking Module

### Overview

The `RetrievalService` implements a production-grade semantic retrieval pipeline with optional cross-encoder reranking. It is designed to be scalable, testable, and production-safe.

The pipeline performs:

1. Query embedding
2. Vector similarity search
3. Score threshold filtering
4. Optional cross-encoder reranking (BGE)
5. Structured response formatting

---

### Architecture Flow

User Query  
↓  
Embedding Service  
↓  
Vector Store (Similarity Search)  
↓  
Score Threshold Filtering  
↓  
(Optional) Cross-Encoder Reranking  
↓  
Final Ranked Results  

---

### Key Features

- Semantic search using embeddings
- Optional BGE cross-encoder reranking
- Metadata-based filtering (doc_type, section, recency)
- Score threshold control
- Structured logging with latency tracking
- Dependency injection for test isolation
- Thread-safe lazy model loading
- Graceful fallback if reranker fails

---

### Configuration

```python
RetrievalService(
    embedding_service,
    vector_store_service,
    score_threshold=0.0,
    rerank=True,
    rerank_top_k=5,
    max_latency_ms=2000,
    reranker_cls=None,  # Inject custom reranker (used in tests)
)
