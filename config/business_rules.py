PLANS = [
    {
        'id': 1,
        'name': 'Basic',
        'monthly_price': 99,
        'api_call_limit': 10000,
        'data_retention_days': 30,
        'max_projects': 3,
        'features': ['basic_analytics', 'dashboard', 'api_access']
    },
    {
        'id': 2,
        'name': 'Pro',
        'monthly_price': 299,
        'api_call_limit': 50000,
        'data_retention_days': 90,
        'max_projects': 10,
        'features': ['basic_analytics', 'dashboard', 'api_access', 'advanced_analytics', 'custom_reports']        
    },
    {
        'id': 3,
        'name': 'Enterprise',
        'monthly_price': 999,
        'api_call_limit': 200000,
        'data_retention_days': 365,
        'max_projects': 50,
        'features': ['basic_analytics', 'dashboard', 'api_access', 'advanced_analytics', 'custom_reports', 'white_label', 'priority_support']
   }
]

UPGRADE_USAGE_THRESHOLD = 0.8
PAYMENT_FAILURE_CHURN_THRESHOLD = 2
SIMULATION_MONTHS = 24
TOTAL_CUSTOMERS = 1000