#!/usr/bin/env python3
"""
Script to test database connection and diagnose issues
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from config import Config

def test_database_connection():
    """Test the database connection"""
    print("🔍 Testing Database Connection...")
    print(f"📊 DATABASE_URL: {Config.DATABASE_URL}")
    
    try:
        # Create engine with SSL configuration
        if Config.DATABASE_URL and Config.DATABASE_URL.startswith('postgresql'):
            print("🐘 Using PostgreSQL with SSL configuration...")
            engine = create_engine(
                Config.DATABASE_URL,
                connect_args={
                    "sslmode": "require" if "localhost" not in Config.DATABASE_URL else "prefer"
                },
                pool_pre_ping=True
            )
        else:
            print("💾 Using SQLite...")
            engine = create_engine(Config.DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            print("✅ Database connection successful!")
            print(f"📋 Test query result: {result.fetchone()}")
            
            # Test if tables exist
            if Config.DATABASE_URL.startswith('postgresql'):
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                print(f"📋 Existing tables: {tables}")
            else:
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table'
                """))
                tables = [row[0] for row in result.fetchall()]
                print(f"📋 Existing tables: {tables}")
                
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Check network connectivity")
        print("4. Verify SSL certificates")
        return False
        
    except SQLAlchemyError as e:
        print(f"❌ SQLAlchemy error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def create_sample_data():
    """Create sample data if database is empty"""
    print("\n📝 Creating sample data...")
    
    try:
        from database import SessionLocal, Item, Workflow
        from datetime import datetime
        import uuid
        
        db = SessionLocal()
        
        # Check if we have any items
        item_count = db.query(Item).count()
        if item_count == 0:
            print("📋 Creating sample item...")
            sample_item = Item(
                id=str(uuid.uuid4()),
                user_id="default_user",
                title="Sample Project",
                description="This is a sample project for testing",
                status="active",
                priority="high",
                type="project"
            )
            db.add(sample_item)
            db.commit()
            print(f"✅ Created sample item with ID: {sample_item.id}")
            
            # Create a sample workflow
            print("⚙️ Creating sample workflow...")
            sample_workflow = Workflow(
                id=str(uuid.uuid4()),
                user_id="default_user",
                item_id=sample_item.id,
                name="Sample Workflow",
                description="A sample AI workflow",
                components={
                    "nodes": [
                        {
                            "id": "userQuery_1",
                            "type": "userQuery",
                            "position": {"x": 100, "y": 100},
                            "data": {"label": "User Query"}
                        }
                    ],
                    "edges": []
                }
            )
            db.add(sample_workflow)
            db.commit()
            print(f"✅ Created sample workflow with ID: {sample_workflow.id}")
        else:
            print(f"📋 Found {item_count} existing items")
            
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

if __name__ == "__main__":
    print("🚀 Workflow Studio Database Connection Test")
    print("=" * 50)
    
    # Test connection
    if test_database_connection():
        # Create sample data
        create_sample_data()
        print("\n🎉 Database setup completed successfully!")
    else:
        print("\n💥 Database setup failed!")
        sys.exit(1)
