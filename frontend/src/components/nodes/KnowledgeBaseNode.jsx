import { memo, useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';

import { documentsAPI } from '../../services/api';

const KnowledgeBaseNode = memo(({ data, isConnectable, selected, id, onNodeDelete, workflowId }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load documents when workflowId changes
  useEffect(() => {
    if (workflowId) {
      loadDocuments();
    }
  }, [workflowId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await documentsAPI.getDocuments(workflowId);
      setDocuments(docs || []);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }
    
    try {
      const result = await documentsAPI.deleteDocument(workflowId, documentId);
      if (result.success) {
        alert(`Document "${filename}" deleted successfully`);
        // Reload documents after deletion
        await loadDocuments();
      } else {
        alert(`Failed to delete document: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      alert(`Error deleting document: ${error.message}`);
    }
  };

  const handleClearAllDocuments = async () => {
    if (!confirm('Are you sure you want to clear ALL documents from this Knowledge Base? This cannot be undone.')) {
      return;
    }
    
    try {
      const result = await documentsAPI.clearAllDocuments(workflowId);
      if (result.success) {
        alert('All documents cleared successfully');
        // Reload documents after clearing
        await loadDocuments();
      } else {
        alert(`Failed to clear documents: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error clearing documents:', error);
      alert(`Error clearing documents: ${error.message}`);
    }
  };



  const handleDelete = (e) => {
    e.stopPropagation();
    if (onNodeDelete) {
      onNodeDelete(id);
    }
  };

  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-white border-2 min-w-[200px] relative ${
      selected ? 'border-blue-500' : 'border-gray-200'
    }`} style={{ overflow: 'visible' }}>
      {/* Delete button */}
      {selected && (
        <button
          onClick={handleDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 transition-colors z-10"
          title="Delete node"
        >
          ×
        </button>
      )}



      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-green-100">
          📚
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold">Knowledge Base</div>
          <div className="text-gray-500">Document storage</div>
        </div>
      </div>
      <div className="mt-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">Upload PDF</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            if (!workflowId) {
              alert('Please save the workflow first to upload documents.');
              return;
            }
            try {
              const res = await documentsAPI.upload(workflowId, file);
              if (res?.success) {
                alert(`Uploaded: ${file.name}. Chunks created: ${res.chunks_created}`);
                // Reload documents after successful upload
                await loadDocuments();
              } else if (res?.detail) {
                alert(`Upload failed: ${res.detail}`);
                // Don't clear file input on failure
              } else {
                alert('Upload failed. Please check server logs.');
                // Don't clear file input on failure
              }
            } catch (err) {
              console.error('Upload error', err);
              const message = (err && err.message) ? err.message : 'Error uploading file';
              alert(message);
              // Don't clear file input on error - let user retry
            }
          }}
          className="block w-full text-xs text-gray-700 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-medium file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
        />
        {!workflowId && (
          <p className="text-xs text-yellow-600 mt-1">Save the workflow to enable uploads.</p>
        )}
        
        {/* Show uploaded documents */}
        {workflowId && (
          <div className="mt-3">
                    <div className="flex items-center justify-between text-xs font-medium text-gray-700 mb-2">
          <span>Uploaded Documents:</span>
          {documents.length > 0 && (
            <button
              onClick={handleClearAllDocuments}
              className="text-red-500 hover:text-red-700 text-xs"
              title="Clear all documents"
            >
              🗑️ Clear All
            </button>
          )}
        </div>
            {loading ? (
              <div className="text-xs text-gray-500">Loading...</div>
            ) : documents.length > 0 ? (
              <div className="space-y-1">
                {documents.map((doc, index) => (
                  <div key={doc.id || index} className="flex items-center justify-between text-xs text-green-600 bg-green-50 p-1 rounded">
                    <span>📄 {doc.filename || doc.name || `Document ${index + 1}`}</span>
                    <button
                      onClick={() => handleDeleteDocument(doc.id, doc.filename || doc.name || `Document ${index + 1}`)}
                      className="text-red-500 hover:text-red-700 ml-2 text-xs"
                      title="Delete document"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-500">No documents uploaded yet</div>
            )}
          </div>
        )}
      </div>
      <Handle
        id="out"
        type="source"
        position={Position.Bottom}
        isConnectable={isConnectable}
        style={{ width: 18, height: 18, zIndex: 20, pointerEvents: 'all', bottom: -9 }}
      />
    </div>
  );
});

KnowledgeBaseNode.displayName = 'KnowledgeBaseNode';

export default KnowledgeBaseNode;


