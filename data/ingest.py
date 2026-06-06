import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag import embed_documents
from data.bank_policies import BANK_POLICIES

if __name__ == "__main__":
    print("Starting ingestion...")
    embed_documents(BANK_POLICIES)
    print("Done. All policies embedded into Qdrant.")