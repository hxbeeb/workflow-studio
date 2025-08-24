#!/usr/bin/env python3
"""
Script to help set up environment variables for Workflow Studio
"""

import os
from pathlib import Path

def create_env_file():
    """Create a .env file with default configuration"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    print("🔧 Creating .env file with default configuration...")
    
    env_content = """# Workflow Studio Environment Configuration

# Database Configuration
# For PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/workflow_studio

# For SQLite (for development/testing)
# DATABASE_URL=sqlite:///./workflow.db

# ChromaDB Configuration
CHROMA_API_KEY=your_chroma_api_key
CHROMA_HOST=your_chroma_host
CHROMA_USE_CLOUD=false

# AI Services API Keys (optional - can be provided in UI)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Environment
ENVIRONMENT=development
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit the .env file with your actual database credentials")

def check_env_variables():
    """Check current environment variables"""
    print("🔍 Checking environment variables...")
    
    env_vars = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'CHROMA_API_KEY': os.getenv('CHROMA_API_KEY'),
        'CHROMA_HOST': os.getenv('CHROMA_HOST'),
        'CHROMA_USE_CLOUD': os.getenv('CHROMA_USE_CLOUD'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'ENVIRONMENT': os.getenv('ENVIRONMENT')
    }
    
    for var, value in env_vars.items():
        if value:
            if 'KEY' in var and value != 'your_chroma_api_key':
                print(f"✅ {var}: {'*' * 10} (set)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    return env_vars

def setup_database_url():
    """Interactive setup for database URL"""
    print("\n🐘 Database Setup")
    print("=" * 30)
    
    db_type = input("Choose database type (1=PostgreSQL, 2=SQLite): ").strip()
    
    if db_type == "1":
        print("\n📝 PostgreSQL Configuration:")
        host = input("Host (default: localhost): ").strip() or "localhost"
        port = input("Port (default: 5432): ").strip() or "5432"
        database = input("Database name (default: workflow_studio): ").strip() or "workflow_studio"
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
    else:
        print("\n💾 Using SQLite for development")
        database_url = "sqlite:///./workflow.db"
    
    # Update .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace DATABASE_URL
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('DATABASE_URL='):
                lines[i] = f'DATABASE_URL={database_url}'
                break
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Updated DATABASE_URL: {database_url}")
    else:
        print("❌ .env file not found. Run create_env_file() first.")

if __name__ == "__main__":
    print("🚀 Workflow Studio Environment Setup")
    print("=" * 40)
    
    # Check if .env exists
    if not Path(".env").exists():
        create_env_file()
    
    # Check current environment
    check_env_variables()
    
    # Interactive setup
    setup = input("\nWould you like to set up the database URL? (y/n): ").strip().lower()
    if setup == 'y':
        setup_database_url()
    
    print("\n🎉 Environment setup completed!")
    print("📝 Next steps:")
    print("1. Edit .env file with your actual credentials")
    print("2. Run: python test_db_connection.py")
    print("3. Run: python main.py")
