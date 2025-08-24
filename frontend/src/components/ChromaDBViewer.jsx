import { useState, useEffect } from 'react';

const ChromaDBViewer = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deletingCollections, setDeletingCollections] = useState(new Set());
  const [notification, setNotification] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/chroma-dashboard');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteCollection = async (collectionName) => {
    if (!confirm(`Are you sure you want to delete collection '${collectionName}'? This action cannot be undone.`)) {
      return;
    }
    
    // Add to deleting set
    setDeletingCollections(prev => new Set(prev).add(collectionName));
    
    try {
      const response = await fetch(`http://localhost:8000/chroma-collections/${collectionName}`, {
        method: 'DELETE'
      });
      const result = await response.json();
      
      if (result.success) {
        setNotification({ type: 'success', message: `Collection '${collectionName}' deleted successfully` });
        fetchDashboardData(); // Refresh the data
      } else {
        setNotification({ type: 'error', message: `Failed to delete collection: ${result.error}` });
      }
    } catch (err) {
      setNotification({ type: 'error', message: `Error deleting collection: ${err.message}` });
    } finally {
      // Remove from deleting set
      setDeletingCollections(prev => {
        const newSet = new Set(prev);
        newSet.delete(collectionName);
        return newSet;
      });
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Auto-dismiss notifications after 5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  if (loading) {
    return (
      <div className="p-4">
        <div className="text-center">Loading ChromaDB data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-500">Error: {error}</div>
        <button 
          onClick={fetchDashboardData}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      {/* Notification */}
      {notification && (
        <div className={`mb-4 p-4 rounded-lg ${
          notification.type === 'success' 
            ? 'bg-green-100 border border-green-400 text-green-700' 
            : 'bg-red-100 border border-red-400 text-red-700'
        }`}>
          <div className="flex items-center justify-between">
            <span>{notification.message}</span>
            <button 
              onClick={() => setNotification(null)}
              className="ml-4 text-lg font-bold hover:opacity-70"
            >
              ×
            </button>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ChromaDB Dashboard</h1>
          {dashboardData?.collections && (
            <p className="text-sm text-gray-600 mt-1">
              {dashboardData.collections.length} collection{dashboardData.collections.length !== 1 ? 's' : ''} found
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {dashboardData?.collections?.length > 0 && (
            <button 
              onClick={() => {
                if (confirm(`Are you sure you want to delete ALL ${dashboardData.collections.length} collections? This action cannot be undone.`)) {
                  Promise.all(dashboardData.collections.map(col => deleteCollection(col.name)));
                }
              }}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              🗑️ Delete All Collections
            </button>
          )}
          <button 
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {dashboardData?.collections?.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No collections found in ChromaDB
        </div>
      ) : (
        <div className="space-y-6">
          {dashboardData?.collections?.map((collection, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                             <div className="flex items-center justify-between mb-4">
                 <h2 className="text-xl font-semibold text-gray-900">
                   Collection: {collection.name}
                 </h2>
                 <div className="flex items-center space-x-2">
                   <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                     {collection.count || 0} documents
                   </span>
                   <button
                     onClick={() => deleteCollection(collection.name)}
                     disabled={deletingCollections.has(collection.name)}
                     className={`px-3 py-1 rounded text-sm transition-colors ${
                       deletingCollections.has(collection.name)
                         ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                         : 'bg-red-500 text-white hover:bg-red-600'
                     }`}
                     title={`Delete collection '${collection.name}'`}
                   >
                     {deletingCollections.has(collection.name) ? '⏳ Deleting...' : '🗑️ Delete'}
                   </button>
                 </div>
               </div>

              {collection.error ? (
                <div className="text-red-500 bg-red-50 p-3 rounded">
                  Error: {collection.error}
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Sample Documents */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-700 mb-2">Sample Documents:</h3>
                    {collection.sample_documents?.length > 0 ? (
                      <div className="space-y-2">
                        {collection.sample_documents.map((doc, docIndex) => (
                          <div key={docIndex} className="bg-gray-50 p-3 rounded border">
                            <div className="text-sm text-gray-600 mb-1">
                              Document {docIndex + 1}:
                            </div>
                            <div className="text-sm text-gray-800">
                              {doc.length > 200 ? `${doc.substring(0, 200)}...` : doc}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-sm">No documents found</div>
                    )}
                  </div>

                  {/* Sample Metadata */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-700 mb-2">Sample Metadata:</h3>
                    {collection.sample_metadatas?.length > 0 ? (
                      <div className="space-y-2">
                        {collection.sample_metadatas.map((metadata, metaIndex) => (
                          <div key={metaIndex} className="bg-yellow-50 p-3 rounded border">
                            <div className="text-sm text-gray-600 mb-1">
                              Metadata {metaIndex + 1}:
                            </div>
                            <pre className="text-xs text-gray-800 overflow-x-auto">
                              {JSON.stringify(metadata, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-sm">No metadata found</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChromaDBViewer;
