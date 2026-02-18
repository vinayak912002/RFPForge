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