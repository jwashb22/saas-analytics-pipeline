import pandas as pd
import random
from datetime import datetime, timedelta
from collections import defaultdict

class TimelineSimulator:
    def __init__(self, behavior_engine, subscription_generator, config):
        self.behavior_engine = behavior_engine
        self.subscription_generator = subscription_generator
        self.config = config
        self.simulation_months = config.get('SIMULATION_MONTHS', 24)
        
        self.all_subscriptions = []
        self.all_usage_events = []
        self.all_billing_transactions = []
        
        self.customer_states = {}  
        self.customer_usage_history = defaultdict(list)  
        self.customer_payment_failures = defaultdict(int) 
        
    def simulate(self, customers_df):
    
        print(f"Starting simulation for {len(customers_df)} customers over {self.simulation_months} months...")
        
        self._initialize_customer_states(customers_df)
        
        initial_subscriptions = self.subscription_generator.generate_initial_subscriptions(customers_df)
        self.all_subscriptions.extend(initial_subscriptions.to_dict('records'))
        
        for month in range(1, self.simulation_months + 1):
            print(f"Simulating month {month}/{self.simulation_months}...")
            self._simulate_month(month, customers_df)
        
        print("Updating customer final states...")
        for customer_id, state in self.customer_states.items():
            mask = customers_df['id'] == customer_id
            customers_df.loc[mask, 'status'] = state['status']
            customers_df.loc[mask, 'plan_tier'] = state['current_plan']
        
        churned_count = (customers_df['status'] == 'churned').sum()
        print(f"Updated {churned_count} customers to churned status")
        
        results = {
            'customers': customers_df,
            'subscriptions': pd.DataFrame(self.all_subscriptions),
            'usage_events': pd.DataFrame(self.all_usage_events),
            'billing_transactions': pd.DataFrame(self.all_billing_transactions)
        }
    
        print("Simulation completed!")
        return results
    
    def _initialize_customer_states(self, customers_df):
        for _, customer in customers_df.iterrows():
            self.customer_states[customer['id']] = {
                'status': 'active',
                'current_plan': 'Basic',
                'signup_month': self._get_month_from_signup(customer['signup_date']),
                'churn_month': None,
                'last_usage': None,
                'consecutive_low_usage': 0
            }
    
    def _simulate_month(self, month, customers_df):
        simulation_date = datetime(2023, 1, 1) + timedelta(days=month * 30)
        
        active_customers = [cid for cid, state in self.customer_states.items() 
                          if state['status'] == 'active']
        
        for customer_id in active_customers:
            customer = customers_df[customers_df['id'] == customer_id].iloc[0]
            self._simulate_customer_month(customer, month, simulation_date)
    
    def _simulate_customer_month(self, customer, month, simulation_date):
        customer_id = customer['id']
        state = self.customer_states[customer_id]
        
        if month < state['signup_month']:
            return
        
        current_sub = self._get_customer_current_subscription(customer_id, simulation_date)
        if not current_sub:
            return
            
        current_plan = current_sub['plan_name']
        
        previous_usage = state['last_usage']
        usage = self.behavior_engine.calculate_usage(
            customer, month - state['signup_month'] + 1, current_plan, previous_usage
        )
        
        self._record_usage_event(customer_id, simulation_date, usage, current_plan)
        
        state['last_usage'] = usage
        self.customer_usage_history[customer_id].append(usage)
        
        if usage['usage_percentage'] < 0.3:
            state['consecutive_low_usage'] += 1
        else:
            state['consecutive_low_usage'] = 0
        
        self._check_plan_changes(customer, month, usage, current_sub, simulation_date)
        
        self._generate_billing_transaction(customer, current_sub, simulation_date)
        
        self._check_churn(customer, month, simulation_date)
    
    def _check_plan_changes(self, customer, month, usage, current_subscription, simulation_date):
        customer_id = customer['id']
        current_plan = current_subscription['plan_name']
        
        should_upgrade, target_plan = self.behavior_engine.should_upgrade(
            customer, usage, current_plan, month
        )
        
        if should_upgrade and target_plan != current_plan:
            self._execute_plan_change(customer_id, current_subscription, target_plan, 
                                    simulation_date, 'upgrade')
            return
        
        should_downgrade, target_plan = self.behavior_engine.should_downgrade(
            customer, usage, current_plan, month
        )
        
        if should_downgrade and target_plan != current_plan:
            self._execute_plan_change(customer_id, current_subscription, target_plan, 
                                    simulation_date, 'downgrade')
    
    def _check_churn(self, customer, month, simulation_date):
        customer_id = customer['id']
        state = self.customer_states[customer_id]
        
        usage_history = self.customer_usage_history[customer_id]
        payment_failures = self.customer_payment_failures[customer_id]
        
        churn_probability = self.behavior_engine.calculate_churn_risk(
            customer, month - state['signup_month'] + 1, usage_history, payment_failures
        )
        
        if customer['archetype'] == 'failed_adoption':
            if state['consecutive_low_usage'] >= 2:
                churn_probability = min(churn_probability * 2, 0.8)
        
        elif customer['archetype'] == 'enterprise_pilot':
            tenure_months = month - state['signup_month'] + 1
            if tenure_months <= 3:
                avg_usage = sum(u['usage_percentage'] for u in usage_history) / len(usage_history)
                if avg_usage < 0.4:  
                    churn_probability = 0.4  
                else:
                    churn_probability = 0.05  
        
        if random.random() < churn_probability:
            self._execute_churn(customer_id, simulation_date)
    
    def _execute_plan_change(self, customer_id, current_subscription, new_plan, date, change_type):
        ended_sub, new_sub = self.subscription_generator.create_plan_change(
            customer_id, current_subscription, new_plan, date.strftime('%Y-%m-%d'), change_type
        )
        
        for i, sub in enumerate(self.all_subscriptions):
            if sub['id'] == current_subscription['id']:
                self.all_subscriptions[i] = ended_sub
                break
        
        self.all_subscriptions.append(new_sub)
        
        self.customer_states[customer_id]['current_plan'] = new_plan
        
        price_difference = self.subscription_generator.calculate_mrr_impact(
            current_subscription['plan_name'], new_plan
        )
        
        if price_difference > 0:  
            self._record_billing_transaction(
                customer_id, date, price_difference, 'upgrade', 'success'
            )
        elif price_difference < 0:  
            self._record_billing_transaction(
                customer_id, date, abs(price_difference), 'refund', 'success'
            )
    
    def _execute_churn(self, customer_id, churn_date):
        state = self.customer_states[customer_id]
        state['status'] = 'churned'
        state['churn_month'] = churn_date
        
        current_sub = self._get_customer_current_subscription(customer_id, churn_date)
        if current_sub:
            cancelled_sub = self.subscription_generator.cancel_subscription(
                current_sub, churn_date.strftime('%Y-%m-%d')
            )
            
            for i, sub in enumerate(self.all_subscriptions):
                if sub['id'] == current_sub['id']:
                    self.all_subscriptions[i] = cancelled_sub
                    break
        
        print(f"Customer {customer_id} churned in month {churn_date.strftime('%Y-%m')}")
    
    def _generate_billing_transaction(self, customer, subscription, date):
        customer_id = customer['id']
        
        payment_success_rate = self._get_payment_success_rate(customer)
        payment_succeeded = random.random() < payment_success_rate
        
        if payment_succeeded:
            self.customer_payment_failures[customer_id] = 0  
            status = 'success'
        else:
            self.customer_payment_failures[customer_id] += 1
            status = 'failed'
        
        self._record_billing_transaction(
            customer_id, date, subscription['monthly_price'], 'subscription', status
        )
    
    def _record_usage_event(self, customer_id, date, usage, plan_name):
        available_features = self._get_plan_features(plan_name)
        
        weeks_in_month = 4
        monthly_api_calls = usage['api_calls']
        monthly_data_points = usage['data_points_ingested']
        monthly_queries = usage['queries_executed']
        
        for week in range(weeks_in_month):
            week_date = date + timedelta(days=week * 7)
            

            base_weekly_pct = 0.25  
            variance = random.uniform(-0.05, 0.05)  
            weekly_pct = base_weekly_pct + variance
            
            features_used = random.sample(available_features, 
                                        random.randint(1, min(3, len(available_features))))
            
            usage_event = {
                'customer_id': customer_id,
                'date': week_date.strftime('%Y-%m-%d'),
                'api_calls': int(monthly_api_calls * weekly_pct),
                'data_points_ingested': int(monthly_data_points * weekly_pct),
                'queries_executed': int(monthly_queries * weekly_pct),
                'projects_active': usage['projects_active'],
                'feature_used': ','.join(features_used)
            }
            
            self.all_usage_events.append(usage_event)
    
    def _record_billing_transaction(self, customer_id, date, amount, transaction_type, status):
        """Record a billing transaction."""
        transaction = {
            'customer_id': customer_id,
            'transaction_date': date.strftime('%Y-%m-%d'),
            'amount': amount,
            'type': transaction_type,
            'status': status
        }
        
        self.all_billing_transactions.append(transaction)
    
    def _get_customer_current_subscription(self, customer_id, date):
        """Get customer's active subscription on a specific date."""
        customer_subs = [sub for sub in self.all_subscriptions 
                        if sub['customer_id'] == customer_id]
        
        for sub in reversed(customer_subs):  
            start_date = datetime.strptime(sub['start_date'], '%Y-%m-%d')
            
            if start_date <= date:
                if sub['end_date'] is None:  
                    return sub
                else:
                    end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d')
                    if end_date > date:  
                        return sub
        
        return None
    
    def _get_payment_success_rate(self, customer):
        """Get payment success rate based on customer characteristics."""
        base_rate = 0.95  
        
        if customer['geography'] == 'US':
            base_rate = 0.97
        elif customer['geography'] == 'EU':
            base_rate = 0.94
        
        if customer['archetype'] == 'price_sensitive':
            base_rate *= 0.92  
        elif customer['archetype'] == 'enterprise_pilot':
            base_rate *= 1.02 
        return min(base_rate, 0.99)  
    
    def _get_plan_features(self, plan_name):
        plan_features = {
            'Basic': ['basic_analytics', 'dashboard', 'api_access'],
            'Pro': ['basic_analytics', 'dashboard', 'api_access', 'advanced_analytics', 'custom_reports'],
            'Enterprise': ['basic_analytics', 'dashboard', 'api_access', 'advanced_analytics', 
                         'custom_reports', 'white_label', 'priority_support']
        }
        return plan_features.get(plan_name, ['basic_analytics'])
    
    def _get_month_from_signup(self, signup_date_str):
        signup_date = datetime.strptime(signup_date_str, '%Y-%m-%d')
        simulation_start = datetime(2023, 1, 1)
        days_diff = (signup_date - simulation_start).days
        return max(1, days_diff // 30 + 1)
    
    def get_simulation_summary(self, results):
        customers_df = results['customers']
        subscriptions_df = results['subscriptions']
        usage_df = results['usage_events']
        billing_df = results['billing_transactions']
        
        total_customers = len(customers_df)
        churned_customers = len([s for s in self.customer_states.values() if s['status'] == 'churned'])
        retention_rate = (total_customers - churned_customers) / total_customers * 100
        
        successful_transactions = billing_df[billing_df['status'] == 'success']
        total_revenue = successful_transactions['amount'].sum()
        
        active_subscriptions = subscriptions_df[subscriptions_df['status'] == 'active']
        plan_distribution = active_subscriptions['plan_name'].value_counts()
        
        summary = {
            'total_customers': total_customers,
            'churned_customers': churned_customers,
            'retention_rate': f"{retention_rate:.1f}%",
            'total_revenue': f"${total_revenue:,.0f}",
            'total_usage_events': len(usage_df),
            'total_billing_transactions': len(billing_df),
            'plan_distribution': plan_distribution.to_dict(),
            'final_mrr': active_subscriptions['monthly_price'].sum()
        }
        
        return summary


if __name__ == "__main__":
    print("Timeline Simulator ready for integration!")
    print("Usage: simulator = TimelineSimulator(behavior_engine, subscription_generator, config)")
    print("       results = simulator.simulate(customers_df)")