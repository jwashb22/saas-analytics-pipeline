import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from config.customer_archetypes import CUSTOMER_ARCHETYPES, GEOGRAPHIC_MODIFIERS, INDUSTRY_MODIFIERS
from config.business_rules import PLANS, SIMULATION_MONTHS, TOTAL_CUSTOMERS
from config.constants import GEOGRAPHIES, INDUSTRIES, ACQUISITION_CHANNELS

from core.behavior_engine import BehaviorEngine
from core.timeline_simulator import TimelineSimulator
from generators.customer_generator import CustomerGenerator
from generators.subscription_generator import SubscriptionGenerator

def main():
    
    print("🚀 Starting Customer Analytics SaaS Simulation")
    print("=" * 50)
    
    print("📋 Loading configuration...")
    config = {
        'CUSTOMER_ARCHETYPES': CUSTOMER_ARCHETYPES,
        'GEOGRAPHIC_MODIFIERS': GEOGRAPHIC_MODIFIERS,
        'INDUSTRY_MODIFIERS': INDUSTRY_MODIFIERS,
        'PLANS': PLANS,
        'SIMULATION_MONTHS': SIMULATION_MONTHS,
        'TOTAL_CUSTOMERS': TOTAL_CUSTOMERS,
        'GEOGRAPHIES': GEOGRAPHIES,
        'INDUSTRIES': INDUSTRIES,
        'ACQUISITION_CHANNELS': ACQUISITION_CHANNELS
    }
    
    print("🧠 Initializing behavior engine...")
    behavior_engine = BehaviorEngine(
        CUSTOMER_ARCHETYPES,
        {'PLANS': PLANS, 'SIMULATION_MONTHS': SIMULATION_MONTHS},
        GEOGRAPHIC_MODIFIERS,
        INDUSTRY_MODIFIERS
    )
    
    print("📊 Initializing generators...")
    customer_generator = CustomerGenerator(config)
    subscription_generator = SubscriptionGenerator(config)
    timeline_simulator = TimelineSimulator(behavior_engine, subscription_generator, config)
    
    print(f"👥 Generating {TOTAL_CUSTOMERS} customers...")
    customers = customer_generator.generate(TOTAL_CUSTOMERS)
    
    print("\n📈 Customer Archetype Distribution:")
    dist_report = customer_generator.get_archetype_distribution(customers)
    for archetype, stats in dist_report.items():
        print(f"  {archetype}: {stats['actual_count']} ({stats['actual_pct']:.1f}%) - Expected: {stats['expected_pct']:.1f}%")
    
    summary_stats = customer_generator.get_summary_stats(customers)
    print(f"\n🌍 Geography Split: {summary_stats['geography_split']}")
    print(f"🏭 Industry Split: {summary_stats['industry_split']}")
    
    print(f"\n⏱️  Running {SIMULATION_MONTHS}-month timeline simulation...")
    print("This may take a few minutes...")
    
    results = timeline_simulator.simulate(customers)
    
    print("\n✅ Simulation Complete! Results Summary:")
    print("=" * 50)
    
    summary = timeline_simulator.get_simulation_summary(results)
    
    print(f"📊 Total Customers: {summary['total_customers']}")
    print(f"💔 Churned Customers: {summary['churned_customers']}")
    print(f"🎯 Retention Rate: {summary['retention_rate']}")
    print(f"💰 Total Revenue: {summary['total_revenue']}")
    print(f"📈 Final MRR: ${summary['final_mrr']:,.0f}")
    print(f"📋 Total Usage Events: {summary['total_usage_events']}")
    print(f"💳 Total Billing Transactions: {summary['total_billing_transactions']}")
    
    print(f"\n📊 Final Plan Distribution:")
    for plan, count in summary['plan_distribution'].items():
        print(f"  {plan}: {count} customers")
    
    print("\n📋 Sample Data from Generated Tables:")
    print("-" * 50)
    
    print("\n👥 CUSTOMERS (first 3 rows):")
    print(results['customers'].head(3))
    
    print("\n💳 SUBSCRIPTIONS (first 5 rows):")
    print(results['subscriptions'].head(5))
    
    print("\n📈 USAGE_EVENTS (first 5 rows):")
    print(results['usage_events'].head(5))
    
    print("\n💰 BILLING_TRANSACTIONS (first 5 rows):")
    print(results['billing_transactions'].head(5))
    
    import pandas as pd
    plans_df = pd.DataFrame(PLANS)
    
    print("\n📋 PLANS (static reference data):")
    print(plans_df)
    
    save_to_csv = input("\n💾 Save results to CSV files? (y/n): ").lower().strip()
    
    if save_to_csv == 'y':
        output_dir = 'simulation_output'
        os.makedirs(output_dir, exist_ok=True)
        
        plans_df.to_csv(f'{output_dir}/plans.csv', index=False)
        results['customers'].to_csv(f'{output_dir}/customers.csv', index=False)
        results['subscriptions'].to_csv(f'{output_dir}/subscriptions.csv', index=False)
        results['usage_events'].to_csv(f'{output_dir}/usage_events.csv', index=False)
        results['billing_transactions'].to_csv(f'{output_dir}/billing_transactions.csv', index=False)
        
        print(f"✅ Files saved to {output_dir}/ directory")
        print("  - plans.csv")
        print("  - customers.csv")
        print("  - subscriptions.csv") 
        print("  - usage_events.csv")
        print("  - billing_transactions.csv")
    
    print("\n🎉 Simulation complete! Your data is ready for dashboard analysis.")
    
    return results

def quick_test():
    print("🧪 Running Quick Test Simulation (100 customers, 6 months)")
    
    test_config = {
        'CUSTOMER_ARCHETYPES': {
            'steady_grower': {'distribution_weight': 0.40, 'monthly_growth_rate': 0.15, 'upgrade_threshold': 0.8, 'base_churn_rate': 0.01},
            'seasonal_business': {'distribution_weight': 0.30, 'seasonal_multipliers': {'Q1': 1.3, 'Q2': 0.6, 'Q3': 0.7, 'Q4': 2.0}, 'base_churn_rate': 0.03},
            'price_sensitive': {'distribution_weight': 0.30, 'usage_management': 0.85, 'upgrade_threshold': 0.95, 'base_churn_rate': 0.02}
        },
        'GEOGRAPHIC_MODIFIERS': {
            'US': {'payment_success_rate': 0.97, 'upgrade_propensity': 1.1},
            'EU': {'payment_success_rate': 0.94, 'upgrade_propensity': 0.95}
        },
        'INDUSTRY_MODIFIERS': {
            'ecommerce': {'seasonal_multiplier': 1.5, 'q4_spike': 2.5},
            'saas_tech': {'steady_growth': 1.2, 'enterprise_propensity': 1.4},
            'other': {'seasonal_multiplier': 1.0}
        },
        'PLANS': [
            {'id': 1, 'name': 'Basic', 'monthly_price': 99, 'api_call_limit': 10000, 'data_retention_days': 30, 'max_projects': 3},
            {'id': 2, 'name': 'Pro', 'monthly_price': 299, 'api_call_limit': 50000, 'data_retention_days': 90, 'max_projects': 10},
            {'id': 3, 'name': 'Enterprise', 'monthly_price': 999, 'api_call_limit': 200000, 'data_retention_days': 365, 'max_projects': 50}
        ],
        'SIMULATION_MONTHS': 6,
        'TOTAL_CUSTOMERS': 100,
        'GEOGRAPHIES': ['US', 'EU'],
        'INDUSTRIES': ['ecommerce', 'saas_tech', 'other'],
        'ACQUISITION_CHANNELS': ['organic_search', 'paid_ads', 'referral']
    }
    
    behavior_engine = BehaviorEngine(
        test_config['CUSTOMER_ARCHETYPES'],
        {'PLANS': test_config['PLANS'], 'SIMULATION_MONTHS': test_config['SIMULATION_MONTHS']},
        test_config['GEOGRAPHIC_MODIFIERS'],
        test_config['INDUSTRY_MODIFIERS']
    )
    
    customer_generator = CustomerGenerator(test_config)
    subscription_generator = SubscriptionGenerator(test_config)
    timeline_simulator = TimelineSimulator(behavior_engine, subscription_generator, test_config)
    
    customers = customer_generator.generate(100)
    results = timeline_simulator.simulate(customers)
    summary = timeline_simulator.get_simulation_summary(results)
    
    print(f"✅ Test Results: {summary['total_customers']} customers, {summary['churned_customers']} churned")
    print(f"📊 Generated {len(results['usage_events'])} usage events, {len(results['billing_transactions'])} billing transactions")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Customer Analytics SaaS Simulation')
    parser.add_argument('--test', action='store_true', help='Run quick test with 100 customers')
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    else:
        main()