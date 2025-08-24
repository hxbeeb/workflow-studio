# Workflow Studio - Complete Architecture Documentation

## 🏗️ System Overview

Workflow Studio is a comprehensive AI workflow management platform that combines task management, visual workflow building, document processing, and multi-LLM AI integration. The system follows a modern client-server architecture with a React frontend and FastAPI backend.

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Database Design](#database-design)
5. [AI Services Architecture](#ai-services-architecture)
6. [Workflow Engine](#workflow-engine)
7. [Vector Database Integration](#vector-database-integration)
8. [Authentication & Security](#authentication--security)
9. [API Design](#api-design)
10. [Component Interactions](#component-interactions)
11. [Data Flow](#data-flow)
12. [Deployment Architecture](#deployment-architecture)
13. [Detailed Component Documentation](#detailed-component-documentation)

---

## 🏛️ System Architecture

### High-Level Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • REST API      │    │ • OpenAI API    │
│ • Workflow      │    │ • Workflow      │    │ • Gemini API    │
│   Builder       │    │   Engine        │    │ • Claude API    │
│ • Chat          │    │ • Document      │    │ • SerpAPI       │
│   Interface     │    │   Processor     │    │ • Clerk Auth    │
│ • ChromaDB      │    │ • Vector Store  │    │                 │
│   Viewer        │    │ • Database      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   Layer         │
                       │                 │
                       │ • PostgreSQL    │
                       │ • ChromaDB      │
                       │ • File Storage  │
                       └─────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 19, React Flow, Tailwind CSS | User interface and workflow visualization |
| **Backend** | FastAPI, Python 3.8+ | API server and business logic |
| **Database** | PostgreSQL, ChromaDB | Data persistence and vector storage |
| **Authentication** | Clerk | User authentication and management |
| **AI Services** | OpenAI, Google Gemini, Anthropic | Large language model integration |
| **Vector DB** | ChromaDB | Document embeddings and similarity search |
| **Build Tools** | Vite, pip | Development and build tooling |

---

## 🔧 Backend Architecture

### Core Components

#### 1. **Main Application (`main.py`)**
**Role**: FastAPI application entry point and API routing
**Key Responsibilities**:
- REST API endpoint definitions
- Request/response handling
- CORS middleware configuration
- Static file serving
- Database session management

**Key Endpoints**:
```python
# Items Management
GET/POST /items                    # CRUD operations for tasks/items
GET/PUT/DELETE /items/{id}        # Individual item operations

# Workflow Management  
GET/POST /workflows               # Workflow CRUD operations
GET/PUT/DELETE /workflows/{id}    # Individual workflow operations

# Document Processing
POST /workflows/{id}/documents     # Upload and process documents
GET /workflows/{id}/documents      # Retrieve workflow documents

# Workflow Execution
POST /workflows/{id}/execute       # Execute workflow with query

# ChromaDB Management
GET /chroma-dashboard             # View vector database contents
DELETE /chroma-collections/{name} # Manage collections
```

#### 2. **Database Layer (`database.py`)**
**Role**: SQLAlchemy ORM models and database configuration
**Key Models**:

```python
class Item(Base):
    """Task/Project items that can have workflows"""
    - id: Primary key
    - user_id: User ownership
    - title, description, status, priority, type
    - created_at, updated_at timestamps
    - workflows: One-to-many relationship

class Workflow(Base):
    """AI workflows associated with items"""
    - id: Primary key
    - user_id, item_id: Relationships
    - name, description: Metadata
    - components: JSON field for React Flow nodes/edges
    - is_active: Workflow status
    - conversations, documents: Related entities

class Conversation(Base):
    """Chat history for workflow executions"""
    - workflow_id: Associated workflow
    - user_query, system_response: Chat content
    - context_used: Knowledge base context
    - llm_used, processing_time: Execution metadata

class Document(Base):
    """Uploaded documents for knowledge base"""
    - workflow_id: Associated workflow
    - filename, file_path: File metadata
    - extracted_text: Processed content
    - embeddings_created: Processing status
```

#### 3. **Configuration (`config.py`)**
**Role**: Environment-based configuration management
**Key Settings**:
- Database connection strings
- ChromaDB configuration (local vs cloud)
- API keys for external services
- Environment-specific settings

---

## 🎨 Frontend Architecture

### Core Components

#### 1. **Application Entry (`App.jsx`)**
**Role**: Main application component with routing and authentication
**Key Features**:
- Clerk authentication provider
- React Router setup
- Protected route handling
- Sign-in/sign-up UI

#### 2. **Dashboard (`Dashboard.jsx`)**
**Role**: Main user interface for task management
**Key Features**:
- Item CRUD operations
- Statistics display
- User profile management
- Navigation to workflow builder

#### 3. **Workflow Builder (`WorkflowBuilder.jsx`)**
**Role**: Visual workflow construction interface
**Key Features**:
- React Flow integration
- Drag-and-drop component placement
- Node configuration panels
- Workflow saving/loading
- Real-time chat interface

#### 4. **Node Components**
**Role**: Individual workflow node implementations

**UserQueryNode**: Entry point for user questions
**KnowledgeBaseNode**: Document management and vector search
**LLMEngineNode**: AI model configuration and execution
**OutputNode**: Response display and chat interface

#### 5. **API Service Layer (`api.js`)**
**Role**: Centralized API communication
**Key Services**:
- Items API: Task management
- Workflows API: Workflow CRUD
- Documents API: File upload/management
- Execution API: Workflow execution

---

## 🗄️ Database Design

### Relational Database (PostgreSQL)

#### Entity Relationships
```
User (Clerk)
  ↓ (1:many)
Items
  ↓ (1:many)
Workflows
  ↓ (1:many)
├── Conversations
└── Documents
```

#### Key Design Patterns
- **UUID Primary Keys**: All entities use string UUIDs
- **Soft Deletes**: Items marked as inactive rather than deleted
- **Audit Trail**: created_at/updated_at timestamps on all entities
- **JSON Storage**: Workflow components stored as JSON for flexibility

### Vector Database (ChromaDB)

#### Collection Structure
```
Collection: workflow_{workflow_id}
├── Documents: Text chunks from uploaded PDFs
├── Embeddings: 384-dimensional vectors
├── Metadata: File info, workflow association
└── IDs: Unique document identifiers
```

#### Key Features
- **Workflow Isolation**: Each workflow has its own collection
- **Metadata Filtering**: Documents tagged with workflow and file info
- **Similarity Search**: Vector-based document retrieval
- **Persistence**: Local file-based storage

---

## 🤖 AI Services Architecture

### Service Layer (`services/ai_service.py`)

#### 1. **DocumentProcessor**
**Role**: PDF processing and text extraction
**Key Functions**:
```python
def extract_text_from_pdf(file_path) -> str
def chunk_text(text, chunk_size=1000, overlap=200) -> List[str]
def create_embeddings(texts) -> List[List[float]]
def process_document(file_path, workflow_id) -> Dict[str, Any]
```

**Processing Pipeline**:
1. PDF text extraction using PyPDF2
2. Text chunking with overlap for context preservation
3. Hash-based embedding generation (384 dimensions)
4. Vector storage in ChromaDB

#### 2. **ChromaDBService**
**Role**: Vector database management
**Key Functions**:
```python
def get_or_create_collection(workflow_id) -> Collection
def add_documents(workflow_id, documents, embeddings, metadata) -> List[str]
def search_similar(workflow_id, query, n_results=5) -> List[Dict]
```

**Features**:
- Automatic collection management
- Schema mismatch handling
- Local persistence
- Workflow-specific document isolation

#### 3. **LLMService**
**Role**: Multi-provider AI model integration
**Supported Providers**:
- OpenAI (GPT-3.5, GPT-4)
- Google Gemini (Gemini Pro, Gemini Flash)
- Anthropic (Claude-3)

**Key Functions**:
```python
def generate_response(prompt, context, model, api_key, provider, 
                     use_web_search, serp_api_key, custom_prompt) -> Dict[str, Any]
```

**Features**:
- Provider-agnostic interface
- Context injection from knowledge base
- Web search integration via SerpAPI
- Custom prompt templates
- Fallback to mock responses when no API key

#### 4. **WorkflowEngine**
**Role**: Workflow execution orchestration
**Key Functions**:
```python
def execute_workflow(workflow_data, query) -> Dict[str, Any]
```

**Execution Flow**:
1. Parse workflow components (nodes/edges)
2. Determine execution path from Output node
3. Gather context from Knowledge Base nodes
4. Execute LLM with context and query
5. Return structured response with metadata

---

## ⚙️ Workflow Engine

### Workflow Structure
```json
{
  "components": {
    "nodes": [
      {
        "id": "node_1",
        "type": "userQuery",
        "position": {"x": 100, "y": 100},
        "data": {}
      },
      {
        "id": "node_2", 
        "type": "knowledgeBase",
        "position": {"x": 300, "y": 100},
        "data": {}
      },
      {
        "id": "node_3",
        "type": "llmEngine", 
        "position": {"x": 500, "y": 100},
        "data": {
          "provider": "openai",
          "model": "gpt-3.5-turbo",
          "api_key": "sk-...",
          "custom_prompt": "..."
        }
      },
      {
        "id": "node_4",
        "type": "output",
        "position": {"x": 700, "y": 100},
        "data": {}
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "node_1",
        "target": "node_3"
      },
      {
        "id": "edge_2", 
        "source": "node_2",
        "target": "node_3"
      },
      {
        "id": "edge_3",
        "source": "node_3", 
        "target": "node_4"
      }
    ]
  }
}
```

### Execution Logic
1. **Path Resolution**: Start from Output node, trace backwards
2. **Context Gathering**: Collect documents from Knowledge Base nodes
3. **LLM Execution**: Run configured AI model with context and query
4. **Response Formatting**: Structure response with metadata

---

## 🔍 Vector Database Integration

### ChromaDB Architecture

#### Local Storage Structure
```
chroma_db_new/
├── chroma.sqlite3          # Metadata database
├── index/                  # Vector index files
└── embeddings/             # Embedding storage
```

#### Collection Management
- **Naming Convention**: `workflow_{workflow_id}`
- **Isolation**: Each workflow has independent collection
- **Persistence**: Local file-based storage
- **Schema Handling**: Automatic migration and reset capabilities

#### Document Processing Pipeline
1. **Upload**: PDF file uploaded to backend
2. **Extraction**: Text extracted using PyPDF2
3. **Chunking**: Text split into overlapping chunks
4. **Embedding**: Hash-based vectors generated
5. **Storage**: Chunks and embeddings stored in ChromaDB
6. **Metadata**: File info and workflow association stored

#### Search Functionality
- **Query Embedding**: User query converted to vector
- **Similarity Search**: Cosine similarity with stored documents
- **Context Retrieval**: Top-k most similar documents returned
- **Metadata Filtering**: Workflow-specific document isolation

---

## 🔐 Authentication & Security

### Clerk Integration
**Role**: User authentication and session management
**Features**:
- Email/password authentication
- Social login providers
- Session management
- User profile data

### Security Measures
- **CORS Configuration**: Restricted origins
- **API Key Management**: User-provided keys for AI services
- **File Upload Validation**: PDF-only uploads
- **Workflow Isolation**: User-specific data access

---

## 🌐 API Design

### RESTful Endpoints

#### Items API
```http
GET    /items                    # List user's items
POST   /items                    # Create new item
GET    /items/{id}              # Get specific item
PUT    /items/{id}              # Update item
DELETE /items/{id}              # Delete item
```

#### Workflows API
```http
GET    /workflows               # List user's workflows
POST   /workflows               # Create workflow
GET    /workflows/{id}          # Get workflow
PUT    /workflows/{id}          # Update workflow
DELETE /workflows/{id}          # Delete workflow
```

#### Documents API
```http
POST   /workflows/{id}/documents     # Upload document
GET    /workflows/{id}/documents     # List documents
DELETE /workflows/{id}/documents/{doc_id}  # Delete document
DELETE /workflows/{id}/documents/clear     # Clear all documents
```

#### Execution API
```http
POST   /workflows/{id}/execute       # Execute workflow
GET    /workflows/{id}/conversations # Get chat history
```

### Request/Response Patterns

#### Standard Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "details": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 🔄 Component Interactions

### Frontend-Backend Communication

#### 1. **Dashboard Flow**
```
Dashboard → API Service → Backend → Database
     ↑                                    ↓
     ←────────── Response ←───────────────┘
```

#### 2. **Workflow Builder Flow**
```
WorkflowBuilder → React Flow → Node Components
     ↓
API Service → Backend → Workflow Engine
     ↑                                    ↓
     ←────────── Response ←───────────────┘
```

#### 3. **Document Processing Flow**
```
File Upload → Backend → DocumentProcessor → ChromaDB
     ↑                                              ↓
     ←────────── Processing Status ←───────────────┘
```

#### 4. **Workflow Execution Flow**
```
Chat Interface → Backend → Workflow Engine → LLM Service
     ↑                                                    ↓
     ←────────── AI Response ←────────────────────────────┘
```

### Data Flow Patterns

#### 1. **User Authentication**
1. Clerk handles authentication
2. User data passed to backend via headers
3. Backend validates user and associates data

#### 2. **Workflow Creation**
1. User drags components in React Flow
2. Components saved as JSON in database
3. Workflow associated with specific item

#### 3. **Document Processing**
1. PDF uploaded via multipart form
2. Backend processes and chunks text
3. Embeddings generated and stored in ChromaDB
4. Document metadata saved in PostgreSQL

#### 4. **AI Query Processing**
1. User query sent to backend
2. Workflow engine determines execution path
3. Context retrieved from ChromaDB
4. LLM called with context and query
5. Response returned with metadata

---

## 🚀 Deployment Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   localhost:3000│◄──►│  localhost:8000 │
│   (Vite Dev)    │    │  (Uvicorn)      │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Local Files   │
                       │                 │
                       |• PostgreSQL DB  │
                       │ • ChromaDB      │
                       │ • Uploads       │
                       └─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/Static    │    │   Load Balancer │    │   Application   │
│   Frontend      │◄──►│   (Nginx)       │◄──►│   Servers       │
│   (Built)       │    │                 │    │   (Gunicorn)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Database      │
                                              │   Layer         │
                                              │                 │
                                              │ • PostgreSQL    │
                                              │ • ChromaDB      │
                                              │ • Object Storage│
                                              └─────────────────┘
```

### Scalability Considerations

#### Horizontal Scaling
- **Stateless Backend**: FastAPI instances can be scaled horizontally
- **Database Separation**: PostgreSQL for relational data, ChromaDB for vectors
- **File Storage**: Object storage (S3) for document uploads

#### Performance Optimization
- **Caching**: Redis for session and query caching
- **CDN**: Static assets served via CDN
- **Database Indexing**: Proper indexes on frequently queried fields
- **Vector Search**: Optimized ChromaDB collections per workflow

---

## 🔧 Configuration Management

### Environment Variables

#### Backend Configuration
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/workflow_studio

# ChromaDB
CHROMA_API_KEY=your_chroma_api_key
CHROMA_HOST=your_chroma_host
CHROMA_USE_CLOUD=false

# AI Services (Optional - can be provided in UI)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Environment
ENVIRONMENT=development
```

#### Frontend Configuration
```env
# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🧪 Testing Strategy

### Backend Testing
- **Unit Tests**: Individual service functions
- **Integration Tests**: API endpoint testing
- **Database Tests**: ORM model validation
- **AI Service Tests**: Mock LLM responses

### Frontend Testing
- **Component Tests**: React component testing
- **Integration Tests**: User workflow testing
- **E2E Tests**: Complete user journey testing

---

## 📊 Monitoring & Logging

### Application Monitoring
- **Performance Metrics**: Response times, throughput
- **Error Tracking**: Exception monitoring
- **User Analytics**: Workflow usage patterns
- **Resource Monitoring**: Database, vector store performance

### Logging Strategy
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Context Information**: User ID, workflow ID, request ID
- **Performance Logging**: Processing times, API call durations

---

## 🔮 Future Enhancements

### Planned Features
1. **Multi-User Collaboration**: Shared workflows and documents
2. **Advanced Workflow Nodes**: Custom function nodes, conditional logic
3. **Real-time Collaboration**: Live workflow editing
4. **Advanced Analytics**: Workflow performance metrics
5. **Mobile Support**: Responsive mobile interface
6. **Plugin System**: Third-party node extensions
7. **Advanced AI Features**: Fine-tuning, custom models
8. **Enterprise Features**: SSO, RBAC, audit logs

### Technical Improvements
1. **Microservices Architecture**: Service decomposition
2. **Event-Driven Architecture**: Async processing
3. **Advanced Caching**: Redis integration
4. **Database Optimization**: Connection pooling, query optimization
5. **Security Enhancements**: Rate limiting, input validation
6. **Performance Optimization**: Lazy loading, code splitting

---

## 📚 Additional Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [User Guide](./USER_GUIDE.md)
- [Developer Guide](./DEVELOPER_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

### Code Organization
```
workflow-studio/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── database.py         # Database models
│   ├── config.py           # Configuration
│   ├── chroma_connection.py # Vector DB connection
│   └── services/           # Business logic
│       └── ai_service.py   # AI services
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx         # Main application
│   │   ├── components/     # React components
│   │   └── services/       # API services
│   └── package.json        # Dependencies
└── README.md              # Project overview
```

---

## 📋 Detailed Component Documentation

### Backend Components

#### 1. **Main Application (`main.py`)**
- **Role**: FastAPI application entry point and API routing
- **Key Endpoints**: Items, Workflows, Documents, Execution, ChromaDB management
- **Features**: CORS middleware, file upload handling, database session management

#### 2. **Database Layer (`database.py`)**
- **Role**: SQLAlchemy ORM models and database configuration
- **Models**: Item, Workflow, Conversation, Document
- **Features**: UUID primary keys, audit trails, JSON storage for workflow components

#### 3. **Configuration (`config.py`)**
- **Role**: Environment-based configuration management
- **Settings**: Database URLs, ChromaDB config, API keys, environment detection

#### 4. **ChromaDB Connection (`chroma_connection.py`)**
- **Role**: Vector database connection management
- **Features**: Singleton client pattern, local storage, dependency injection

### Frontend Components

#### 1. **Application Entry (`App.jsx`)**
- **Role**: Main application component with routing and authentication
- **Features**: Clerk authentication, React Router, protected routes

#### 2. **Dashboard (`Dashboard.jsx`)**
- **Role**: Main user interface for task management
- **Features**: Item CRUD operations, statistics, user profile, navigation

#### 3. **Workflow Builder (`WorkflowBuilder.jsx`)**
- **Role**: Visual workflow construction interface
- **Features**: React Flow integration, drag-and-drop, node configuration, chat interface

#### 4. **API Service Layer (`api.js`)**
- **Role**: Centralized API communication
- **Services**: Items, Workflows, Documents, Execution APIs

### AI Service Components

#### 1. **Document Processor**
- **Role**: PDF processing and text extraction
- **Pipeline**: PDF extraction → Text chunking → Embedding generation → Vector storage

#### 2. **ChromaDB Service**
- **Role**: Vector database management
- **Features**: Collection management, document storage, similarity search

#### 3. **LLM Service**
- **Role**: Multi-provider AI model integration
- **Providers**: OpenAI, Google Gemini, Anthropic
- **Features**: Context injection, web search, custom prompts

#### 4. **Workflow Engine**
- **Role**: Workflow execution orchestration
- **Logic**: Path resolution → Context gathering → LLM execution → Response formatting

### Workflow Nodes

#### 1. **User Query Node**
- Entry point for user questions
- No configuration required

#### 2. **Knowledge Base Node**
- Document management and vector search
- Upload interface and context retrieval

#### 3. **LLM Engine Node**
- AI model configuration and execution
- Provider selection, API keys, custom prompts

#### 4. **Output Node**
- Response display and chat interface
- Conversation history and metadata

### Data Flow Patterns

#### 1. **User Authentication**
Clerk Auth → Frontend → Backend Headers → User Validation

#### 2. **Workflow Creation**
React Flow → Node Configuration → API Save → Database Storage

#### 3. **Document Processing**
File Upload → Backend → PDF Processing → ChromaDB Storage → Metadata Update

#### 4. **Workflow Execution**
User Query → Workflow Engine → Context Retrieval → LLM Call → Response Display

### Key Features

#### Backend
- RESTful API with FastAPI
- PostgreSQL database with SQLAlchemy ORM
- ChromaDB vector database integration
- Multi-LLM provider support
- Document processing pipeline

#### Frontend
- React 19 with modern hooks
- React Flow for visual workflow building
- Clerk authentication integration
- Tailwind CSS for styling
- Real-time chat interface

#### AI Services
- PDF text extraction and chunking
- Hash-based embedding generation
- Vector similarity search
- Multi-provider LLM integration
- Web search capabilities

---

*This documentation provides a comprehensive overview of the Workflow Studio architecture and all its components. For specific implementation details, refer to the individual code files and comments.*
