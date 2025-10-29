import random
import pandas as pd
from datetime import datetime, timedelta

class CustomerGenerator:
    def __init__(self, config):
        self.archetypes = config['CUSTOMER_ARCHETYPES']
        self.geographies = config['GEOGRAPHIES']
        self.industries = config['INDUSTRIES']
        self.acquisition_channels = config['ACQUISITION_CHANNELS']
        self.simulation_months = config.get('SIMULATION_MONTHS', 24)

        self.archetype_weights = []
        self.archetype_names = []
        for name, archetype in self.archetypes.items():
            self.archetype_names.append(name)
            self.archetype_weights.append(archetype['distribution_weight'])

    def generate(self, num_customers=1000):
        customers = []
        
        for i in range(num_customers):
            customer = {
                'id': i + 1,
                'company_name': self._generate_company_name(),
                'signup_date': self._generate_signup_date(),
                'plan_tier': 'Basic',
                'geography': self._assign_geography(),
                'industry': self._assign_industry(),
                'acquisition_channel': self._assign_acquisition_channel(),
                'status': 'active',
                'archetype': self._assign_archetype()
            }
            customers.append(customer)

        return pd.DataFrame(customers)
    
    def _assign_archetype(self):
        return random.choices(self.archetype_names, weights=self.archetype_weights)[0]
    
    def _assign_geography(self):
        return random.choices(['US', 'EU'], weights=[0.6, 0.4])[0]
    
    def _assign_industry(self):
        industries = [
            'ecommerce', 'saas_tech', 'financial_services', 'marketing_agency',
            'healthcare', 'manufacturing', 'other'            
        ]
        weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]
        return random.choices(industries, weights=weights)[0]
    
    def _assign_acquisition_channel(self):
        channels = [
            'organic_search', 'paid_ads', 'referral',
            'direct', 'partner', 'content_marketing'
        ]
        weights = [0.30, 0.25, 0.15, 0.15, 0.10, 0.05]
        return random.choices(channels, weights=weights)[0]
    
    def _generate_signup_date(self):
        max_signup_month = 6

        month_weights = self._get_signup_seasonality()

        signup_month = random.choices(
            range(1, max_signup_month + 1),
            weights=month_weights[:max_signup_month]
        )[0]

        start_date = datetime(2023, 1, 1)
        signup_date = start_date + timedelta(days=(signup_month - 1) * 30 + random.randint(0, 29))

        return signup_date.strftime('%Y-%m-%d')
    
    def _get_signup_seasonality(self):
        base_weight = 1.0
        weights = [base_weight] * 24
        
        for i in range(0, 24, 12):
            if i < len(weights):
                weights[i] = 1.3

        for i in range(8, 24, 12):
            if i < len(weights):
                weights[i] = 1.2

        return weights
    
    def _generate_company_name(self):
        prefixes = [
            'Apex', 'Nova', 'Prime', 'Elite', 'Summit', 'Vertex', 'Zenith', 'Alpha',
            'Beta', 'Delta', 'Gamma', 'Meta', 'Ultra', 'Super', 'Mega', 'Hyper',
            'Smart', 'Quick', 'Fast', 'Rapid', 'Swift', 'Agile', 'Dynamic', 'Global',
            'Digital', 'Cyber', 'Tech', 'Data', 'Cloud', 'Web', 'Mobile', 'Auto'            
        ]

        suffixes = [
            'Solutions', 'Systems', 'Technologies', 'Dynamics', 'Innovations',
            'Labs', 'Works', 'Studio', 'Group', 'Corp', 'Inc', 'LLC', 'Ltd',
            'Enterprises', 'Ventures', 'Partners', 'Associates', 'Consulting',
            'Services', 'Analytics', 'Intelligence', 'Insights', 'Data', 'Hub'           
        ]

        if random.random() < 0.3:
            return random.choice(prefixes + ['Acme', 'Pioneer', 'Fusion', 'Nexus', 'Quantum'])
        else:
            return f"{random.choice(prefixes)} {random.choice(suffixes)}"
        
    def get_archetype_distribution(self, customers_df):
        actual_dist = customers_df['archetype'].value_counts()
        total = len(customers_df)
        distribution_report = {}

        for archetype, config in self.archetypes.items():
            expected_pct = config['distribution_weight'] * 100
            actual_count = actual_dist.get(archetype, 0)
            actual_pct = (actual_count / total) * 100

            distribution_report[archetype] = {
                'expected_pct': expected_pct,
                'actual_count': actual_count,
                'actual_pct': actual_pct,
                'difference': actual_pct - expected_pct
            }

        return distribution_report
    
    def get_summary_stats(self, customers_df):
        
        return {
            'total_customers': len(customers_df),
            'geography_split': customers_df['geography'].value_counts().to_dict(),
            'industry_split': customers_df['industry'].value_counts().to_dict(),
            'channel_split': customers_df['acquisition_channel'].value_counts().to_dict(),
            'archetype_split': customers_df['archetype'].value_counts().to_dict()
        }
    

if __name__ == "__main__":
    sample_config = {
        'CUSTOMER_ARCHETYPES': {
            'steady_grower': {'distribution_weight': 0.30},
            'seasonal_business': {'distribution_weight': 0.25},
            'enterprise_pilot': {'distribution_weight': 0.15},
            'price_sensitive': {'distribution_weight': 0.20},
            'failed_adoption': {'distribution_weight': 0.10}        
        },
        'GEOGRAPHIES': ['US', 'EU'],
        'INDUSTRIES': ['ecommerce', 'saas_tech', 'financial_services', 'marketing_agency', 'healthcare', 'manufacturing', 'other'],
        'ACQUISITION_CHANNELS': ['organic_search', 'paid_ads', 'referral', 'direct', 'partner', 'content_marketing'],
        'SIMULATION_MONTHS': 24
    }

    generator = CustomerGenerator(sample_config)
    customers = generator.generate(1000)

    print("Generated", len(customers), "customers")
    print("\nArchetype Distribution:")
    dist_report = generator.get_archetype_distribution(customers)
    for archetype, stats in dist_report.items():
        print(f"{archetype}: {stats['actual_count']} ({stats['actual_pct']:.1f}%) - Expected: {stats['expected_pct']:.1f}%")

    print(customers.head())

    