import { SignIn } from '@clerk/clerk-react';

const AuthPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Workflow Studio</h1>
          <p className="text-gray-600">Sign in to access your dashboard</p>
        </div>
        
        <div className="bg-white py-8 px-6 shadow rounded-lg">
          <SignIn 
            appearance={{
              elements: {
                formButtonPrimary: 'bg-blue-600 hover:bg-blue-700 text-white',
                card: 'shadow-none',
                headerTitle: 'text-gray-900 text-xl font-semibold',
                headerSubtitle: 'text-gray-600',
                socialButtonsBlockButton: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
                formFieldInput: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                footerActionLink: 'text-blue-600 hover:text-blue-700',
                dividerLine: 'bg-gray-200',
                dividerText: 'text-gray-500'
              }
            }}
            routing="path"
            path="/auth"
            signUpUrl="/auth/sign-up"
            redirectUrl="/"
          />
        </div>
        
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <a href="/auth/sign-up" className="font-medium text-blue-600 hover:text-blue-700">
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
