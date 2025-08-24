from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import shutil
from sqlalchemy.orm import Session

# Import our modules
from database import get_db, create_tables, Item, Workflow, Conversation, Document
from services.ai_service import document_processor, vector_store, workflow_engine
from chroma_connection import get_chroma_collection

app = FastAPI(title="AI Planet API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173","https://work-flow-studio.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create tables on startup
create_tables()

# Pydantic Models
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    type: str = "task"

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None

class ItemResponse(ItemBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    components: Dict[str, Any]

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WorkflowResponse(WorkflowCreate):
    id: str
    user_id: str
    item_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    context_used: Optional[List[str]] = None
    llm_used: Optional[str] = None
    processing_time: float
    workflow_id: str

# Simple user dependency - expects user info from frontend
async def get_current_user(
    user_id: str = "default_user"  # Default user for simplicity
) -> dict:
    """Get current user from frontend headers"""
    return {"id": user_id}

# Routes
@app.get("/")
def root():
    return {"message": "AI Planet API is running"}

# Items CRUD
@app.get("/items", response_model=List[ItemResponse])
async def get_all_items(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all items for the current user"""
    items = db.query(Item).filter(Item.user_id == current_user["id"]).all()
    
    # Convert SQLAlchemy objects to dictionaries, excluding _sa_instance_state
    item_dicts = []
    for item in items:
        item_dict = {
            'id': item.id,
            'user_id': item.user_id,
            'title': item.title,
            'description': item.description,
            'status': item.status,
            'priority': item.priority,
            'type': item.type,
            'created_at': item.created_at,
            'updated_at': item.updated_at
        }
        item_dicts.append(item_dict)
    
    return item_dicts

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new item"""
    try:
        db_item = Item(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            title=item.title,
            description=item.description,
            status=item.status,
            priority=item.priority,
            type=item.type
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Convert to dictionary
        return {
            'id': db_item.id,
            'user_id': db_item.user_id,
            'title': db_item.title,
            'description': db_item.description,
            'status': db_item.status,
            'priority': db_item.priority,
            'type': db_item.type,
            'created_at': db_item.created_at,
            'updated_at': db_item.updated_at
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a single item by ID"""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user["id"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Convert to dictionary
    return {
        'id': item.id,
        'user_id': item.user_id,
        'title': item.title,
        'description': item.description,
        'status': item.status,
        'priority': item.priority,
        'type': item.type,
        'created_at': item.created_at,
        'updated_at': item.updated_at
    }

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item_update: ItemUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update item by ID"""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user["id"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    
    # Convert to dictionary
    return {
        'id': item.id,
        'user_id': item.user_id,
        'title': item.title,
        'description': item.description,
        'status': item.status,
        'priority': item.priority,
        'type': item.type,
        'created_at': item.created_at,
        'updated_at': item.updated_at
    }

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete item by ID"""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user["id"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return None

# Workflow CRUD
@app.get("/workflows", response_model=List[WorkflowResponse])
async def get_workflows(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all workflows for the current user"""
    workflows = db.query(Workflow).filter(Workflow.user_id == current_user["id"]).all()
    
    # Convert SQLAlchemy objects to dictionaries
    workflow_dicts = []
    for workflow in workflows:
        workflow_dict = {
            'id': workflow.id,
            'user_id': workflow.user_id,
            'item_id': workflow.item_id,
            'name': workflow.name,
            'description': workflow.description,
            'components': workflow.components,
            'is_active': workflow.is_active,
            'created_at': workflow.created_at,
            'updated_at': workflow.updated_at
        }
        workflow_dicts.append(workflow_dict)
    
    return workflow_dicts

@app.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow_data: Dict[str, Any], current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new workflow"""
    try:
        print(f"Received workflow data: {workflow_data}")
        
        # Extract item_id and workflow data
        item_id = workflow_data.get("item_id")
        if not item_id:
            raise HTTPException(status_code=400, detail="item_id is required")
            
        # Verify item belongs to user
        item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user["id"]).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db_workflow = Workflow(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            item_id=item_id,
            name=workflow_data.get("name", f"Workflow for Item {item_id}"),
            description=workflow_data.get("description", ""),
            components=workflow_data.get("components", {})
        )
        db.add(db_workflow)
        # Touch parent item updated_at
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_workflow)
        print(f"Created workflow with ID: {db_workflow.id}")
        
        # Convert to dictionary
        return {
            'id': db_workflow.id,
            'user_id': db_workflow.user_id,
            'item_id': db_workflow.item_id,
            'name': db_workflow.name,
            'description': db_workflow.description,
            'components': db_workflow.components,
            'is_active': db_workflow.is_active,
            'created_at': db_workflow.created_at,
            'updated_at': db_workflow.updated_at
        }
    except Exception as e:
        print(f"Error creating workflow: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a single workflow by ID"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Convert to dictionary
    return {
        'id': workflow.id,
        'user_id': workflow.user_id,
        'item_id': workflow.item_id,
        'name': workflow.name,
        'description': workflow.description,
        'components': workflow.components,
        'is_active': workflow.is_active,
        'created_at': workflow.created_at,
        'updated_at': workflow.updated_at
    }

@app.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str, 
    workflow_update: WorkflowUpdate, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Update workflow by ID"""
    try:
        print(f"Received update request for workflow {workflow_id}")
        print(f"Update data: {workflow_update}")
        print(f"Update data dict: {workflow_update.dict()}")
        
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
        if not workflow:
            print(f"Workflow {workflow_id} not found for user {current_user['id']}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        print(f"Found existing workflow: {workflow.name}")
        
        update_data = workflow_update.dict(exclude_unset=True)
        print(f"Updating workflow {workflow_id} with data: {update_data}")
        
        for field, value in update_data.items():
            print(f"Setting {field} = {value}")
            setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        # Touch parent item updated_at
        parent_item = db.query(Item).filter(Item.id == workflow.item_id, Item.user_id == current_user["id"]).first()
        if parent_item:
            parent_item.updated_at = datetime.utcnow()
        print(f"Committing changes...")
        db.commit()
        db.refresh(workflow)
        print(f"Workflow updated successfully")
        
        # Convert to dictionary
        return {
            'id': workflow.id,
            'user_id': workflow.user_id,
            'item_id': workflow.item_id,
            'name': workflow.name,
            'description': workflow.description,
            'components': workflow.components,
            'is_active': workflow.is_active,
            'created_at': workflow.created_at,
            'updated_at': workflow.updated_at
        }
    except Exception as e:
        print(f"Error updating workflow: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")

@app.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete workflow by ID"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db.delete(workflow)
    db.commit()
    return None

# Document upload and processing
@app.post("/workflows/{workflow_id}/documents")
async def upload_document(
    workflow_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document for a workflow"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    
    # Save file
    file_path = f"uploads/{workflow_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process document
        if file.filename.lower().endswith('.pdf'):
            print(f"Processing PDF file: {file.filename}")
            print(f"File path: {file_path}")
            print(f"Workflow ID: {workflow_id}")
            
            try:
                processed_data = document_processor.process_document(file_path, workflow_id)
                print(f"Document processing successful. Chunks: {len(processed_data.get('chunks', []))}")
                print(f"Embeddings: {len(processed_data.get('embeddings', []))}")
            except Exception as process_error:
                print(f"Error processing document: {process_error}")
                import traceback
                traceback.print_exc()
                raise
            
            # Save document record
            db_document = Document(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                filename=file.filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type="pdf",
                extracted_text=processed_data["text"],
                embeddings_created=True
            )
            db.add(db_document)
            db.commit()
            
            # Add to ChromaDB using the vector_store service
            print(f"Adding {len(processed_data['chunks'])} chunks to ChromaDB for workflow: {workflow_id}")
            
            try:
                # Use the vector_store service to add documents
                metadata = [{"workflow_id": workflow_id, "filename": file.filename} for _ in processed_data["chunks"]]
                ids = vector_store.add_documents(
                    workflow_id=workflow_id,
                    documents=processed_data["chunks"],
                    embeddings=processed_data["embeddings"],
                    metadata=metadata
                )
                print(f"Successfully added {len(ids)} documents to ChromaDB with IDs: {ids[:3]}...")
            except Exception as chroma_error:
                print(f"Error adding to ChromaDB: {chroma_error}")
                import traceback
                traceback.print_exc()
                raise
            
            return {
                "success": True,
                "message": "Document processed successfully",
                "document_id": db_document.id,
                "chunks_created": len(processed_data["chunks"])
            }
        else:
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

# Workflow execution
@app.post("/workflows/{workflow_id}/execute", response_model=QueryResponse)
async def execute_workflow(
    workflow_id: str,
    query: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a workflow with a query"""
    # Debug: Print current user and workflow search
    print(f"Current user: {current_user}")
    print(f"Looking for workflow: {workflow_id}")
    
    # Check if workflow exists at all
    all_workflows = db.query(Workflow).all()
    print(f"All workflows in DB: {[w.id for w in all_workflows]}")
    
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        # Check if workflow exists but belongs to different user
        workflow_exists = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow_exists:
            raise HTTPException(status_code=404, detail=f"Workflow exists but belongs to user {workflow_exists.user_id}, not {current_user['id']}")
        else:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found in database")
    
    # Execute workflow
    result = workflow_engine.execute_workflow(workflow.__dict__, query.query)
    
    # Save conversation
    db_conversation = Conversation(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        user_query=query.query,
        system_response=result.get("response"),
        context_used=result.get("context_used"),
        llm_used=result.get("llm_used"),
        processing_time=result.get("processing_time", 0)
    )
    db.add(db_conversation)
    db.commit()
    
    return QueryResponse(**result)

# ChromaDB document management
class ChromaDocumentRequest(BaseModel):
    ids: list[str]
    documents: list[str]
    metadatas: list[dict]

@app.post("/api/documents/")
async def add_documents(request: ChromaDocumentRequest, col=Depends(get_chroma_collection)):
    """Add documents directly to ChromaDB collection"""
    try:
        col.add(
            ids=request.ids,
            documents=request.documents,
            metadatas=request.metadatas
        )
        return {"message": "Documents added successfully", "ids": request.ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test ChromaDB connection
@app.get("/test-chroma")
async def test_chroma():
    """Test ChromaDB connection and list collections"""
    try:
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        collections = client.list_collections()
        return {
            "success": True,
            "message": "ChromaDB connection successful",
            "collections": [col.name for col in collections]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/test-chroma-add")
async def test_chroma_add():
    """Test adding documents to ChromaDB"""
    try:
        # Test with a simple document
        test_workflow_id = "test-workflow-123"
        test_documents = ["This is a test document for ChromaDB"]
        test_embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5] * 76]  # 384 dimensions
        test_metadata = [{"workflow_id": test_workflow_id, "filename": "test.pdf"}]
        
        # Use the vector_store service
        ids = vector_store.add_documents(
            workflow_id=test_workflow_id,
            documents=test_documents,
            embeddings=test_embeddings,
            metadata=test_metadata
        )
        
        # Check if documents were added
        collection = vector_store.get_or_create_collection(test_workflow_id)
        count = collection.count()
        
        return {
            "success": True,
            "message": "Test document added successfully",
            "ids": ids,
            "collection_count": count
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ChromaDB Dashboard endpoint
@app.get("/chroma-dashboard")
async def chroma_dashboard():
    """Get ChromaDB dashboard data"""
    try:
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        collections = client.list_collections()
        
        dashboard_data = {
            "collections": []
        }
        
        for collection in collections:
            try:
                count = collection.count()
                # Get a sample of documents
                sample = collection.get(limit=5)
                dashboard_data["collections"].append({
                    "name": collection.name,
                    "count": count,
                    "sample_documents": sample.get('documents', [])[:3] if sample else [],
                    "sample_metadatas": sample.get('metadatas', [])[:3] if sample else []
                })
            except Exception as e:
                dashboard_data["collections"].append({
                    "name": collection.name,
                    "error": str(e)
                })
        
        return dashboard_data
    except Exception as e:
        return {
            "error": str(e)
        }

# Delete old ChromaDB collection
@app.delete("/chroma-collections/{collection_name}")
async def delete_chroma_collection(collection_name: str):
    """Delete a specific ChromaDB collection"""
    try:
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        
        # Delete the collection
        client.delete_collection(collection_name)
        
        return {
            "success": True,
            "message": f"Collection '{collection_name}' deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Reset ChromaDB collection for a workflow
@app.post("/workflows/{workflow_id}/documents/reset-chroma")
async def reset_chroma_collection(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset ChromaDB collection for a workflow (delete and recreate)"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        collection_name = f"workflow_{workflow_id}"
        
        # Delete the collection if it exists
        try:
            client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception as e:
            print(f"Collection {collection_name} doesn't exist or couldn't be deleted: {e}")
        
        # Create a new empty collection
        collection = client.create_collection(collection_name)
        print(f"Created new empty collection: {collection_name}")
        
        return {"success": True, "message": f"ChromaDB collection '{collection_name}' reset successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting ChromaDB collection: {str(e)}")

# Get documents for a workflow
@app.get("/workflows/{workflow_id}/documents")
async def get_documents(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get documents for a workflow"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    documents = db.query(Document).filter(Document.workflow_id == workflow_id).order_by(Document.created_at.desc()).all()
    return documents

# Delete a document from a workflow
@app.delete("/workflows/{workflow_id}/documents/{document_id}")
async def delete_document(
    workflow_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document from a workflow"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Find the document
    document = db.query(Document).filter(Document.id == document_id, Document.workflow_id == workflow_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Remove from ChromaDB collection
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        collection_name = f"workflow_{workflow_id}"
        print(f"Deleting from collection: {collection_name}")
        collection = client.get_or_create_collection(collection_name)
        
        # Debug: List all collections
        all_collections = client.list_collections()
        print(f"All collections: {[col.name for col in all_collections]}")
        
        # Debug: Check collection count before deletion
        try:
            before_count = collection.count()
            print(f"Collection has {before_count} documents before deletion")
        except Exception as e:
            print(f"Error getting collection count: {e}")
        
        # Get all documents to find the one to delete
        all_results = collection.get()
        if all_results and 'documents' in all_results:
            # Find the document index (this is a simplified approach)
            # In a real implementation, you'd want to store ChromaDB IDs in the Document model
            documents = all_results['documents']
            ids = all_results.get('ids', [])
            
            # Get all documents from the database for this workflow
            workflow_documents = db.query(Document).filter(Document.workflow_id == workflow_id).all()
            workflow_filenames = [doc.filename for doc in workflow_documents]
            print(f"Documents that should remain: {workflow_filenames}")
            
            # Remove all documents and re-add only the ones that should remain
            documents_to_keep = []
            ids_to_keep = []
            metadatas_to_keep = []
            
            for i, doc in enumerate(documents):
                if i < len(ids):
                    # Check if this document should be kept
                    should_keep = False
                    for filename in workflow_filenames:
                        if filename and filename in doc:
                            should_keep = True
                            break
                    
                    if should_keep:
                        documents_to_keep.append(doc)
                        ids_to_keep.append(ids[i])
                        if i < len(all_results.get('metadatas', [])):
                            metadatas_to_keep.append(all_results['metadatas'][i])
            
            print(f"Keeping {len(documents_to_keep)} documents, removing {len(documents) - len(documents_to_keep)} documents")
            
            # Clear all documents and re-add only the ones we want to keep
            collection.delete(ids=ids)
            if documents_to_keep:
                collection.add(
                    documents=documents_to_keep,
                    ids=ids_to_keep,
                    metadatas=metadatas_to_keep if metadatas_to_keep else None
                )
        
        # Remove from database
        db.delete(document)
        db.commit()
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# Clear all documents from a workflow's ChromaDB collection
@app.delete("/workflows/{workflow_id}/documents/clear")
async def clear_all_documents(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all documents from a workflow's ChromaDB collection"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        # Clear from ChromaDB collection
        from chroma_connection import get_chroma_client
        client = get_chroma_client()
        collection_name = f"workflow_{workflow_id}"
        print(f"Clearing collection: {collection_name}")
        collection = client.get_or_create_collection(collection_name)
        
        # Get all documents and delete them
        all_results = collection.get()
        if all_results and 'ids' in all_results and all_results['ids']:
            collection.delete(ids=all_results['ids'])
            print(f"Deleted {len(all_results['ids'])} documents from ChromaDB")
        
        # Clear from database
        documents = db.query(Document).filter(Document.workflow_id == workflow_id).all()
        for doc in documents:
            db.delete(doc)
        db.commit()
        
        return {"success": True, "message": f"Cleared {len(documents)} documents from workflow"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

# Get conversation history
@app.get("/workflows/{workflow_id}/conversations")
async def get_conversations(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history for a workflow"""
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user["id"]).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    conversations = db.query(Conversation).filter(Conversation.workflow_id == workflow_id).order_by(Conversation.created_at.desc()).all()
    return conversations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


