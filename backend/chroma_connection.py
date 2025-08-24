import chromadb
from fastapi import Depends
from dotenv import load_dotenv
import os

load_dotenv()

CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")

_client = None
_collection = None

def get_chroma_client():
    global _client
    if _client is None:
        from chromadb.config import Settings
        from config import Config
        _client = chromadb.Client(Settings(
            persist_directory=Config.CHROMA_LOCAL_PATH,
            chroma_db_impl="duckdb+parquet"
        ))
    return _client

def get_chroma_collection(client = Depends(get_chroma_client)):
    global _collection
    if _collection is None:
        _collection = client.get_or_create_collection("my_collection")
    return _collection
