CUSTOMER_ARCHETYPES = {
    'steady_grower': {
        'distribution_weight': 0.30,
        'monthlly_growth_rate': 0.15,
        'growth_variance': 0.8,
        'upgrade_threshold': 0.8,
        'base_churn_rate': 0.01,
        'seasonal_sensitivity': 0.1,
        'description': 'Consistent growth, reliable upgraders'
    },

    'seasonal_business': {
        'distribution_weight': 0.25,
        'base_usage': 1.0,
        'seasonal_multipliers': {
            'Q1': 1.3, 'Q2': 0.6, 'Q3': 0.7, 'Q4': 2.0
        },
        'upgrade_threshold': 0.7,
        'base_churn_rate': 0.03,
        'seasonal_churn_risk': {'Q2': 2.0, 'Q3': 1.5},
        'description': 'Consistent growth, reliable upgraders'        
    },

    'enterprise_pilot': {
        'distribution_weight': 0.15,
        'trial_period': 3,
        'success_probability': 0.6,
        'rapid_growth_rate': 3.0,
        'early_churn_rate': 0.15,
        'upgrade_velocity': 'fast',
        'description': 'Binary outcome - huge success or quick churn'
    },

    'price_sensitive': {
        'distribution_weight': 0.20,
        'usage_management': 0.85,
        'upgrade_threshold': 0.95,
        'base_churn_rate': 0.02,
        'price_increase_churn_multiplier': 2.0,
        'plan_preference': 'Basic',
        'description': 'High engagement, low revenue, price-sensitive'
    },

    'failed_adoption': {
        'distribution_weight': 0.10,
        'low_usage_multiplier': 0.2,
        'churn_timeline': 2,
        'early_churn_rate': 0.25,
        'engagement_decline': 0.5,
        'description': 'Low usage from start, quick churn'
    }
}

GEOGRAPHIC_MODIFIERS = {
    'US': {
        'payment_success_rate': 0.97,
        'seasonal_intensity': 1.2,
        'upgrade_propensity': 1.1
    },
    'EU': {
        'payment_success_rate': 0.94,
        'seasonal_intensity': 0.9,
        'upgrade_propensity': 0.95,
        'gdpr_churn_factor': 1.05
    }
}

INDUSTRY_MODIFIERS = {
    'ecomerce': {
        'seasonal_multiplier': 1.5,
        'q4_spike': 2.5,
        'preferred_features': ['dashboard', 'api_access']
    },
    'saas_tech': {
        'steady_growth': 1.2,
        'feature_adoption_rate': 1.3,
        'enterprise_propensity': 1.4
    },
    'financial_services': {
        'compliance_features': True,
        'data_retention_importance': 2.0,
        'enterprise_propensity': 1.6
    },
    'marketing_agency': {
        'usage_volatility': 1.6,
        'seasonal_multiplier': 1.2,
        'q1_spike': 1.4,
        'price_sensitivity': 1.3,
        'feature_adoption_rate': 1.2
    },

    'healthcare': {
        'steady_growth': 1.1,
        'seasonal_multiplier': 0.8,
        'enterprise_propensity': 1.4,
        'churn_resistance': 1.3,
        'feature_adoption_rate': 0.8
    },

    'manufacturing': {
        'usage_consistency': 1.3,
        'seasonal_multiplier': 0.9,
        'price_sensitivity': 1.4,
        'upgrade_threshold_modifier': 1.2,
        'enterprise_propensity': 0.7
    },

    'other': {
        'seasonal_multiplier': 1.0,
        'usage_volatility': 1.0,
        'price_sensitivity': 1.0,
        'feature_adoption_rate': 1.0,
        'enterprise_propensity': 1.0
    }
}