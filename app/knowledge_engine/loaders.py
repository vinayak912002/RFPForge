# PDF/DOCX loaders 
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_loader(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".docx":
        return Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file type")
    
loader = get_loader("E:\\vinayak\\RFPForge\\data\\knowledge_docs\\RFP_MAPP10022014.pdf")
documents = loader.load()
print(f"Loaded {len(documents)} documents.")
print(documents[10].page_content[:500])  # Print the first 500 characters of the first document