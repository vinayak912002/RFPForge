# PDF/DOCX loaders 
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredWordDocumentLoader 

def get_loader(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".docx":
        return Docx2txtLoader(file_path)
    elif ext ==".doc":
         return UnstructuredWordDocumentLoader(file_path)
    else:
        raise ValueError("Unsupported file type")
    
loader = get_loader("E:\\vinayak\\RFPForge\\data\\knowledge_docs\\RFP_MAPP10022014.pdf")
documents = loader.load()
# print(f"Loaded {len(documents)} documents.")
# print(documents[10].page_content[:500])  # Print the first 500 characters of the first document 
# print(documents)
# doc = documents[10]
print(repr(documents[10]))  # Print the representation of the document, which includes metadata and content summary

# print("Document(")
# print(f'    page_content="{doc.page_content[:100]}...",')
# print("    metadata={")
# for key, value in doc.metadata.items():
#     print(f'        "{key}": "{value}",')
# print("    }")
# print(")")
