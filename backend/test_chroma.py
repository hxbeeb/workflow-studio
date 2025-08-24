#!/usr/bin/env python3
"""
Simple test script to verify ChromaDB functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import ChromaDBService, DocumentProcessor
import uuid

def test_chroma_functionality():
    """Test ChromaDB functionality"""
    print("Testing ChromaDB functionality...")
    
    # Initialize services
    vector_store = ChromaDBService()
    doc_processor = DocumentProcessor()
    
    # Test workflow ID
    test_workflow_id = "test-workflow-" + str(uuid.uuid4())
    print(f"Using test workflow ID: {test_workflow_id}")
    
    # Test document processing
    test_text = "This is a test document for ChromaDB functionality testing."
    print(f"Processing test text: {test_text}")
    
    # Create chunks and embeddings
    chunks = doc_processor.chunk_text(test_text)
    embeddings = doc_processor.create_embeddings(chunks)
    
    print(f"Created {len(chunks)} chunks")
    print(f"Created {len(embeddings)} embeddings")
    print(f"First chunk: {chunks[0]}")
    print(f"First embedding (first 5 values): {embeddings[0][:5]}")
    
    # Test adding to ChromaDB
    print("\nAdding documents to ChromaDB...")
    metadata = [{"workflow_id": test_workflow_id, "filename": "test.pdf"} for _ in chunks]
    
    try:
        ids = vector_store.add_documents(
            workflow_id=test_workflow_id,
            documents=chunks,
            embeddings=embeddings,
            metadata=metadata
        )
        print(f"Successfully added documents with IDs: {ids[:3]}...")
        
        # Test collection count
        collection = vector_store.get_or_create_collection(test_workflow_id)
        count = collection.count()
        print(f"Collection count: {count}")
        
        # Test search
        print("\nTesting search functionality...")
        search_results = vector_store.search_similar(test_workflow_id, "test document", n_results=3)
        print(f"Search results: {len(search_results)} documents found")
        
        for i, result in enumerate(search_results):
            print(f"Result {i+1}: {result['document'][:100]}...")
        
        print("\n✅ ChromaDB test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chroma_functionality()
