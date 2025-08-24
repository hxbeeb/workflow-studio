import chromadb
import shutil
import os
import uuid
import time
from typing import List, Dict, Any, Optional, Union
import PyPDF2
import numpy as np
from config import Config
from chroma_connection import get_chroma_client
from database import Document

# Simple hash-based embeddings to avoid compilation issues
import hashlib
import math

class DocumentProcessor:
    def __init__(self):
        # Simple document processor with hash-based embeddings
        pass
    
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
        """Create simple hash-based embeddings for text chunks"""
        embeddings = []
        dim = 384
        
        for text in texts:
            # Create a simple hash-based embedding
            # Use the text hash to seed a random-like vector
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Convert hash to a list of floats
            embedding = []
            for i in range(0, len(text_hash), 2):
                if len(embedding) >= dim:
                    break
                # Convert hex pair to float between -1 and 1
                hex_val = text_hash[i:i+2]
                float_val = (int(hex_val, 16) / 255.0) * 2 - 1
                embedding.append(float_val)
            
            # Pad or truncate to exact dimension
            while len(embedding) < dim:
                embedding.append(0.0)
            embedding = embedding[:dim]
            
            # Normalize to unit vector
            norm = math.sqrt(sum(x * x for x in embedding))
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            embeddings.append(embedding)
        
        return embeddings
    
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
                from chromadb.config import Settings
                self.client = chromadb.Client(Settings(
                    persist_directory=Config.CHROMA_LOCAL_PATH,
                    chroma_db_impl="duckdb+parquet"
                ))
        else:
            # Use local ChromaDB with better error handling
            try:
                from chromadb.config import Settings
                self.client = chromadb.Client(Settings(
                    persist_directory=Config.CHROMA_LOCAL_PATH,
                    chroma_db_impl="duckdb+parquet"
                ))
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
                        from chromadb.config import Settings
                        self.client = chromadb.Client(Settings(
                            persist_directory=Config.CHROMA_LOCAL_PATH,
                            chroma_db_impl="duckdb+parquet"
                        ))
                        print("ChromaDB local store reset completed.")
                    except Exception as reset_err:
                        print(f"Failed to reset ChromaDB local store: {reset_err}")
                        raise
                else:
                    raise
        
        self.collections = {}
    
    def get_or_create_collection(self, workflow_id: str):
        """Get or create a collection for a workflow"""
        collection_name = f"workflow_{workflow_id}"
        print(f"Getting or creating collection: {collection_name}")
        
        if workflow_id not in self.collections:
            try:
                print(f"Trying to get existing collection: {collection_name}")
                collection = self.client.get_collection(name=collection_name)
                print(f"Successfully got existing collection: {collection_name}")
            except Exception as e:
                print(f"Collection {collection_name} not found, creating new one: {e}")
                try:
                    collection = self.client.create_collection(name=collection_name)
                    print(f"Successfully created new collection: {collection_name}")
                except Exception as ce:
                    print(f"Error creating collection {collection_name}: {ce}")
                    # Handle local schema mismatch by resetting store and retrying once
                    if "no such column" in str(e) or "no such column" in str(ce):
                        print("ChromaDB collection access failed due to schema mismatch. Resetting local store and retrying once...")
                        try:
                            shutil.rmtree(Config.CHROMA_LOCAL_PATH, ignore_errors=True)
                            from chromadb.config import Settings
                            self.client = chromadb.Client(Settings(
                                persist_directory=Config.CHROMA_LOCAL_PATH,
                                chroma_db_impl="duckdb+parquet"
                            ))
                            collection = self.client.get_or_create_collection(name=collection_name)
                            print(f"Successfully created collection after reset: {collection_name}")
                        except Exception as retry_err:
                            print(f"Retry after reset failed (collection): {retry_err}")
                            raise
                    else:
                        raise
            self.collections[workflow_id] = collection
        else:
            print(f"Using cached collection: {collection_name}")
        
        return self.collections[workflow_id]
    
    def add_documents(self, workflow_id: str, documents: List[str], embeddings: List[List[float]], metadata: List[Dict] = None):
        """Add documents to the knowledge base"""
        print(f"Adding {len(documents)} documents to workflow {workflow_id}")
        collection = self.get_or_create_collection(workflow_id)
        # Generate IDs for documents
        ids = [str(uuid.uuid4()) for _ in documents]
        print(f"Generated IDs: {ids[:3]}...")
        
        def _do_add():
            print(f"Adding documents to collection with {len(documents)} chunks")
            print(f"First document sample: {documents[0][:100]}..." if documents else "No documents")
            print(f"First embedding sample: {embeddings[0][:5]}..." if embeddings else "No embeddings")
            print(f"First metadata sample: {metadata[0] if metadata else 'No metadata'}")
            print(f"First ID sample: {ids[0] if ids else 'No IDs'}")
            
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata or [{"workflow_id": workflow_id} for _ in documents],
                ids=ids
            )
            print(f"Documents added to collection successfully")
            
            # Persist changes to disk
            print("Persisting changes to disk...")
            self.client.persist()
            print(f"Successfully added and persisted {len(documents)} documents")
            
            # Verify the documents were added
            try:
                count_after = collection.count()
                print(f"Collection count after adding: {count_after}")
            except Exception as count_error:
                print(f"Error getting count after adding: {count_error}")
        
        try:
            _do_add()
        except Exception as e:
            # Handle legacy/local schema mismatch gracefully by resetting and retrying once
            if "no such column" in str(e):
                print("ChromaDB add failed due to schema mismatch. Resetting local store and retrying once...")
                try:
                    shutil.rmtree(Config.CHROMA_LOCAL_PATH, ignore_errors=True)
                    from chromadb.config import Settings
                    self.client = chromadb.Client(Settings(
                        persist_directory=Config.CHROMA_LOCAL_PATH,
                        chroma_db_impl="duckdb+parquet"
                    ))
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
        
        # Create query embedding using hash-based approach
        try:
            # Create a simple hash-based embedding for the query
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            # Convert hash to a list of floats
            query_embedding = []
            dim = 384
            for i in range(0, len(query_hash), 2):
                if len(query_embedding) >= dim:
                    break
                # Convert hex pair to float between -1 and 1
                hex_val = query_hash[i:i+2]
                float_val = (int(hex_val, 16) / 255.0) * 2 - 1
                query_embedding.append(float_val)
            
            # Pad or truncate to exact dimension
            while len(query_embedding) < dim:
                query_embedding.append(0.0)
            query_embedding = query_embedding[:dim]
            
            # Normalize to unit vector
            query_norm = math.sqrt(sum(x * x for x in query_embedding))
            if query_norm > 0:
                query_embedding = [x / query_norm for x in query_embedding]
            
            query_embedding = [query_embedding]
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
        
        # Format results - handle different response formats
        formatted_results = []
        try:
            # Check if results have the expected structure
            if 'documents' in results and results['documents']:
                documents = results['documents']
                metadatas = results.get('metadatas', [])
                distances = results.get('distances', [])
                
                # Handle both list and nested list formats
                if isinstance(documents, list) and len(documents) > 0:
                    if isinstance(documents[0], list):
                        # Nested list format: documents[0] contains the actual documents
                        doc_list = documents[0]
                        meta_list = metadatas[0] if metadatas and len(metadatas) > 0 else []
                        dist_list = distances[0] if distances and len(distances) > 0 else []
                    else:
                        # Flat list format
                        doc_list = documents
                        meta_list = metadatas
                        dist_list = distances
                    
                    for i in range(len(doc_list)):
                        formatted_results.append({
                            'document': doc_list[i],
                            'metadata': meta_list[i] if i < len(meta_list) else {},
                            'distance': dist_list[i] if i < len(dist_list) else 0.0
                        })
            else:
                print("No documents found in search results")
        except Exception as e:
            print(f"Error formatting search results: {e}")
            # Return empty results if formatting fails
            return []
        
        return formatted_results

class LLMService:
    def __init__(self):
        self.available_models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
    
    def generate_response(self, prompt: str, context: List[str] = None, model: str = "gpt-3.5-turbo", api_key: str = None, provider: str = "openai", use_web_search: bool = False, serp_api_key: str = None, custom_prompt: str = None) -> Dict[str, Any]:
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
        
        # Combine context, web search results, custom prompt, and user prompt
        full_prompt = ""
        if context:
            full_prompt += "Context from Knowledge Base:\n" + "\n".join(context) + "\n\n"
        if web_search_results:
            full_prompt += "Web Search Results:\n" + "\n".join(web_search_results) + "\n\n"
        if custom_prompt and custom_prompt.strip():
            print(f"Using custom prompt: {custom_prompt.strip()}")
            full_prompt += f"Custom Instructions:\n{custom_prompt.strip()}\n\n"
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
            
            # Simplified text extraction for newer versions of google-generativeai
            print(f"Response type: {type(response)}")
            
            # Method 1: Try response.parts (newer API)
            try:
                if hasattr(response, 'parts'):
                    parts = response.parts
                    if parts:
                        all_text = []
                        for part in parts:
                            if hasattr(part, 'text') and part.text:
                                all_text.append(part.text)
                        if all_text:
                            result = ' '.join(all_text)
                            print(f"Successfully extracted text using response.parts: {result[:100]}...")
                            return result
            except Exception as e:
                print(f"response.parts failed: {e}")
            
            # Method 2: Try response.text directly (most common)
            try:
                if hasattr(response, 'text'):
                    text = response.text
                    if text and text.strip():
                        print(f"Successfully extracted text using response.text: {text[:100]}...")
                        return text
            except Exception as e:
                print(f"response.text failed: {e}")
            
            # Method 3: Try to call response.text() if it's a method
            try:
                if hasattr(response, 'text') and callable(getattr(response, 'text', None)):
                    text = response.text()
                    if text and text.strip():
                        print(f"Successfully extracted text using response.text(): {text[:100]}...")
                        return text
            except Exception as e:
                print(f"response.text() failed: {e}")
            
            # Method 4: Try response.candidates[0].content.parts[0].text
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and hasattr(parts[0], 'text'):
                            text = parts[0].text
                            if text and text.strip():
                                print(f"Successfully extracted text from candidate: {text[:100]}...")
                                return text
            except Exception as e:
                print(f"candidate.content.parts failed: {e}")
            
            # Method 5: Try to get all text from all parts
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    all_text = []
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    all_text.append(part.text)
                    if all_text:
                        result = ' '.join(all_text)
                        print(f"Successfully extracted text from all parts: {result[:100]}...")
                        return result
            except Exception as e:
                print(f"all parts extraction failed: {e}")
            
            # Method 4: Try to convert response to string and extract
            try:
                response_str = str(response)
                print(f"Response as string: {response_str[:200]}...")
                
                # Simple regex to find text content
                import re
                # Look for text patterns in the response
                text_patterns = [
                    r'"text":\s*"([^"]+)"',
                    r"'text':\s*'([^']+)'",
                    r'text:\s*"([^"]+)"',
                    r'text:\s*\'([^\']+)\''
                ]
                
                for pattern in text_patterns:
                    matches = re.findall(pattern, response_str)
                    if matches:
                        result = ' '.join(matches)
                        print(f"Successfully extracted using regex: {result[:100]}...")
                        return result
                
                # If no text found with regex, try to extract the entire response content
                # This handles cases where the response is a direct string
                if response_str and response_str.strip():
                    # Remove any wrapper text and return the actual content
                    # Look for JSON-like content
                    json_match = re.search(r'\{.*\}', response_str, re.DOTALL)
                    if json_match:
                        return json_match.group(0)
                    
                    # If no JSON found, return the cleaned string
                    cleaned_response = response_str.strip()
                    if cleaned_response and len(cleaned_response) > 10:  # Ensure it's not just whitespace
                        return cleaned_response
                        
            except Exception as e:
                print(f"String parsing failed: {e}")
            
            # Final fallback - return error with response info
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
                custom_prompt = node_data.get('custom_prompt', '')

                # Normalize model for provider
                valid_models = self._valid_models_for_provider(provider)
                if not model or model not in valid_models:
                    model = self._default_model_for_provider(provider)

                result = self.llm_service.generate_response(query, context, model, api_key, provider, use_web_search, serp_api_key, custom_prompt)

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
