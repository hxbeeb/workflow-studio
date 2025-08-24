import axios from 'axios';

// const API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = 'https://workflow-studio.onrender.com';
// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to get user headers from Clerk user
export const getUserHeaders = (user) => {
  if (!user) {
    console.log('No user provided to getUserHeaders');
    return {};
  }
  
  const headers = {
    'X-User-ID': user.id,
    'X-User-Email': user.emailAddresses?.[0]?.emailAddress || '',
    'X-User-First-Name': user.firstName || '',
    'X-User-Last-Name': user.lastName || '',
    'X-User-Image-URL': user.imageUrl || '',
  };
  
  console.log('Generated headers:', headers);
  return headers;
};

// Items API
export const itemsAPI = {
  getAll: () => fetch(`${API_BASE_URL}/items`).then(res => res.json()),
  getById: (id) => fetch(`${API_BASE_URL}/items/${id}`).then(res => res.json()),
  create: (item) => fetch(`${API_BASE_URL}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  }).then(res => res.json()),
  update: (id, item) => fetch(`${API_BASE_URL}/items/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  }).then(res => res.json()),
  delete: (id) => fetch(`${API_BASE_URL}/items/${id}`, { method: 'DELETE' })
};

// Workflows API
export const workflowsAPI = {
  getAll: () => fetch(`${API_BASE_URL}/workflows`).then(res => res.json()),
  getById: (id) => fetch(`${API_BASE_URL}/workflows/${id}`).then(res => res.json()),
  create: (workflow, itemId) => {
    console.log('Creating workflow with data:', workflow, 'itemId:', itemId);
    
    const workflowData = {
      name: workflow.name,
      description: workflow.description || '',
      components: workflow.components,
      item_id: itemId
    };
    
    console.log('Sending workflow data:', workflowData);
    
    return fetch(`${API_BASE_URL}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflowData)
    }).then(res => {
      if (!res.ok) {
        return res.text().then(text => {
          console.error('Create workflow error:', text);
          throw new Error(`HTTP ${res.status}: ${text}`);
        });
      }
      return res.json();
    });
  },
  update: (id, workflow) => {
    console.log('Updating workflow with data:', workflow);
    console.log('Request body:', JSON.stringify(workflow));
    return fetch(`${API_BASE_URL}/workflows/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflow)
    }).then(res => {
      if (!res.ok) {
        return res.text().then(text => {
          console.error('Update workflow error:', text);
          console.error('Response status:', res.status);
          console.error('Response headers:', res.headers);
          throw new Error(`HTTP ${res.status}: ${text}`);
        });
      }
      return res.json();
    });
  },
  delete: (id) => fetch(`${API_BASE_URL}/workflows/${id}`, { method: 'DELETE' })
};

// Documents API
export const documentsAPI = {
  upload: (workflowId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return fetch(`${API_BASE_URL}/workflows/${workflowId}/documents`, {
      method: 'POST',
      body: formData
    }).then(res => res.json());
  },
  
  getDocuments: (workflowId) => fetch(`${API_BASE_URL}/workflows/${workflowId}/documents`).then(res => res.json()),
  
  deleteDocument: (workflowId, documentId) => fetch(`${API_BASE_URL}/workflows/${workflowId}/documents/${documentId}`, {
    method: 'DELETE'
  }).then(res => res.json()),
  
  clearAllDocuments: (workflowId) => fetch(`${API_BASE_URL}/workflows/${workflowId}/documents/clear`, {
    method: 'DELETE'
  }).then(res => res.json()),
  
  resetChromaCollection: (workflowId) => fetch(`${API_BASE_URL}/workflows/${workflowId}/documents/reset-chroma`, {
    method: 'POST'
  }).then(res => res.json())
};

// Workflow Execution API
export const executionAPI = {
  execute: (workflowId, query) => fetch(`${API_BASE_URL}/workflows/${workflowId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  }).then(res => res.json()),
  
  getConversations: (workflowId) => fetch(`${API_BASE_URL}/workflows/${workflowId}/conversations`).then(res => res.json())
};
