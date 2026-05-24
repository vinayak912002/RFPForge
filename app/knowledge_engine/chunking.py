"""
steps in chunking:

1. Document type detection
2. Seection Extraction
3. Semantic Chunking
4. Metadata Enrichment
"""

import re
import uuid
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.logging import get_logger

logger = get_logger("knowledge.chunking")

# ==========================================================
# CONFIGURATION
# ==========================================================

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100

# ==========================================================
# PUBLIC ENTRY FUNCTION
# ==========================================================

def chunk_documents(
        documents: List[Document],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Document]:
    logger.info(f"Starting chunking process for {len(documents)} documents.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    all_chunks = []

    for i, doc in enumerate(documents):
        cleaned_text = clean_text(doc.page_content)
        structure_score = compute_structure_score(cleaned_text)
        logger.info(f"Processing doc {i+1}/{len(documents)} | Structure Score: {structure_score}")

        if structure_score > 20:
            logger.info(f"Doc {i+1}: Selecting STRUCTURED chunking mode.")
            chunks = structured_chunking(
                cleaned_text,
                doc.metadata,
                text_splitter
            )

        elif structure_score > 8:
            logger.info(f"Doc {i+1}: Selecting SEMI-STRUCTURED chunking mode.")
            chunks = semi_structured_chunking(
                cleaned_text,
                doc.metadata,
                text_splitter,
            )
        
        else:
            logger.info(f"Doc {i+1}: Selecting UNSTRUCTURED chunking mode.")
            chunks = unstructured_chunking(
                cleaned_text,
                doc.metadata,
                text_splitter
            )
        
        logger.info(f"Doc {i+1}: Generated {len(chunks)} chunks.")
        all_chunks.extend(chunks)

    logger.info(f"Total chunks generated: {len(all_chunks)}")
    return all_chunks


# ==========================================================
# CLEANING
# ==========================================================

def clean_text(text: str) -> str:
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line_lower = line.lower().strip()

        if not line_lower:
            continue
        if "for official use only" in line_lower:
            continue
        if re.match(r"^page\s*\d+", line_lower):
            continue
        if re.match(r"^\d+\s*$", line_lower):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

# ==========================================================
# STRUCTURE CONFIDENCE SCORE CALCULATION
# ==========================================================

def compute_structure_score(text: str) -> int:

    clause_matches = len(re.findall(r"\b\d{1,2}\.\d{1,2}(?:\.\d{1,2})*\b", text))
    uppercase_headers = len(re.findall(r"\n[A-Z][A-Z\s]{4,}\n", text))
    bullet_points = len(re.findall(r"\n\s*[-•]\s+", text))
    colon_headers = len(re.findall(r"(?m)^(?:[ \t]*)(([A-Z][A-Z\s]{3,}))\s*$", text))

    score = (
        clause_matches
        + (uppercase_headers * 3)
        + bullet_points
        + (colon_headers * 2)
    )

    return score


# ==========================================================
# STRUCTURED CHUNKING
# ==========================================================

def structured_chunking(text, metadata, text_splitter):
    """
    Used for strongly structured RFPs (legal/government style).
    Splits by headers first, then clause boundaries,
    then applies semantic chunking inside each clause block.
    """

    sections = split_by_headers(text)
    chunked_docs = []

    clause_pattern = r"\n\d+\.\d+(?:\.\d+)*[^\n]*"

    for section_title, section_content in sections:

        # Split by clause anchors
        clause_splits = re.split(clause_pattern, section_content)

        if len(clause_splits) <= 1:
            clause_splits = [section_content]

        for clause_block in clause_splits:
            sub_chunks = text_splitter.split_text(clause_block)

            for chunk in sub_chunks:
                enriched_metadata = build_metadata(
                    metadata,
                    section_title,
                    chunk,
                )

                chunked_docs.append(
                    Document(
                        page_content=chunk,
                        metadata=enriched_metadata,
                    )
                )

    return chunked_docs


# ==========================================================
# SEMI STRUCTURED CHUNKING
# ==========================================================


def semi_structured_chunking(text, metadata, text_splitter):
    """
    Used for moderately structured RFPs.
    Splits by paragraph blocks and preserves bullet lists.
    """

    paragraphs = re.split(r"\n\n+", text)
    chunked_docs = []

    for paragraph in paragraphs:

        if not paragraph.strip():
            continue

        sub_chunks = text_splitter.split_text(paragraph)

        for chunk in sub_chunks:
            enriched_metadata = build_metadata(
                metadata,
                section_title=None,
                content=chunk,
            )

            chunked_docs.append(
                Document(
                    page_content=chunk,
                    metadata=enriched_metadata,
                )
            )

    return chunked_docs


# ==========================================================
# UNSTRUCTURED CHUNKING
# ==========================================================


def unstructured_chunking(text, metadata, _):
    """
    Used for weakly structured or messy documents.
    Pure semantic chunking with higher overlap.
    """

    semantic_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,  # Larger overlap because structure is weak
        separators=[". ", " ", ""],
    )

    chunks = semantic_splitter.split_text(text)
    chunked_docs = []

    for chunk in chunks:
        enriched_metadata = build_metadata(
            metadata,
            section_title=None,
            content=chunk,
        )

        chunked_docs.append(
            Document(
                page_content=chunk,
                metadata=enriched_metadata,
            )
        )

    return chunked_docs

# ==========================================================
# HEADER SPLITTING
# ==========================================================

def split_by_headers(text):

    header_pattern = r"\n([A-Z][A-Z\s]{4,})\n"
    splits = re.split(header_pattern, text)

    if len(splits) <= 1:
        return [("FULL_DOCUMENT", text)]

    sections = []

    for i in range(1, len(splits), 2):
        title = splits[i].strip()
        content = splits[i + 1]
        sections.append((title, content))

    return sections

# ==========================================================
# METADATA ENRICHMENT
# ==========================================================

def build_metadata(base_metadata, section_title, content):

    clause_numbers = re.findall(r"\b\d+\.\d+(?:\.\d+)*\b", content)

    metadata={
        **base_metadata,
        "chunk_id": str(uuid.uuid4()),
        "structure_detected": section_title is not None
    }
    if section_title:
        metadata["section_title"] = section_title
    
    if clause_numbers:
        # ChromaDB metadata must be strings, numbers, or booleans (no lists)
        metadata["clauses"] = ", ".join([str(c) for c in clause_numbers if c])
    
    return metadata
    # return {
    #     **base_metadata,
    #     "chunk_id": str(uuid.uuid4()),
    #     "section_title": section_title,
    #     "clauses": clause_numbers,
    #     "structure_detected": section_title is not None,
    # }