import { useState, useEffect } from 'react';

const ChromaDBViewer = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('https://workflow-studio.onrender.com/chroma-dashboard');
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
    
    try {
      const response = await fetch(`https://workflow-studio.onrender.com/chroma-collections/${collectionName}`, {
        method: 'DELETE'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`Collection '${collectionName}' deleted successfully`);
        fetchDashboardData(); // Refresh the data
      } else {
        alert(`Failed to delete collection: ${result.error}`);
      }
    } catch (err) {
      alert(`Error deleting collection: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

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
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ChromaDB Dashboard</h1>
        <button 
          onClick={fetchDashboardData}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          🔄 Refresh
        </button>
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
                   {collection.name === 'my_collection' && (
                     <button
                       onClick={() => deleteCollection(collection.name)}
                       className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                       title="Delete this collection (contains old Invoice documents)"
                     >
                       🗑️ Delete
                     </button>
                   )}
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
