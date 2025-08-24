import chromadb
import shutil
import os
import uuid
import time
from typing import List, Dict, Any, Optional
import PyPDF2
import numpy as np
from config import Config
from chroma_connection import get_chroma_client
from database import Document

# Use scikit-learn for simple embeddings to avoid heavy compilation
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

class DocumentProcessor:
    def __init__(self):
        # Initialize TF-IDF vectorizer for simple embeddings
        self.vectorizer = None
        if HAS_SKLEARN:
            try:
                self.vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
            except Exception:
                self.vectorizer = None
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create TF-IDF embeddings for text chunks"""
        if self.vectorizer is None:
            # Fallback: deterministic dummy vectors so pipeline can proceed
            dim = 384
            return [[0.0] * dim for _ in texts]
        
        try:
            # Fit and transform the texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            # Convert to dense array and normalize
            embeddings = tfidf_matrix.toarray()
            # Normalize to unit vectors
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms
            return embeddings.tolist()
        except Exception as e:
            print(f"Error creating TF-IDF embeddings: {e}")
            # Fallback: deterministic dummy vectors
            dim = 384
            return [[0.0] * dim for _ in texts]
    
    def process_document(self, file_path: str, workflow_id: str) -> Dict[str, Any]:
        """Process document and return chunks and embeddings"""
        # Extract text
        text = self.extract_text_from_pdf(file_path)
        
        # Create chunks
        chunks = self.chunk_text(text)
        
        # Create embeddings
        embeddings = self.create_embeddings(chunks)
        
        return {
            "text": text,
            "chunks": chunks,
            "embeddings": embeddings
        }
    
class ChromaDBService:
    def __init__(self):
        # Initialize ChromaDB client based on configuration
        if Config.CHROMA_USE_CLOUD:
            try:
                # Use the cloud connection from chroma_connection.py
                self.client = get_chroma_client()
                print("Using ChromaDB CloudClient")
            except Exception as e:
                print(f"ChromaDB Cloud initialization error: {e}")
                # Fallback to local if cloud fails
                print("Falling back to local ChromaDB")
                self.client = chromadb.PersistentClient(path=Config.CHROMA_LOCAL_PATH)
        else:
            # Use local ChromaDB with better error handling
            try:
                self.client = chromadb.PersistentClient(path=Config.CHROMA_LOCAL_PATH)
                # Test the connection
                _ = self.client.list_collections()
                print("Using local ChromaDB")
            except Exception as e:
                print(f"ChromaDB initialization error: {e}")
                # If there's a schema mismatch, reset the database
                if "no such column" in str(e) or "schema" in str(e).lower():
                    print("ChromaDB schema mismatch detected. Resetting local Chroma store...")
                    try:
                        import os
                        import shutil
                        if os.path.exists(Config.CHROMA_LOCAL_PATH):
                            shutil.rmtree(Config.CHROMA_LOCAL_PATH, ignore_errors=True)
                        self.client = chromadb.PersistentClient(path=Config.CHROMA_LOCAL_PATH)
                        print("ChromaDB local store reset completed.")
                    except Exception as reset_err:
                        print(f"Failed to reset ChromaDB local store: {reset_err}")
                        raise
                else:
                    raise
        
        self.collections = {}
    
    def get_or_create_collection(self, workflow_id: str):
        """Get or create a collection for a workflow"""
        if workflow_id not in self.collections:
            try:
                collection = self.client.get_collection(name=f"workflow_{workflow_id}")
            except Exception as e:
                try:
                    collection = self.client.create_collection(name=f"workflow_{workflow_id}")
                except Exception as ce:
                    # Handle local schema mismatch by resetting store and retrying once
                    if "no such column" in str(e) or "no such column" in str(ce):
                        print("ChromaDB collection access failed due to schema mismatch. Resetting local store and retrying once...")
                        try:
                            shutil.rmtree(Config.CHROMA_LOCAL_PATH, ignore_errors=True)
                            self.client = chromadb.PersistentClient(path=Config.CHROMA_LOCAL_PATH)
                            collection = self.client.get_or_create_collection(name=f"workflow_{workflow_id}")
                        except Exception as retry_err:
                            print(f"Retry after reset failed (collection): {retry_err}")
                            raise
                    else:
                        raise
            self.collections[workflow_id] = collection
        return self.collections[workflow_id]
    
    def add_documents(self, workflow_id: str, documents: List[str], embeddings: List[List[float]], metadata: List[Dict] = None):
        """Add documents to the knowledge base"""
        collection = self.get_or_create_collection(workflow_id)
        # Generate IDs for documents
        ids = [str(uuid.uuid4()) for _ in documents]
        
        def _do_add():
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata or [{"workflow_id": workflow_id} for _ in documents],
                ids=ids
            )
        
        try:
            _do_add()
        except Exception as e:
            # Handle legacy/local schema mismatch gracefully by resetting and retrying once
            if "no such column" in str(e):
                print("ChromaDB add failed due to schema mismatch. Resetting local store and retrying once...")
                try:
                    shutil.rmtree(Config.CHROMA_LOCAL_PATH, ignore_errors=True)
                    self.client = chromadb.PersistentClient(path=Config.CHROMA_LOCAL_PATH)
                    # Re-obtain collection and retry
                    collection = self.get_or_create_collection(workflow_id)
                    _do_add()
                except Exception as retry_err:
                    print(f"Retry after reset failed: {retry_err}")
                    raise
            else:
                raise
        
        return ids
    
    def search_similar(self, workflow_id: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents"""
        print(f"Searching for query: '{query}' in workflow: {workflow_id}")
        collection = self.get_or_create_collection(workflow_id)
        
        # Check if collection has any documents
        try:
            collection_count = collection.count()
            print(f"Collection has {collection_count} documents")
        except Exception as e:
            print(f"Error getting collection count: {e}")
        
        # Create query embedding using TF-IDF
        if not HAS_SKLEARN:
            # Without sklearn support, skip semantic search
            print("scikit-learn not available, skipping search")
            return []
        
        try:
            # Create a simple TF-IDF vectorizer for the query
            query_vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
            # Get all documents in the collection for fitting
            all_docs = collection.get()['documents']
            if not all_docs:
                return []
            
            # Fit on all documents and transform query
            query_vectorizer.fit(all_docs)
            query_embedding = query_vectorizer.transform([query]).toarray()[0]
            # Normalize query vector
            query_norm = np.linalg.norm(query_embedding)
            if query_norm > 0:
                query_embedding = query_embedding / query_norm
            query_embedding = [query_embedding.tolist()]
        except Exception as e:
            print(f"Error creating query embedding: {e}")
            return []
        
        # Search
        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            print(f"Search returned: {results}")
        except Exception as e:
            print(f"Error during search: {e}")
            return []
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted_results

class LLMService:
    def __init__(self):
        self.available_models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
    
    def generate_response(self, prompt: str, context: List[str] = None, model: str = "gpt-3.5-turbo", api_key: str = None, provider: str = "openai", use_web_search: bool = False, serp_api_key: str = None) -> Dict[str, Any]:
        """Generate response using LLM with user-provided API key and optional web search"""
        start_time = time.time()
        
        # Perform web search if enabled
        web_search_results = []
        if use_web_search and serp_api_key:
            try:
                web_search_results = self._perform_web_search(prompt, serp_api_key)
                print(f"Web search found {len(web_search_results)} results")
            except Exception as e:
                print(f"Web search error: {e}")
                web_search_results = []
        
        # Combine context, web search results, and prompt
        full_prompt = ""
        if context:
            full_prompt += "Context from Knowledge Base:\n" + "\n".join(context) + "\n\n"
        if web_search_results:
            full_prompt += "Web Search Results:\n" + "\n".join(web_search_results) + "\n\n"
        full_prompt += f"Question: {prompt}\n\nAnswer:"
        
        # Check if API key is provided
        if api_key:
            try:
                # Here you would integrate with the actual LLM API
                # For now, we'll simulate a real API call
                if provider == "openai":
                    response = self._call_openai_api(full_prompt, model, api_key)
                elif provider == "anthropic":
                    response = self._call_anthropic_api(full_prompt, model, api_key)
                elif provider == "gemini":
                    response = self._call_gemini_api(full_prompt, model, api_key)
                else:
                    response = f"Mock response to: {prompt}\n\nContext provided: {len(context) if context else 0} documents\n\nWeb search results: {len(web_search_results)} results\n\n(Using {provider} with provided API key)"
            except Exception as e:
                response = f"Error calling {provider} API: {str(e)}"
        else:
            # Fallback to mock response
            response = f"This is a mock response to: {prompt}\n\nContext provided: {len(context) if context else 0} documents\n\nWeb search results: {len(web_search_results)} results\n\n(No API key provided - using mock mode)"
        
        processing_time = time.time() - start_time
        
        return {
            "response": response,
            "model": model,
            "provider": provider,
            "processing_time": processing_time,
            "context_used": context,
            "web_search_results": web_search_results,
            "api_key_provided": bool(api_key),
            "web_search_used": bool(web_search_results)
        }
    
    def _call_openai_api(self, prompt: str, model: str, api_key: str) -> str:
        """Call OpenAI API (placeholder for real implementation)"""
        # This would be replaced with actual OpenAI API call
        # import openai
        # openai.api_key = api_key
        # response = openai.ChatCompletion.create(
        #     model=model,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return response.choices[0].message.content
        
        return f"OpenAI {model} response: {prompt[:100]}... (API key provided)"
    
    def _call_anthropic_api(self, prompt: str, model: str, api_key: str) -> str:
        """Call Anthropic API (placeholder for real implementation)"""
        # This would be replaced with actual Anthropic API call
        # import anthropic
        # client = anthropic.Anthropic(api_key=api_key)
        # response = client.messages.create(
        #     model=model,
        #     max_tokens=1000,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return response.content[0].text
        
        return f"Anthropic {model} response: {prompt[:100]}... (API key provided)"

    def _call_gemini_api(self, prompt: str, model: str, api_key: str) -> str:
        """Call Gemini API using google-generativeai SDK."""
        print(f"Gemini API call - Model: {model}, API Key provided: {bool(api_key)}")
        
        # Lazy import so the app works even if SDK isn't installed
        try:
            import google.generativeai as genai
            print("Google GenerativeAI SDK imported successfully")
        except Exception as e:
            print(f"Failed to import google.generativeai: {e}")
            # Fallback text if SDK not available
            return f"Gemini {model} response: {prompt[:100]}... (SDK not available)"

        # Normalize model name to a supported one if necessary
        supported_text_models = {
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        }
        # Do not remap 2.5 to older models; use as-is when supported
        resolved_model = model
        if resolved_model not in supported_text_models:
            # Prefer the 2.5 Pro as default when available
            resolved_model = "gemini-1.5-pro"  # Use 1.5-pro as fallback

        print(f"Using Gemini model: {resolved_model}")

        try:
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully")
            
            # Using the high-level interface
            model_client = genai.GenerativeModel(resolved_model)
            print("Gemini model client created")
            
            response = model_client.generate_content(prompt)
            print("Gemini response received")
            
            # Handle response with multiple parts
            print(f"Response type: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            
            # Try the most direct approach first - use the response's text property
            try:
                # For newer versions of google-generativeai, try direct text access
                if hasattr(response, 'text') and callable(getattr(response, 'text', None)):
                    text = response.text
                    if text:
                        print(f"Successfully extracted text using response.text(): {text[:100]}...")
                        return text
            except Exception as e:
                print(f"Direct text() method failed: {e}")
            
            try:
                # Try the simple text accessor first
                text = response.text
                if text:
                    print(f"Successfully extracted text: {text[:100]}...")
                    return text
            except Exception as e:
                print(f"Simple text accessor failed: {e}")
            
            # Fallback: extract from parts
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    print(f"Found {len(response.candidates)} candidates")
                    for i, candidate in enumerate(response.candidates):
                        print(f"Processing candidate {i}: {type(candidate)}")
                        print(f"Candidate attributes: {dir(candidate)}")
                        
                        if hasattr(candidate, 'content'):
                            print(f"Candidate content type: {type(candidate.content)}")
                            print(f"Candidate content attributes: {dir(candidate.content)}")
                            
                            if hasattr(candidate.content, 'parts'):
                                text_parts = []
                                for j, part in enumerate(candidate.content.parts):
                                    print(f"Processing part {j}: {type(part)}")
                                    print(f"Part attributes: {dir(part)}")
                                    if hasattr(part, 'text'):
                                        text_parts.append(part.text)
                                        print(f"Added text: {part.text[:50]}...")
                                if text_parts:
                                    result = ' '.join(text_parts)
                                    print(f"Successfully extracted from parts: {result[:100]}...")
                                    return result
            except Exception as e:
                print(f"Parts extraction failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Try to get response content directly
            try:
                if hasattr(response, 'content'):
                    print("Trying response.content")
                    if hasattr(response.content, 'parts'):
                        text_parts = []
                        for part in response.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        if text_parts:
                            result = ' '.join(text_parts)
                            print(f"Successfully extracted from response.content: {result[:100]}...")
                            return result
            except Exception as e:
                print(f"Response.content extraction failed: {e}")
            
            # Try direct access to response text property
            try:
                if hasattr(response, 'text'):
                    text = response.text
                    if text:
                        print(f"Successfully extracted using response.text: {text[:100]}...")
                        return text
            except Exception as e:
                print(f"Direct text access failed: {e}")
            
            # Try to access the first candidate's text directly
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    first_candidate = response.candidates[0]
                    if hasattr(first_candidate, 'text'):
                        text = first_candidate.text
                        if text:
                            print(f"Successfully extracted using first_candidate.text: {text[:100]}...")
                            return text
            except Exception as e:
                print(f"First candidate text access failed: {e}")
            
            # Try to access the response as a string and parse it
            try:
                response_str = str(response)
                print(f"Response as string: {response_str[:200]}...")
                
                # Try multiple regex patterns to extract text
                import re
                patterns = [
                    r'text["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'content["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'parts["\']?\s*:\s*\[["\']([^"\']+)["\']',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, response_str)
                    if matches:
                        result = ' '.join(matches)
                        print(f"Successfully extracted using regex pattern: {result[:100]}...")
                        return result
            except Exception as e:
                print(f"String parsing failed: {e}")
            
            # Final fallback - return a more informative error
            print(f"All extraction methods failed. Response type: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            return f"Error: Could not extract text from Gemini response. Response type: {type(response)}"
        except Exception as e:
            print(f"Gemini API error: {e}")
            return f"Error calling Gemini API: {str(e)}"
    
    def _perform_web_search(self, query: str, serp_api_key: str) -> List[str]:
        """Perform web search using SERP API"""
        try:
            import requests
            
            # SERP API endpoint
            url = "https://serpapi.com/search"
            
            # Search parameters
            params = {
                'q': query,
                'api_key': serp_api_key,
                'num': 5,  # Number of results
                'engine': 'google'  # Search engine
            }
            
            print(f"Performing web search for: {query}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                search_results = []
                
                # Extract organic search results
                if 'organic_results' in data:
                    for result in data['organic_results'][:5]:  # Top 5 results
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        link = result.get('link', '')
                        
                        # Format the result
                        formatted_result = f"Title: {title}\nSnippet: {snippet}\nURL: {link}"
                        search_results.append(formatted_result)
                
                print(f"Web search completed. Found {len(search_results)} results")
                return search_results
            else:
                print(f"Web search failed with status code: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Web search error: {e}")
            return []

class WorkflowEngine:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = ChromaDBService()
        self.llm_service = LLMService()
    
    def _valid_models_for_provider(self, provider: str):
        if provider == "gemini":
            return ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"]
        if provider == "anthropic":
            return ["claude-3-sonnet", "claude-3-opus", "claude-3-haiku"]
        # default: openai
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    
    def _default_model_for_provider(self, provider: str):
        return self._valid_models_for_provider(provider)[0]
    
    def execute_workflow(self, workflow_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Execute a workflow with a query"""
        try:
            # Extract workflow components
            nodes = workflow_data.get('components', {}).get('nodes', [])
            edges = workflow_data.get('components', {}).get('edges', [])

            # Index nodes by id and type for quick lookup
            id_to_node = {n.get('id'): n for n in nodes}
            nodes_by_type = {}
            for n in nodes:
                nodes_by_type.setdefault(n.get('type'), []).append(n)

            # Helper: incoming sources for a given target id
            def incoming_sources(target_id: str):
                return [id_to_node.get(e.get('source')) for e in edges if e.get('target') == target_id and id_to_node.get(e.get('source'))]

            # Determine the active path by starting from the first Output node
            output_nodes = nodes_by_type.get('output', [])
            if not output_nodes:
                raise Exception("No Output node found. Connect an Output node to run.")

            active_output = output_nodes[0]
            sources_to_output = incoming_sources(active_output.get('id'))
            if not sources_to_output:
                raise Exception("Output node is not connected to any source.")

            # For now, take the first incoming source to Output
            upstream = sources_to_output[0]
            upstream_type = upstream.get('type')

            processing_time_start = time.time()

            if upstream_type == 'llmEngine':
                # Always gather context from Knowledge Base nodes connected to this LLM node
                context: List[str] = []
                print(f"LLM Engine node found: {upstream.get('id')}")
                print(f"Looking for incoming sources to LLM Engine...")
                
                incoming_to_llm = incoming_sources(upstream.get('id'))
                print(f"Incoming sources to LLM: {[src.get('type') for src in incoming_to_llm]}")
                
                for src in incoming_to_llm:
                    print(f"Checking source: {src.get('type')} (ID: {src.get('id')})")
                    if src.get('type') == 'knowledgeBase':
                        print(f"Knowledge Base found! Getting workflow-specific documents...")
                        # Get only documents that belong to this specific workflow
                        try:
                            # First, get the documents from the database for this workflow
                            from database import get_db
                            db = next(get_db())
                            workflow_documents = db.query(Document).filter(Document.workflow_id == workflow_data['id']).all()
                            print(f"Database shows {len(workflow_documents)} documents for workflow {workflow_data['id']}")
                            
                            if workflow_documents:
                                # Get the document filenames for this workflow
                                workflow_filenames = [doc.filename for doc in workflow_documents]
                                print(f"Workflow documents: {workflow_filenames}")
                                
                                # Get all documents from ChromaDB collection
                                collection = self.vector_store.get_or_create_collection(workflow_data['id'])
                                print(f"Using collection: workflow_{workflow_data['id']}")
                                try:
                                    collection_count = collection.count()
                                    print(f"ChromaDB collection has {collection_count} total documents")
                                except Exception as count_error:
                                    print(f"Error getting collection count: {count_error}")
                                    collection_count = 0
                                
                                if collection_count > 0:
                                    all_results = collection.get()
                                    if all_results and 'documents' in all_results:
                                        documents = all_results['documents']
                                        metadatas = all_results.get('metadatas', [])
                                        
                                        # Filter documents to only include those from this workflow
                                        workflow_context = []
                                        print(f"Checking {len(documents)} ChromaDB documents against {len(workflow_filenames)} workflow filenames")
                                        
                                        for i, doc in enumerate(documents):
                                            print(f"Document {i+1}: {doc[:100]}...")
                                            
                                            # Check if this document belongs to the current workflow
                                            doc_belongs_to_workflow = False
                                            matched_filename = None
                                            
                                            # Get metadata for this document
                                            metadata = metadatas[i] if i < len(metadatas) else {}
                                            print(f"Document {i+1} metadata: {metadata}")
                                            
                                            # Strategy 1: Check metadata first (most reliable)
                                            if metadata:
                                                metadata_filename = metadata.get('filename', '')
                                                metadata_workflow_id = metadata.get('workflow_id', '')
                                                
                                                print(f"Document {i+1} - metadata filename: '{metadata_filename}', workflow_id: '{metadata_workflow_id}'")
                                                print(f"Checking against workflow_id: '{workflow_data['id']}' and filenames: {workflow_filenames}")
                                                
                                                # Check if workflow_id matches
                                                if metadata_workflow_id == workflow_data['id']:
                                                    doc_belongs_to_workflow = True
                                                    matched_filename = metadata_filename
                                                    print(f"✓ Document {i+1} matched by workflow_id")
                                                # Check if filename matches
                                                elif metadata_filename in workflow_filenames:
                                                    doc_belongs_to_workflow = True
                                                    matched_filename = metadata_filename
                                                    print(f"✓ Document {i+1} matched by filename")
                                            
                                            # Strategy 2: Fallback to content matching (less reliable)
                                            if not doc_belongs_to_workflow:
                                                for filename in workflow_filenames:
                                                    if filename:
                                                        # Direct filename in document content
                                                        if filename in doc:
                                                            doc_belongs_to_workflow = True
                                                            matched_filename = filename
                                                            print(f"✓ Document {i+1} matched by content (filename: {filename})")
                                                            break
                                                        
                                                        # Filename without extension
                                                        filename_no_ext = filename.replace('.pdf', '').replace('.PDF', '')
                                                        if filename_no_ext in doc:
                                                            doc_belongs_to_workflow = True
                                                            matched_filename = filename
                                                            print(f"✓ Document {i+1} matched by content (filename_no_ext: {filename_no_ext})")
                                                            break
                                            
                                            if doc_belongs_to_workflow:
                                                workflow_context.append(doc)
                                                print(f"✓ Added document {i+1} (matched '{matched_filename}')")
                                            else:
                                                print(f"✗ Skipped document {i+1} (no match)")
                                        
                                        context.extend(workflow_context)
                                        print(f"Added {len(workflow_context)} workflow-specific documents to context")
                                    else:
                                        print("No documents found in ChromaDB collection")
                                else:
                                    print("ChromaDB collection is empty")
                            else:
                                print("No documents found in database for this workflow")
                        except Exception as e:
                            print(f"Error getting Knowledge Base context: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"Source {src.get('type')} is not a Knowledge Base")
                
                print(f"Total context gathered: {len(context)} documents")
                
                # Log the actual Knowledge Base content being sent to LLM
                if context:
                    print("=== KNOWLEDGE BASE CONTENT BEING SENT TO LLM ===")
                    for i, doc in enumerate(context):
                        print(f"Document {i+1}:")
                        print(f"Content: {doc[:200]}..." if len(doc) > 200 else f"Content: {doc}")
                        print("---")
                    print("=== END KNOWLEDGE BASE CONTENT ===")
                else:
                    print("No Knowledge Base content available")

                # Read LLM configuration from this specific LLM node
                node_data = upstream.get('data', {})
                provider = node_data.get('provider', 'openai')
                model = node_data.get('model')
                api_key = node_data.get('api_key')
                use_web_search = node_data.get('use_web_search', False)
                serp_api_key = node_data.get('serp_api_key', '')

                # Normalize model for provider
                valid_models = self._valid_models_for_provider(provider)
                if not model or model not in valid_models:
                    model = self._default_model_for_provider(provider)

                result = self.llm_service.generate_response(query, context, model, api_key, provider, use_web_search, serp_api_key)

                return {
                    "success": True,
                    "response": result["response"],
                    "context_used": result["context_used"],
                    "web_search_results": result.get("web_search_results", []),
                    "web_search_used": result.get("web_search_used", False),
                    "llm_used": result["model"],
                    "provider": result["provider"],
                    "processing_time": result["processing_time"],
                    "workflow_id": workflow_data['id'],
                    "api_key_provided": result["api_key_provided"],
                }

            if upstream_type == 'knowledgeBase':
                # Run a KB-only search and return the top matches as the output
                search_results = self.vector_store.search_similar(
                    workflow_data['id'],
                    query,
                    n_results=5,
                )
                documents = [r['document'] for r in search_results]
                joined = "\n---\n".join(documents) if documents else "No matching context found."
                return {
                    "success": True,
                    "response": joined,
                    "context_used": documents,
                    "llm_used": "kb-search",
                    "provider": "knowledge-base",
                    "processing_time": time.time() - processing_time_start,
                    "workflow_id": workflow_data['id'],
                    "api_key_provided": False,
                }

            if upstream_type == 'userQuery':
                # Directly send the user query to output (echo)
                return {
                    "success": True,
                    "response": query,
                    "context_used": [],
                    "llm_used": "user-query",
                    "provider": "user",
                    "processing_time": time.time() - processing_time_start,
                    "workflow_id": workflow_data['id'],
                    "api_key_provided": False,
                }

            # Unsupported connection type into Output
            raise Exception(f"Unsupported source '{upstream_type}' connected to Output")
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0,
                "workflow_id": workflow_data['id']
            }

# Initialize services
document_processor = DocumentProcessor()
vector_store = ChromaDBService()
workflow_engine = WorkflowEngine()
