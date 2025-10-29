import pandas as pd
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl.db_connection import get_db_connection
from etl.config import Config

class FactLoader:
    def __init__(self):
        self.db = get_db_connection()
        self.data_path = Path(Config.RAW_DATA_PATH)

        self.date_lookup = self._load_date_lookup()

    def _load_date_lookup(self):
        query = "SELECT date, date_id FROM dim_date;"
        df = self.db.execute_query(query)
        return dict(zip(df['date'], df['date_id']))
    
    def _map_date_to_id(self, date_series):
        return date_series.map(self.date_lookup)
    def load_subscriptions(self):
        print("\n" + "="*60)
        print("Loading fact_subscriptions...")
        print("="*60)

        df = pd.read_csv(self.data_path / 'subscriptions.csv')
        print(f"  Read {len(df )} subscriptions from CSV")

        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        df['duration_days'] = (df['end_date'] - df['start_date']).dt.days

        df['is_upgrade'] = False
        df['is_downgrade'] = False

        df_mapped = pd.DataFrame({
            'customer_id': df['customer_id'],
            'plan_id': df['plan_id'],
            'plan_name': df['plan_name'],
            'start_date': df['start_date'],
            'end_date': df['end_date'],
            'monthly_price': df['monthly_price'],
            'status': df['status'],
            'billing_cycle': df['billing_cycle'],
            'duration_days': df['duration_days'],
            'is_upgrade': df['is_upgrade'],
            'is_downgrade': df['is_downgrade']            
        })

        self.db.load_dataframe(df_mapped, 'fact_subscriptions', if_exists='append')

        count = self.db.get_table_count('fact_subscriptions')
        print(f"  fact_subcriptions now has {count} rows")

        return count
    
    def load_usage(self):
        print("\n" + "="*60)
        print("Loading fact_usage...")
        print("="*60)

        df = pd.read_csv(self.data_path / 'usage_events.csv')
        print(f"  Read {len(df)} usage events from CSV")

        df['date'] = pd.to_datetime(df['date'])

        print("  Mapping dates to date_ids...")
        df['date_id'] = self._map_date_to_id(df['date'])

        unmapped = df['date_id'].isna().sum()
        if unmapped > 0:
            print(f"  WARNING: {unmapped} dates could not be mapped to date_id")
            df = df.dropna(subset=['date_id'])

        df_mapped = pd.DataFrame({
            'customer_id': df['customer_id'],
            'date': df['date'],
            'date_id': df['date_id'].astype(int),
            'api_calls': df['api_calls'],
            'data_points_ingested': df['data_points_ingested'],
            'queries_executed': df['queries_executed'],
            'projects_active': df['projects_active'],
            'feature_used': df['feature_used']            
        })

        self.db.load_dataframe(df_mapped, 'fact_usage', if_exists='append')

        count = self.db.get_table_count('fact_usage')
        print(f"  fact_usage now has {count} rows")

        return count
    
    def load_billing(self):
        print("\n" + "="*60)
        print("Loading fact_billing...")
        print("="*60)

        df = pd.read_csv(self.data_path / 'billing_transactions.csv')        
        print(f"  Read {len(df)} billing transactions from CSV")
        
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        print("  Mapping dates to date_id...")
        df['date_id'] = self._map_date_to_id(df['transaction_date'])

        unmapped = df['date_id'].isna().sum()
        if unmapped > 0:
            print(f"  WARNING: {unmapped} dates could not be mapped to date_id")
            df = df.dropna(subset=['date_id'])

        df_mapped = pd.DataFrame({
            'customer_id': df['customer_id'],
            'transaction_date': df['transaction_date'],
            'date_id': df['date_id'].astype(int),
            'amount': df['amount'],
            'transaction_type': df['type'],
            'status': df['status']        
        })

        self.db.load_dataframe(df_mapped, 'fact_billing', if_exists='append')

        count = self.db.get_table_count('fact_billing')
        print(f"  fact_billing now has {count} rows")

        revenue_query = """
            SELECT
                status,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM fact_billing
            GROUP BY status;
        """
        revenue_df = self.db.execute_query(revenue_query)
        print("\n  Billing summary:")
        for _, row in revenue_df.iterrows():
            print(f"    {row['status']}: {row['transaction_count']} transactions, ${row['total_amount']:,.2f}")

        return count
    
    def load_all_facts(self):
        print("\n" + "="*60)
        print("FACT LOADING PIPELINE")
        print("="*60)

        try:
            self.load_subscriptions()
            self.load_usage()
            self.load_billing()

            print("\n" + "="*60)
            print("ALL FACTS LOADED SUCCESSFULLY")
            print("="*60)

        except Exception as e:
            print(f"\n Error loading facts: {e}")
            raise
        finally:
            self.db.close()

def main():
    loader = FactLoader()
    loader.load_all_facts()

if __name__ == "__main__":
    main()

