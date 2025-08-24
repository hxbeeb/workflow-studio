import { useState, useEffect } from 'react';
import { useUser, useClerk } from '@clerk/clerk-react';
import { useLocation, Link } from 'react-router-dom';
import ItemCard from './ItemCard';
import ItemForm from './ItemForm';
import { itemsAPI } from '../services/api';

const Dashboard = () => {
  const { user } = useUser();
  const { signOut } = useClerk();
  const location = useLocation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Debug user object
  useEffect(() => {
    console.log('Dashboard: User object:', user);
    console.log('Dashboard: User ID:', user?.id);
    console.log('Dashboard: User email:', user?.emailAddresses?.[0]?.emailAddress);
  }, [user]);

  // Fetch items on component mount
  useEffect(() => {
    if (user) {
      console.log('Dashboard: User available, fetching data...');
      fetchItems();
    } else {
      console.log('Dashboard: No user available');
    }
  }, [user]);

  const fetchItems = async () => {
    try {
      console.log('Dashboard: Fetching items...');
      setLoading(true);
      const data = await itemsAPI.getAll();
      console.log('Dashboard: Items received:', data);
      setItems(data);
      setError(null);
    } catch (error) {
      console.error('Dashboard: Error fetching items:', error);
      setError('Failed to load items. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateItem = async (itemData) => {
    try {
      console.log('Dashboard: Creating item with data:', itemData);
      const newItem = await itemsAPI.create(itemData);
      console.log('Dashboard: Item created successfully:', newItem);
      setItems(prev => [newItem, ...prev]);
      setShowForm(false);
    } catch (error) {
      console.error('Dashboard: Error creating item:', error);
      alert('Failed to create item. Please try again.');
    }
  };

  const handleUpdateItem = async (itemData) => {
    try {
      const updatedItem = await itemsAPI.update(editingItem.id, itemData);
      setItems(prev => prev.map(item => 
        item.id === editingItem.id ? updatedItem : item
      ));
      setEditingItem(null);
    } catch (error) {
      console.error('Error updating item:', error);
      alert('Failed to update item. Please try again.');
    }
  };

  const handleDeleteItem = async (itemId) => {
    try {
      await itemsAPI.delete(itemId);
      setItems(prev => prev.filter(item => item.id !== itemId));
    } catch (error) {
      console.error('Error deleting item:', error);
      throw error; // Re-throw to be handled by ItemCard
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingItem(null);
  };

  const getFilteredItems = () => {
    return items;
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Please sign in</h2>
          <p className="text-gray-600">You need to be signed in to access the dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Planet Dashboard</h1>
              <p className="text-sm text-gray-600">
                Welcome back, {user.firstName || user.emailAddresses?.[0]?.emailAddress}!
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Link
                to="/chroma-dashboard"
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                🗄️ ChromaDB
              </Link>
              <button
                onClick={() => setShowForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                + New Item
              </button>
              <button
                onClick={() => signOut({ redirectUrl: '/' })}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300"
                title="Logout"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <ItemForm
                onSubmit={editingItem ? handleUpdateItem : handleCreateItem}
                initialData={editingItem}
                onCancel={handleCancelForm}
              />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Total Items</h3>
              <p className="text-3xl font-bold text-blue-600">{items.length}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Pending</h3>
              <p className="text-3xl font-bold text-yellow-600">
                {items.filter(item => (item.status || 'pending') === 'pending').length}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">In Progress</h3>
              <p className="text-3xl font-bold text-blue-600">
                {items.filter(item => (item.status || 'pending') === 'in_progress').length}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Completed</h3>
              <p className="text-3xl font-bold text-green-600">
                {items.filter(item => (item.status || 'pending') === 'completed').length}
              </p>
            </div>
          </div>

          {/* Items List */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Items</h2>
            
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800">{error}</p>
                <button
                  onClick={fetchItems}
                  className="mt-2 text-red-600 hover:text-red-800 underline"
                >
                  Try again
                </button>
              </div>
            ) : items.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No items</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating a new item.</p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    + New Item
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {getFilteredItems().map(item => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onEdit={handleEditItem}
                    onDelete={handleDeleteItem}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
