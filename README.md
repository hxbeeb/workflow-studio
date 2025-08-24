# WorkflowAI

A comprehensive AI workflow builder with drag-and-drop functionality, document processing, and multi-LLM support.

![WorkflowAI](https://img.shields.io/badge/React-19-blue?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-purple?style=for-the-badge)

## 🚀 Features

### Frontend (React.js)
- **React Flow Integration**: Visual drag-and-drop workflow builder
- **Clerk Authentication**: Secure user authentication and management
- **Real-time Chat Interface**: Interactive AI conversation system
- **Document Upload**: PDF processing and knowledge base integration
- **Responsive Design**: Modern UI with Tailwind CSS
- **ChromaDB Dashboard**: Visual database management interface

### Backend (FastAPI)
- **SQLite Database**: Lightweight persistent data storage with SQLAlchemy ORM
- **Multi-LLM Support**: OpenAI GPT, Google Gemini, and Anthropic Claude integration
- **Vector Database**: ChromaDB for document embeddings and retrieval
- **Document Processing**: PyMuPDF for PDF text extraction
- **Web Search**: SerpAPI integration for real-time information
- **Workflow Engine**: Dynamic workflow execution system

## 🛠️ Tech Stack

| Frontend | Backend |
|----------|---------|
| React.js 19 | FastAPI (Python) |
| React Flow | SQLite + SQLAlchemy |
| Clerk Auth | ChromaDB (Vector Store) |
| Tailwind CSS | OpenAI API |
| Vite | Google Gemini API |
| | Anthropic Claude API |
| | PyMuPDF |
| | SerpAPI |
| | Sentence Transformers |

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- API Keys: OpenAI, Google Gemini, or Anthropic Claude (optional)
- Clerk Account for authentication

### Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd workflow
```

2. **Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

3. **Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

### Detailed Setup

#### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables (optional):**
Create a `.env` file in the backend directory:
```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
SERPAPI_KEY=your_serpapi_key
```

**Note**: API keys can also be entered directly in the LLM Engine node UI.

5. **Run the backend server:**
```bash
python -m uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

#### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Set up Clerk Authentication:**
- Create account at [clerk.dev](https://clerk.dev)
- Create a new application
- Get your publishable key from the dashboard
- Create a `.env` file in the frontend directory:
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

4. **Start the development server:**
```bash
npm run dev
```

The app will start on `http://localhost:3000`

## 🎯 Usage

### 1. Authentication
- Sign up/sign in with Clerk
- Access the main dashboard

### 2. Create an Item
- Click "New Item" in the dashboard
- Fill in item details (name, description, status)
- Click "Create Item"

### 3. Build a Workflow
- Click on an item to open the workflow builder
- Drag components from the sidebar to the canvas:
  - **User Query**: Entry point for questions
  - **Knowledge Base**: Upload and manage documents
  - **LLM Engine**: Configure AI models and parameters
  - **Output**: Display responses
- Connect components using React Flow
- Save your workflow

### 4. Configure Components

#### Knowledge Base
- Upload PDF documents
- View uploaded documents
- Delete individual documents
- Clear all documents
- Documents are automatically processed and indexed

#### LLM Engine
- Choose provider (OpenAI, Google Gemini, Anthropic)
- Select model (GPT-4, Gemini Pro, Claude, etc.)
- Enter API key
- Configure temperature and max tokens
- Enable web search (optional)
- Add custom prompts

#### Output
- Chat interface for responses
- View processing metadata
- Conversation history

### 5. Execute Workflows
- Click "Run" to test your workflow
- Use the chat interface to ask questions
- View real-time responses with context
- Check processing time and metadata

## 🔧 API Endpoints

### Items
- `GET /items` - Get all items
- `POST /items` - Create new item
- `GET /items/{id}` - Get specific item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

### Workflows
- `GET /workflows` - Get all workflows
- `POST /workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow
- `PUT /workflows/{id}` - Update workflow
- `DELETE /workflows/{id}` - Delete workflow

### Documents
- `POST /workflows/{id}/documents` - Upload and process document
- `GET /workflows/{id}/documents` - Get workflow documents
- `DELETE /workflows/{id}/documents/{filename}` - Delete specific document
- `DELETE /workflows/{id}/documents` - Clear all documents

### Execution
- `POST /workflows/{id}/execute` - Execute workflow with query

### ChromaDB Management
- `GET /chroma-dashboard` - View ChromaDB collections and documents
- `DELETE /chroma-collections/{collection_name}` - Delete ChromaDB collection

## 🚀 Deployment

### Backend (Production)
```bash
# Install production dependencies
pip install gunicorn uvicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend (Production)
```bash
# Build for production
npm run build

# Serve with nginx or similar
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromaDB Schema Mismatch**
```bash
cd backend
python reset_chroma_complete.py
```

2. **Node Disappearing**
- Workflows auto-save every 2 seconds
- Check localStorage backup
- Reload page to restore from backup

3. **Gemini Response Issues**
- Check API key configuration
- Verify model compatibility
- Check server logs for detailed error messages

4. **Document Upload Issues**
- Ensure PDF files are valid
- Check file size limits
- Verify ChromaDB is running

5. **Clerk Authentication Issues**
- Verify publishable key is correct
- Check Clerk dashboard for application settings
- Ensure proper redirect URLs are configured

### Debug Tools
- **ChromaDB Dashboard**: `http://localhost:3000/chroma-dashboard`
- **API Documentation**: `http://localhost:8000/docs`
- **Server Logs**: Check backend console for detailed logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the API endpoints
- Test with the provided examples
- Check server logs for detailed error messages

---

**Built with ❤️ using modern AI technologies**