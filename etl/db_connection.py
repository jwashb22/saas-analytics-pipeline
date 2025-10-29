from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import pandas as pd
from etl.config import Config

class DatabaseConnection:
    
    def __init__(self):
        Config.validate()
        
        self.engine = create_engine(
            Config.DATABASE_URL,
            poolclass=NullPool,  
            echo=False  
        )
        
        self.Session = sessionmaker(bind=self.engine)
    
    def test_connection(self):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                print(f" Successfully connected to PostgreSQL")
                print(f"  Version: {version}")
                return True
        except Exception as e:
            print(f" Database connection failed: {e}")
            return False
    
    def get_table_count(self, table_name):
        query = f"SELECT COUNT(*) FROM {table_name};"
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchone()[0]
    
    def truncate_table(self, table_name):
        with self.engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            conn.commit()
            print(f"  Truncated table: {table_name}")
    
    def load_dataframe(self, df, table_name, if_exists='append'):
        try:
            rows_inserted = df.to_sql(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=1000
            )
            print(f"   Loaded {len(df)} rows into {table_name}")
            return rows_inserted
        except Exception as e:
            print(f"   Failed to load data into {table_name}: {e}")
            raise
    
    def execute_query(self, query):
        return pd.read_sql(query, self.engine)
    
    def close(self):
        self.engine.dispose()
        print("Database connection closed")

def get_db_connection():
    return DatabaseConnection()
