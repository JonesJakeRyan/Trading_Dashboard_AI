#!/usr/bin/env python3
"""
Quick script to view database tables and data.
Run: python view_database.py
"""
from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv
# from tabulate import tabulate

load_dotenv()
db_url = os.getenv('DATABASE_URL')

def view_database():
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    print("=" * 80)
    print("📊 TRADING DASHBOARD DATABASE")
    print("=" * 80)
    
    # List all tables
    tables = inspector.get_table_names()
    print(f"\n✅ Tables in database ({len(tables)} total):\n")
    
    with engine.connect() as conn:
        for table in sorted(tables):
            if table == 'alembic_version':
                continue
                
            # Get row count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            
            # Get columns
            columns = inspector.get_columns(table)
            col_names = [col['name'] for col in columns[:5]]  # First 5 columns
            
            print(f"📋 {table}")
            print(f"   Rows: {count}")
            print(f"   Columns: {', '.join(col_names)}...")
            
            # Show sample data if exists
            if count > 0:
                result = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                rows = result.fetchall()
                if rows:
                    print(f"   Sample data:")
                    for row in rows:
                        print(f"      {dict(row)}")
            print()
    
    print("=" * 80)
    print("💡 TIP: Install pgAdmin or TablePlus for a better GUI experience!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        view_database()
    except Exception as e:
        print(f"❌ Error: {e}")
