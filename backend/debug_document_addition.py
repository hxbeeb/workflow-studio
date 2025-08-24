#!/usr/bin/env python3
"""
Debug document addition after deleting all collections
"""

from services.ai_service import DocumentProcessor, ChromaDBService
from database import SessionLocal, Document, Workflow
import os
import uuid
from config import Config

def debug_document_addition():
    """Debug document addition process"""
    print("🔍 Debugging Document Addition After Collection Deletion")
    print("=" * 60)
    
    # Initialize services
    document_processor = DocumentProcessor()
    vector_store = ChromaDBService()
    
    # Check ChromaDB status
    print("\n1. Checking ChromaDB Status:")
    try:
        collections = vector_store.client.list_collections()
        print(f"   Collections found: {len(collections)}")
        for col in collections:
            print(f"   - {col.name}: {col.count()} documents")
    except Exception as e:
        print(f"   Error listing collections: {e}")
    
    # Check if there are any uploaded files
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
        print(f"\n2. Found {len(files)} PDF files in uploads directory")
        
        if files:
            # Test with the first file
            test_file = os.path.join(uploads_dir, files[0])
            print(f"   Testing with file: {test_file}")
            
            # Extract workflow_id from filename
            filename = os.path.basename(test_file)
            if '_' in filename:
                workflow_id = filename.split('_')[0]
                print(f"   Extracted workflow_id: {workflow_id}")
                
                # Check if workflow exists in database
                db = SessionLocal()
                try:
                    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
                    if workflow:
                        print(f"   ✅ Workflow found in database: {workflow.name}")
                        
                        # Check if document exists in database
                        document = db.query(Document).filter(
                            Document.workflow_id == workflow_id,
                            Document.filename == filename.replace(workflow_id + '_', '')
                        ).first()
                        
                        if document:
                            print(f"   ✅ Document found in database: {document.filename}")
                            
                            # Test document processing
                            print(f"\n3. Testing Document Processing:")
                            try:
                                processed_data = document_processor.process_document(test_file, workflow_id)
                                print(f"   ✅ Processing successful:")
                                print(f"      - Text length: {len(processed_data['text'])}")
                                print(f"      - Chunks: {len(processed_data['chunks'])}")
                                print(f"      - Embeddings: {len(processed_data['embeddings'])}")
                                
                                # Test adding to ChromaDB
                                print(f"\n4. Testing ChromaDB Addition:")
                                try:
                                    metadata = [{"workflow_id": workflow_id, "filename": document.filename} for _ in processed_data["chunks"]]
                                    ids = vector_store.add_documents(
                                        workflow_id=workflow_id,
                                        documents=processed_data["chunks"],
                                        embeddings=processed_data["embeddings"],
                                        metadata=metadata
                                    )
                                    print(f"   ✅ Successfully added {len(ids)} documents to ChromaDB")
                                    
                                    # Verify the documents were added
                                    collection = vector_store.get_or_create_collection(workflow_id)
                                    count = collection.count()
                                    print(f"   ✅ Collection count after addition: {count}")
                                    
                                    # Check if documents are actually there
                                    if count > 0:
                                        print(f"   ✅ Documents successfully added to ChromaDB")
                                    else:
                                        print(f"   ❌ Collection shows 0 documents despite successful addition")
                                        
                                except Exception as chroma_error:
                                    print(f"   ❌ Error adding to ChromaDB: {chroma_error}")
                                    import traceback
                                    traceback.print_exc()
                                    
                            except Exception as process_error:
                                print(f"   ❌ Error processing document: {process_error}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"   ❌ Document not found in database")
                    else:
                        print(f"   ❌ Workflow not found in database")
                finally:
                    db.close()
            else:
                print(f"   ❌ Could not extract workflow_id from filename: {filename}")
        else:
            print("   No PDF files found for testing")
    else:
        print("   Uploads directory not found")

if __name__ == "__main__":
    debug_document_addition()
