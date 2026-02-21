"""
Document Loader Utility

Supports:
- PDF (.pdf)
- DOCX (.docx)
- DOC (.doc)

Provides:
- Single file loading
- Directory loading
- Error handling and logging
"""

import os
import logging
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document



# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ----------------------------
# Loader Selection
# ----------------------------
def get_loader(file_path: str):
    """
    Returns appropriate LangChain loader based on file extension.

    Args:
        file_path (str): Path to the document.

    Returns:
        Loader instance.

    Raises:
        FileNotFoundError
        ValueError
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(file_path)

    elif ext == ".docx":
        return Docx2txtLoader(file_path)

    elif ext == ".doc":
        return UnstructuredWordDocumentLoader(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ----------------------------
# Single File Loader
# ----------------------------
def load_document(file_path: str) -> List[Document]:
    """
    Loads a single document file.

    Args:
        file_path (str): Path to file.

    Returns:
        List[Document]
    """

    logging.info(f"Loading document: {file_path}")

    try:
        loader = get_loader(file_path)
        documents = loader.load()
        logging.info(f"Loaded {len(documents)} document(s)")
        return documents

    except Exception as e:
        logging.error(f"Error loading document: {e}")
        raise RuntimeError(f"Failed to load document: {e}")


# ----------------------------
# Directory Loader
# ----------------------------
def load_directory(folder_path: str) -> List[Document]:
    """
    Loads all supported documents from a folder.

    Args:
        folder_path (str): Path to folder.

    Returns:
        List[Document]
    """

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Invalid directory: {folder_path}")

    all_documents = []

    logging.info(f"Loading documents from directory: {folder_path}")

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            docs = load_document(file_path)
            all_documents.extend(docs)
        except ValueError:
            logging.warning(f"Skipping unsupported file: {filename}")
        except Exception as e:
            logging.warning(f"Skipping file due to error: {filename} | {e}")

    logging.info(f"Total documents loaded: {len(all_documents)}")
    return all_documents

docs =load_document("E:\\vinayak\\RFPForge\\data\\knowledge_docs\\RFP_MAPP10022014.pdf")
print(docs[10])  