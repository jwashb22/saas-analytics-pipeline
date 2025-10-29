import pandas as pd
from datetime import datetime, timedelta

class SubscriptionGenerator:
    def __init__(self, config):
        self.plans = {plan['name']: plan for plan in config['PLANS']}
        self.plan_list = config['PLANS']
        self.simulation_months = config.get('SIMULATION_MONTHS', 24)
        
        self.subscription_id_counter = 1
    
    def generate_initial_subscriptions(self, customers_df):

        subscriptions = []
        
        for _, customer in customers_df.iterrows():
            subscription = {
                'id': self.subscription_id_counter,
                'customer_id': customer['id'],
                'plan_id': self._get_plan_id('Basic'),
                'plan_name': 'Basic',
                'start_date': customer['signup_date'],
                'end_date': None,  
                'monthly_price': self._get_plan_price('Basic'),
                'status': 'active',
                'billing_cycle': 'monthly'
            }
            subscriptions.append(subscription)
            self.subscription_id_counter += 1
        
        return pd.DataFrame(subscriptions)
    
    def create_plan_change(self, customer_id, current_subscription, new_plan_name, change_date, change_type='upgrade'):

        ended_subscription = current_subscription.copy()
        ended_subscription['end_date'] = change_date
        ended_subscription['status'] = 'cancelled'
        
        new_subscription = {
            'id': self.subscription_id_counter,
            'customer_id': customer_id,
            'plan_id': self._get_plan_id(new_plan_name),
            'plan_name': new_plan_name,
            'start_date': change_date,
            'end_date': None,
            'monthly_price': self._get_plan_price(new_plan_name),
            'status': 'active',
            'billing_cycle': 'monthly'
        }
        
        self.subscription_id_counter += 1
        return ended_subscription, new_subscription
    
    def cancel_subscription(self, subscription, cancellation_date):

        cancelled_subscription = subscription.copy()
        cancelled_subscription['end_date'] = cancellation_date
        cancelled_subscription['status'] = 'cancelled'
        
        return cancelled_subscription
    
    def get_active_subscription(self, subscriptions_df, customer_id, date):
 
        customer_subs = subscriptions_df[subscriptions_df['customer_id'] == customer_id]
        
        for _, sub in customer_subs.iterrows():
            start_date = datetime.strptime(sub['start_date'], '%Y-%m-%d')
            
            if start_date.date() <= date.date():
                if sub['end_date'] is None or pd.isna(sub['end_date']):
                    return sub 
                else:
                    end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d')
                    if end_date.date() > date.date():
                        return sub  
        
        return None
    
    def get_subscription_history(self, subscriptions_df, customer_id):

        customer_subs = subscriptions_df[subscriptions_df['customer_id'] == customer_id]
        return customer_subs.sort_values('start_date')
    
    def calculate_mrr_impact(self, old_plan_name, new_plan_name):

        old_price = self._get_plan_price(old_plan_name)
        new_price = self._get_plan_price(new_plan_name)
        return new_price - old_price
    
    def get_plan_upgrade_path(self, current_plan):

        upgrade_paths = {
            'Basic': 'Pro',
            'Pro': 'Enterprise',
            'Enterprise': None
        }
        return upgrade_paths.get(current_plan)
    
    def get_plan_downgrade_path(self, current_plan):

        downgrade_paths = {
            'Enterprise': 'Pro',
            'Pro': 'Basic',
            'Basic': None
        }
        return downgrade_paths.get(current_plan)
    
    def _get_plan_id(self, plan_name):
        for plan in self.plan_list:
            if plan['name'] == plan_name:
                return plan['id']
        return None
    
    def _get_plan_price(self, plan_name):
        plan = self.plans.get(plan_name)
        return plan['monthly_price'] if plan else 0
    
    def get_subscription_stats(self, subscriptions_df):
 
        active_subs = subscriptions_df[subscriptions_df['status'] == 'active']
        cancelled_subs = subscriptions_df[subscriptions_df['status'] == 'cancelled']
        
        plan_distribution = subscriptions_df['plan_name'].value_counts()
        
        current_mrr = active_subs['monthly_price'].sum()
        
        stats = {
            'total_subscriptions': len(subscriptions_df),
            'active_subscriptions': len(active_subs),
            'cancelled_subscriptions': len(cancelled_subs),
            'current_mrr': current_mrr,
            'plan_distribution': plan_distribution.to_dict(),
            'average_plan_price': subscriptions_df['monthly_price'].mean()
        }
        
        return stats
    
    def simulate_subscription_lifecycle(self, customers_df, behavior_engine, timeline_months):

        all_subscriptions = []
        current_subscriptions = self.generate_initial_subscriptions(customers_df)
        all_subscriptions.extend(current_subscriptions.to_dict('records'))
        
        customers_dict = customers_df.set_index('id').to_dict('records')
        active_customers = set(customers_df['id'].tolist())
        
        for month in range(1, timeline_months + 1):
            current_date = datetime(2023, 1, 1) + timedelta(days=month * 30)
            
            customers_to_remove = set()
            
            for customer_id in list(active_customers):
                customer = customers_dict[customer_id - 1]  
                
                current_sub_df = pd.DataFrame(all_subscriptions)
                current_sub = self.get_active_subscription(current_sub_df, customer_id, current_date)
                
                if current_sub is None:
                    continue
                
                churn_risk = behavior_engine.calculate_churn_risk(
                    customer, month, [], 0  
                )
                
                if random.random() < churn_risk:
                    cancelled_sub = self.cancel_subscription(current_sub, current_date.strftime('%Y-%m-%d'))
                    
                    for i, sub in enumerate(all_subscriptions):
                        if sub['id'] == current_sub['id']:
                            all_subscriptions[i] = cancelled_sub
                            break
                    
                    customers_to_remove.add(customer_id)
                    continue
                
                current_plan = current_sub['plan_name']
                
                if customer['archetype'] == 'steady_grower' and month % 6 == 0:  
                    target_plan = self.get_plan_upgrade_path(current_plan)
                    if target_plan and random.random() < 0.3:  
                        ended_sub, new_sub = self.create_plan_change(
                            customer_id, current_sub, target_plan, 
                            current_date.strftime('%Y-%m-%d'), 'upgrade'
                        )
                        
                        for i, sub in enumerate(all_subscriptions):
                            if sub['id'] == current_sub['id']:
                                all_subscriptions[i] = ended_sub
                                break
                        all_subscriptions.append(new_sub)
                
                elif customer['archetype'] == 'seasonal_business':
                    quarter = ((month - 1) % 12) // 3 + 1
                    
                    if quarter == 3 and current_plan == 'Basic' and random.random() < 0.4:
                        ended_sub, new_sub = self.create_plan_change(
                            customer_id, current_sub, 'Pro',
                            current_date.strftime('%Y-%m-%d'), 'upgrade'
                        )
                        for i, sub in enumerate(all_subscriptions):
                            if sub['id'] == current_sub['id']:
                                all_subscriptions[i] = ended_sub
                                break
                        all_subscriptions.append(new_sub)
                    
                    elif quarter == 2 and current_plan == 'Pro' and random.random() < 0.3:
                        ended_sub, new_sub = self.create_plan_change(
                            customer_id, current_sub, 'Basic',
                            current_date.strftime('%Y-%m-%d'), 'downgrade'
                        )
                        for i, sub in enumerate(all_subscriptions):
                            if sub['id'] == current_sub['id']:
                                all_subscriptions[i] = ended_sub
                                break
                        all_subscriptions.append(new_sub)
            
            active_customers -= customers_to_remove
        
        return pd.DataFrame(all_subscriptions)


if __name__ == "__main__":
    import random
    
    sample_config = {
        'PLANS': [
            {'id': 1, 'name': 'Basic', 'monthly_price': 99},
            {'id': 2, 'name': 'Pro', 'monthly_price': 299},
            {'id': 3, 'name': 'Enterprise', 'monthly_price': 999}
        ],
        'SIMULATION_MONTHS': 24
    }
    
    sample_customers = pd.DataFrame([
        {'id': 1, 'signup_date': '2023-01-15', 'archetype': 'steady_grower'},
        {'id': 2, 'signup_date': '2023-02-01', 'archetype': 'seasonal_business'},
        {'id': 3, 'signup_date': '2023-01-30', 'archetype': 'price_sensitive'}
    ])
    
    generator = SubscriptionGenerator(sample_config)
    
    initial_subs = generator.generate_initial_subscriptions(sample_customers)
    print("Initial subscriptions:")
    print(initial_subs)
    
    current_sub = initial_subs.iloc[0]
    ended_sub, new_sub = generator.create_plan_change(1, current_sub, 'Pro', '2023-06-01', 'upgrade')
    print(f"\nPlan change:")
    print(f"Ended: {ended_sub}")
    print(f"New: {new_sub}")
    
    stats = generator.get_subscription_stats(initial_subs)
    print(f"\nStats: {stats}")