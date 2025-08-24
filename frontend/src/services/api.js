import axios from 'axios';

// const API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = 'http://localhost:8000';

// Helper function to get auth headers from Clerk user
export const getAuthHeaders = async (user, getToken) => {
  console.log('getAuthHeaders called with user:', user);
  
  if (!user || !getToken) {
    console.log('No user or getToken provided to getAuthHeaders');
    return {};
  }
  
  try {
    // Get the JWT token from Clerk using the correct method
    console.log('Getting JWT token from user...');
    
    const token = await getToken();
    console.log('JWT token from getToken():', token ? `${token.substring(0, 20)}...` : 'null');
    
    if (!token) {
      console.log('No JWT token available, user might not be fully authenticated');
      return {};
    }
    
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
    
    console.log('Generated auth headers:', { 'Authorization': `Bearer ${token ? token.substring(0, 20) + '...' : 'null'}` });
    return headers;
  } catch (error) {
    console.error('Error getting JWT token:', error);
    return {};
  }
};

// Helper function to handle authentication errors
const handleAuthError = () => {
  console.log('Authentication failed, redirecting to auth page');
  // Redirect to auth page
  window.location.href = '/auth';
};

// Items API
export const itemsAPI = {
  getAll: async (user, getToken) => {
    console.log('itemsAPI.getAll called with user:', user);
    const headers = await getAuthHeaders(user, getToken);
    console.log('Final headers for getAll:', headers);
    
    const response = await fetch(`${API_BASE_URL}/items`, {
      headers
    });
    
    if (response.status === 401) {
      handleAuthError();
      throw new Error('Authentication required');
    }
    
    return response.json();
  },
  getById: async (user, id, getToken) => {
    const headers = await getAuthHeaders(user, getToken);
    const response = await fetch(`${API_BASE_URL}/items/${id}`, {
      headers
    });
    
    if (response.status === 401) {
      handleAuthError();
      throw new Error('Authentication required');
    }
    
    return response.json();
  },
  create: async (user, item, getToken) => {
    const headers = await getAuthHeaders(user, getToken);
    const response = await fetch(`${API_BASE_URL}/items`, {
      method: 'POST',
      headers,
      body: JSON.stringify(item)
    });
    
    if (response.status === 401) {
      handleAuthError();
      throw new Error('Authentication required');
    }
    
    return response.json();
  },
  update: async (user, id, item, getToken) => {
    const headers = await getAuthHeaders(user, getToken);
    const response = await fetch(`${API_BASE_URL}/items/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(item)
    });
    
    if (response.status === 401) {
      handleAuthError();
      throw new Error('Authentication required');
    }
    
    return response.json();
  },
  delete: async (user, id, getToken) => {
    const headers = await getAuthHeaders(user, getToken);
    const response = await fetch(`${API_BASE_URL}/items/${id}`, {
      method: 'DELETE',
      headers
    });
    
    if (response.status === 401) {
      handleAuthError();
      throw new Error('Authentication required');
    }
    
    return response;
  }
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
