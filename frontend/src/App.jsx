import { ClerkProvider, SignIn, SignUp, SignedIn, SignedOut } from '@clerk/clerk-react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import WorkflowBuilder from './components/WorkflowBuilder';
import ChromaDBViewer from './components/ChromaDBViewer';
import './App.css';

// Replace with your Clerk publishable key
const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <SignedIn>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/workflow/:itemId" element={<WorkflowBuilder />} />
              <Route path="/chroma-dashboard" element={<ChromaDBViewer />} />
            </Routes>
          </SignedIn>
          
          <SignedOut>
            <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
              <div className="max-w-md w-full space-y-8">
                <div className="text-center">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Planet</h1>
                  <p className="text-gray-600">Manage your tasks, issues, and projects</p>
                </div>
                
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                  <div className="space-y-6">
                    <SignIn 
                      appearance={{
                        elements: {
                          formButtonPrimary: 'bg-blue-600 hover:bg-blue-700 text-white',
                          card: 'bg-white',
                          headerTitle: 'text-gray-900',
                          headerSubtitle: 'text-gray-600',
                        }
                      }}
                    />
                    
                    <div className="text-center">
                      <p className="text-sm text-gray-600">
                        Don't have an account?{' '}
                        <button
                          onClick={() => document.querySelector('[data-clerk-sign-up]')?.click()}
                          className="font-medium text-blue-600 hover:text-blue-500"
                        >
                          Sign up
                        </button>
                      </p>
                    </div>
                    
                    <SignUp 
                      appearance={{
                        elements: {
                          formButtonPrimary: 'bg-blue-600 hover:bg-blue-700 text-white',
                          card: 'bg-white',
                          headerTitle: 'text-gray-900',
                          headerSubtitle: 'text-gray-600',
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </SignedOut>
        </div>
      </Router>
    </ClerkProvider>
  );
}

export default App;
