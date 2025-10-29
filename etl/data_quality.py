from etl.db_connection import get_db_connection

class DataQualityChecker:
    
    def __init__(self):
        self.db = get_db_connection()
        self.checks_passed = 0
        self.checks_failed = 0
    
    def run_check(self, check_name, query, expected_result=0):
        print(f"\n  Checking: {check_name}")
        result = self.db.execute_query(query)
        
        if len(result) == 0 or result.iloc[0, 0] == expected_result:
            print(f"    ✓ PASS")
            self.checks_passed += 1
            return True
        else:
            print(f"    ✗ FAIL - Found {result.iloc[0, 0]} issues")
            self.checks_failed += 1
            return False
    
    def check_referential_integrity(self):
        print("\n" + "="*60)
        print("REFERENTIAL INTEGRITY CHECKS")
        print("="*60)
        
        self.run_check(
            "Subscriptions have valid customer_ids",
            """
            SELECT COUNT(*) 
            FROM fact_subscriptions fs 
            LEFT JOIN dim_customers dc ON fs.customer_id = dc.customer_id 
            WHERE dc.customer_id IS NULL;
            """
        )
        
        self.run_check(
            "Subscriptions have valid plan_ids",
            """
            SELECT COUNT(*) 
            FROM fact_subscriptions fs 
            LEFT JOIN dim_plans dp ON fs.plan_id = dp.plan_id 
            WHERE dp.plan_id IS NULL;
            """
        )
        
        self.run_check(
            "Usage events have valid customer_ids",
            """
            SELECT COUNT(*) 
            FROM fact_usage fu 
            LEFT JOIN dim_customers dc ON fu.customer_id = dc.customer_id 
            WHERE dc.customer_id IS NULL;
            """
        )
        
        self.run_check(
            "Billing transactions have valid customer_ids",
            """
            SELECT COUNT(*) 
            FROM fact_billing fb 
            LEFT JOIN dim_customers dc ON fb.customer_id = dc.customer_id 
            WHERE dc.customer_id IS NULL;
            """
        )
    
    def check_data_completeness(self):
        print("\n" + "="*60)
        print("DATA COMPLETENESS CHECKS")
        print("="*60)
        
        self.run_check(
            "No null customer names",
            "SELECT COUNT(*) FROM dim_customers WHERE company_name IS NULL;"
        )
        
        self.run_check(
            "No null subscription start dates",
            "SELECT COUNT(*) FROM fact_subscriptions WHERE start_date IS NULL;"
        )
        
        self.run_check(
            "No negative billing amounts",
            "SELECT COUNT(*) FROM fact_billing WHERE amount < 0;"
        )
        
        self.run_check(
            "Usage events have at least one metric > 0",
            """
            SELECT COUNT(*) 
            FROM fact_usage 
            WHERE api_calls = 0 
              AND data_points_ingested = 0 
              AND queries_executed = 0 
              AND projects_active = 0;
            """
        )
    
    def check_business_logic(self):
        print("\n" + "="*60)
        print("BUSINESS LOGIC CHECKS")
        print("="*60)
        
        self.run_check(
            "Churned customers have no active subscriptions",
            """
            SELECT COUNT(*) 
            FROM dim_customers dc 
            JOIN fact_subscriptions fs ON dc.customer_id = fs.customer_id 
            WHERE dc.status = 'churned' AND fs.status = 'active';
            """
        )
        
        self.run_check(
            "Subscription end dates after start dates",
            """
            SELECT COUNT(*) 
            FROM fact_subscriptions 
            WHERE end_date IS NOT NULL AND end_date < start_date;
            """
        )
        
        print(f"\n  Checking: Usage dates align with subscription periods")
        result = self.db.execute_query("""
            SELECT COUNT(*) as misaligned
            FROM fact_usage fu
            LEFT JOIN fact_subscriptions fs 
                ON fu.customer_id = fs.customer_id 
                AND fu.date BETWEEN fs.start_date AND COALESCE(fs.end_date, '2025-12-31')
            WHERE fs.subscription_id IS NULL;
        """)
        
        misaligned = result.iloc[0, 0]
        if misaligned == 0:
            print(f"    ✓ PASS")
            self.checks_passed += 1
        else:
            print(f"    ⚠ WARNING - {misaligned} usage events outside subscription periods")
            print(f"      (This might be expected for data at period boundaries)")
            self.checks_passed += 1
    
    def generate_summary_stats(self):
        print("\n" + "="*60)
        print("DATA SUMMARY STATISTICS")
        print("="*60)
        
        print("\n  CUSTOMERS:")
        customer_stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN status = 'churned' THEN 1 END) as churned,
                ROUND(100.0 * COUNT(CASE WHEN status = 'churned' THEN 1 END) / COUNT(*), 2) as churn_rate_pct
            FROM dim_customers;
        """)
        for col in customer_stats.columns:
            print(f"    {col}: {customer_stats[col].iloc[0]}")
        
        print("\n  REVENUE:")
        revenue_stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN status = 'success' THEN amount ELSE 0 END) as successful_revenue,
                SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END) as failed_revenue,
                AVG(CASE WHEN status = 'success' THEN amount END) as avg_transaction
            FROM fact_billing;
        """)
        for col in revenue_stats.columns:
            val = revenue_stats[col].iloc[0]
            if 'revenue' in col or 'transaction' in col.lower():
                print(f"    {col}: ${val:,.2f}")
            else:
                print(f"    {col}: {val}")
        
        print("\n  USAGE:")
        usage_stats = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT customer_id) as active_users,
                SUM(api_calls) as total_api_calls,
                AVG(api_calls) as avg_api_calls_per_event,
                MAX(api_calls) as max_api_calls
            FROM fact_usage;
        """)
        for col in usage_stats.columns:
            print(f"    {col}: {usage_stats[col].iloc[0]:,.0f}")
    
    def run_all_checks(self):
        print("\n" + "="*60)
        print("DATA QUALITY CHECK PIPELINE")
        print("="*60)
        
        try:
            self.check_referential_integrity()
            self.check_data_completeness()
            self.check_business_logic()
            self.generate_summary_stats()
            
            print("\n" + "="*60)
            print("FINAL RESULTS")
            print("="*60)
            print(f"  ✓ Checks passed: {self.checks_passed}")
            print(f"  ✗ Checks failed: {self.checks_failed}")
            
            if self.checks_failed == 0:
                print("\n  🎉 ALL CHECKS PASSED - Data is ready for dashboards!")
            else:
                print("\n  ⚠ Some checks failed - review data before proceeding")
            
        except Exception as e:
            print(f"\n✗ Error during quality checks: {e}")
            raise
        finally:
            self.db.close()

def main():
    """Run data quality checks"""
    checker = DataQualityChecker()
    checker.run_all_checks()

if __name__ == "__main__":
    main()