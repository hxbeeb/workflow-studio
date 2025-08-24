from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, JSON, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from config import Config

# Database configuration - Use PostgreSQL
DATABASE_URL = Config.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Item Model
class Item(Base):
    __tablename__ = "items"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # Remove foreign key constraint
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    type = Column(String, default="task")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workflows = relationship("Workflow", back_populates="item")

# Workflow Model
class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    item_id = Column(String, ForeignKey("items.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    components = Column(JSON)  # Store workflow components and connections
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item = relationship("Item", back_populates="workflows")
    conversations = relationship("Conversation", back_populates="workflow")
    documents = relationship("Document", back_populates="workflow")

# Conversation Model
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    user_query = Column(Text, nullable=False)
    system_response = Column(Text)
    context_used = Column(JSON)  # Store context from knowledge base
    llm_used = Column(String)  # Which LLM was used
    processing_time = Column(Float)  # Time taken to process
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="conversations")

# Document Model
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    extracted_text = Column(Text)
    embeddings_created = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="documents")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
