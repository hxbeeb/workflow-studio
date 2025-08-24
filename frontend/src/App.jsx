import { ClerkProvider, SignedIn, SignedOut } from '@clerk/clerk-react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import WorkflowBuilder from './components/WorkflowBuilder';
import ChromaDBViewer from './components/ChromaDBViewer';
import AuthPage from './components/AuthPage';
import SignUpPage from './components/SignUpPage';
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
              <Route path="/auth" element={<Navigate to="/" replace />} />
              <Route path="/auth/sign-up" element={<Navigate to="/" replace />} />
            </Routes>
          </SignedIn>
          
          <SignedOut>
            <Routes>
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/auth/sign-up" element={<SignUpPage />} />
              <Route path="*" element={<Navigate to="/auth" replace />} />
            </Routes>
          </SignedOut>
        </div>
      </Router>
    </ClerkProvider>
  );
}

export default App;
