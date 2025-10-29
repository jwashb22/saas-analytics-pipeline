import random
from datetime import datetime, timedelta

class BehaviorEngine:
    def __init__(self, archetypes_config, business_rules, geographic_modifiers, industry_modifiers):
        self.archetypes = archetypes_config
        self.business_rules = business_rules
        self.geo_modifiers = geographic_modifiers
        self.industry_modifiers = industry_modifiers
        self.plans = {plan['name']: plan for plan in business_rules['PLANS']}

    def get_monthly_behavior(self, customer, month):
        archetype = self.archetypes[customer['archetype']]
        behavior = archetype.copy()
        behavior = self._apply_geographic_modifiers(behavior, customer['geography'])
        behavior = self._apply_industry_modifiers(behavior, customer['industry'])
        behavior = self._apply_seasonal_modifiers(behavior, customer, month)
        behavior = self._apply_tenure_modifiers(behavior, customer, month)
        return behavior
    
    def calculate_usage(self, customer, month, current_plan_name, previous_usage=None):
        behavior = self.get_monthly_behavior(customer, month)
        current_plan = self.plans[current_plan_name]
        base_usage_pct = self._get_base_usage_percentage(customer, behavior)

        if previous_usage:
            growth_rate = behavior.get('monthly_growth_rate', 0)
            growth_variance = behavior.get('growth_variance', 0.05)
            actual_growth = growth_rate + random.uniform(-growth_variance, growth_variance)
            base_usage_pct *= (1 + actual_growth)

        seasonal_mult = self._get_seasonal_multiplier(customer, behavior, month)
        base_usage_pct *= seasonal_mult

        industry_mult = self._get_industry_usage_multiplier(customer, month)
        base_usage_pct *= industry_mult

        api_calls = int(current_plan['api_call_limit'] * base_usage_pct)
        data_points = int(api_calls * random.uniform(1.5, 3.0))
        queries = int(api_calls * 0.1)
        projects = min(random.randint(1, 3), current_plan['max_projects'])

        return {
            'api_calls': max(0, api_calls),
            'data_points_ingested': max(0, data_points),
            'queries_executed': max(0, queries),
            'projects_active': projects,
            'usage_percentage': min(base_usage_pct, 1.5)
        }
    
    def should_upgrade(self, customer, current_usage, current_plan_name, month):
        behavior = self.get_monthly_behavior(customer, month)
        usage_pct = current_usage['usage_percentage']
        upgrade_threshold = behavior.get('upgrade_threshold', 0.8)

        if customer['archetype'] == 'price_sensitive':
            upgrade_threshold = 0.95
        elif customer['archetype'] == 'enterprise_pilot' and month >= 2:
            upgrade_threshold = 0.6

        if usage_pct >= upgrade_threshold:
            target_plan = self._get_target_upgrade_plan(current_plan_name, customer)
            return True, target_plan
        
        return False, current_plan_name
    
    def should_downgrade(self, customer, current_usage, current_plan_name, month):
        if customer['archetype'] != 'seasonal_business':
            return False, current_plan_name
        
        usage_pct = current_usage['usage_percentage']
        quarter = self._get_quarter(month)
        if quarter in ['Q2', 'Q3'] and usage_pct < 0.3:
            if current_plan_name == 'Enterprise':
                return True, 'Pro'
            elif current_plan_name == 'Pro':
                return True, 'Basic'
        
        return False, current_plan_name

    def calculate_churn_risk(self, customer, month, usage_history, payment_failures=0):
        behavior = self.get_monthly_behavior(customer, month)
        base_churn_rate = behavior.get('base_churn_rate', 0.02)

        if customer['archetype'] == 'failed_adoption':
            if month <= 2:
                return behavior.get('early_churn_rate', 0.25)
        elif customer['archetype'] == 'enterprise_pilot':
            if month <= 3:
                avg_usage = self._get_average_usage_trend(usage_history)
                if avg_usage < 0.3:
                    return behavior.get('early_churn_rate', 0.15)
                
        elif customer['archetype'] == 'seasonal_business':
            quarter = self._get_quarter(month)
            seasonal_churn = behavior.get('seasonal_churn_risk', {})
            if quarter in seasonal_churn:
                base_churn_rate *= seasonal_churn[quarter]

        if payment_failures >= 2:
            return 0.95
        elif payment_failures == 1:
            base_churn_rate *= 3

        return min(base_churn_rate, 0.5)
    
    def _apply_geographic_modifiers(self, behavior, geography):
        geo_mods = self.geo_modifiers.get(geography, {})
        modified_behavior = behavior.copy()

        for key, multiplier in geo_mods.items():
            if key in modified_behavior and isinstance(modified_behavior[key], (int, float)):
                modified_behavior[key] *= multiplier

        return modified_behavior
    
    def _apply_industry_modifiers(self, behavior, industry):
        industry_mods = self.industry_modifiers.get(industry, {})
        modified_behavior = behavior.copy()

        for key, multiplier in industry_mods.items():
            if key in modified_behavior and isinstance(modified_behavior[key], (int, float)):
                modified_behavior[key] *= multiplier

        return modified_behavior
    def _apply_seasonal_modifiers(self, behavior, customer, month):
        modified_behavior = behavior.copy()

        if customer['archetype'] == 'seasonal_business':
            quarter = self._get_quarter(month)
            seasonal_mults = behavior.get('seasonal_multipliers', {})
            if quarter in seasonal_mults:
                modified_behavior['seasonal_multiplier'] = seasonal_mults[quarter]

        return modified_behavior
    
    def _apply_tenure_modifiers(self, behavior, customer, month):
        tenure_months = month
        loyalty_factor = min(1.2, 1 + (tenure_months * 0.01))
        modified_behavior = behavior.copy()
        
        if 'base_churn_rate' in modified_behavior:
            modified_behavior['base_churn_rate'] *= (1 / loyalty_factor)

        return modified_behavior
    
    def _get_base_usage_percentage(self, customer, behavior):
        if customer['archetype'] == 'failed_adoption':
            return behavior.get('low_usage_multiplier', 0.2)
        elif customer['archetype'] == 'price_sensitive':
            return behavior.get('usage_management', 0.85)
        else:
            return random.uniform(0.4, 0.7)
        
    def _get_seasonal_multiplier(self, customer, behavior, month):
        return behavior.get('seasonal_multiplier', 1.0)
    
    def _get_industry_usage_multiplier(self, customer, month):
        industry_mods = self.industry_modifiers.get(customer['industry'], {})

        if customer['industry'] == 'ecommerce':
            quarter = self._get_quarter(month)
            if quarter == "Q4":
                return industry_mods.get('q4_spike', 2.5)
            
        elif customer['industry'] == 'marketing_agency':
            quarter = self._get_quarter(month)
            if quarter == 'Q1':
                return industry_mods.get('q1_spike', 1.4)
            
        return industry_mods.get('seasonal_multiplier', 1.0)
    
    def _get_target_upgrade_plan(self, current_plan_name, customer):
        if current_plan_name == 'Basic':
            if customer['archetype'] == 'enterprise_pilot':
                return 'Enterprise'
            return 'Pro'
        elif current_plan_name == 'Pro':
            return 'Enterprise'
        return current_plan_name
    
    def _get_quarter(self, month):
        quarter_map = {
            1: 'Q1', 2: 'Q1', 3: 'Q1',
            4: 'Q2', 5: 'Q2', 6: 'Q2', 
            7: 'Q3', 8: 'Q3', 9: 'Q3',
            10: 'Q4', 11: 'Q4', 12: 'Q4'
        }
        month_in_year = ((month - 1) % 12) + 1
        return quarter_map[month_in_year]
    
    def _get_average_usage_trend(self, usage_history):
        if not usage_history:
            return 0 
        return sum(month.get('usage_percentage', 0) for month in usage_history) / len(usage_history)
    




                                    




        