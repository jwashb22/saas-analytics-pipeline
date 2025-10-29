from etl.data_quality import DataQualityChecker

print("Starting data quality checks...")
checker = DataQualityChecker()
checker.run_all_checks()