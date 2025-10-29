import pandas as pd
from pathlib import Path
from etl.db_connection import get_db_connection
from etl.config import Config

class DimensionLoader:
    def __init__(self):
        self.db = get_db_connection()
        self.data_path = Path(Config.RAW_DATA_PATH)

    def load_plans(self):
        print("\n" + "="*60)
        print("Loading dim_plans...")
        print("="*60)

        df = pd.read_csv(self.data_path / 'plans.csv')
        print(f"  Read {len(df)} plans from CSV")

        df = df.rename(columns={
            'id': 'plan_id',
            'name': 'plan_name'
        })

        self.db.load_dataframe(df, 'dim_plans', if_exists='append')

        count = self.db.get_table_count('dim_plans')
        print(f"  dim_plans now has {count} rows")

        return count
    
    def load_customers(self):
        print("\n" + "="*60)
        print("Loading dim_customers...")
        print("="*60)

        df = pd.read_csv(self.data_path / 'customers.csv')
        print(f"  Read {len(df)} customers from CSV")

        df = df.rename(columns={
            'id': 'customer_id',
            'plan_tier': 'current_plan_tier'
        })

        df['signup_date'] = pd.to_datetime(df['signup_date'])

        self.db.load_dataframe(df, 'dim_customers', if_exists='append')

        count = self.db.get_table_count('dim_customers')
        print(f"  dim_customers now has {count} rows")

        status_query = """
            SELECT status, COUNT(*) as count
            FROM dim_customers
            GROUP BY status
            ORDER BY count DESC;    
        """
        status_df = self.db.execute_query(status_query)
        print("\n  Customer status breakdown:")
        for _, row in status_df.iterrows():
            print(f"    {row['status']}: {row['count']}")

        return count
    
    def load_all_dimensions(self):
        print("\n" + "="*60)
        print("DIMENSION LOADING PIPELINE")
        print("="*60)

        try:
            self.load_plans()
            self.load_customers()

            print("\n" + "="*60)
            print(" ALL DIMENSIONS LOADED SUCCESSFULLY")
            print("="*60)

        except Exception as e:
            print(f"\n Error loading dimensions: {e}")
            raise
        finally:
            self.db.close()

    def main():
        loader = DimensionLoader()
        loader.load_all_dimensions()

    if __name__ == "__main__":
        main()