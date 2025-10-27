from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
loader = DirectoryLoader(r"Y:\Projects\aoss-framework\docs\system-docs", glob="*.txt")
docs = loader.load()
embedding_model = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
texts = splitter.split_documents(docs)
Chroma.from_documents(texts, embedding=embedding_model, persist_directory="rag_store")