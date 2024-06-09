import unittest
from unittest.mock import patch

import pandas as pd

from pyeconomics.data.economic_indicators import EconomicIndicators

from pyeconomics.models.monetary_policy.monetary_policy_rules import (
    calculate_policy_rule_estimates,
    calculate_historical_policy_rates,
    plot_historical_rule_estimates
)

from pyeconomics.verbose.monetary_policy_rules import \
    verbose_monetary_policy_rules
from pyeconomics.utils.utils import print_fred_series_names
from pyeconomics.data.model_parameters import MonetaryPolicyRulesParameters


class TestMonetaryPolicyRules(unittest.TestCase):

    @patch(
        'pyeconomics.models.monetary_policy.'
        'monetary_policy_rules.fred_client.get_series_name')
    def test_print_fred_series_names(self, mock_get_series_name):
        mock_get_series_name.side_effect = lambda x: f"Mocked Name for {x}"
        print_fred_series_names()
        self.assertEqual(mock_get_series_name.call_count, 4)

    @patch('pyeconomics.verbose.monetary_policy_rules.datetime')
    def test_print_verbose_output(self, mock_datetime):
        mock_datetime.now.return_value.strftime.return_value = "May 20, 2024"

        estimates = pd.DataFrame({
            'Estimate (%)': [2.5, 3.0, 3.5, 2.0]
        }, index=[
            'Taylor Rule (TR)',
            'Balanced Approach Rule (BAR)',
            'Balanced Approach Shortfalls Rule (BASR)',
            'First Difference Rule (FDR)'
        ])

        indicators = EconomicIndicators(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate',
            current_fed_rate=2.0
        )

        params = MonetaryPolicyRulesParameters(
            as_of_date="May 20, 2024",
            rho=0.9,
            apply_elb=True
        )

        verbose_monetary_policy_rules(estimates, indicators, params)
        self.assertTrue(True)  # No exception should be raised

    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.fred_client.'
        'get_latest_value')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.taylor_rule')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'balanced_approach_rule')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'first_difference_rule')
    def test_calculate_policy_rule_estimates(
        self,
        mock_first_difference_rule,
        mock_balanced_approach_rule,
        mock_taylor_rule,
        mock_get_latest_value
    ):
        mock_get_latest_value.return_value = 2.0
        mock_taylor_rule.return_value = 2.5
        mock_balanced_approach_rule.return_value = 3.0
        mock_first_difference_rule.return_value = 1.5

        indicators = EconomicIndicators(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate'
        )

        params = MonetaryPolicyRulesParameters(
            inflation_target=2.0,
            rho=0.9,
            apply_elb=True
        )

        estimates = calculate_policy_rule_estimates(indicators, params)
        self.assertIsInstance(estimates, pd.DataFrame)
        self.assertEqual(estimates.shape, (4, 1))

    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'fetch_historical_fed_funds_rate')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'historical_taylor_rule')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'historical_balanced_approach_rule')
    @patch(
        'pyeconomics.models.monetary_policy.monetary_policy_rules.'
        'historical_first_difference_rule')
    def test_calculate_historical_policy_rates(
        self,
        mock_historical_first_difference_rule,
        mock_historical_balanced_approach_rule,
        mock_historical_taylor_rule,
        mock_fetch_historical_fed_funds_rate
    ):
        mock_historical_taylor_rule.return_value = pd.DataFrame({
            'TaylorRule': [2.5, 2.6],
            'AdjustedTaylorRule': [2.7, 2.8]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        mock_historical_balanced_approach_rule.return_value = pd.DataFrame({
            'BalancedApproachRule': [3.0, 3.1],
            'BalancedApproachShortfallsRule': [2.7, 2.8],
            'AdjustedBalancedApproachRule': [3.2, 3.3],
            'AdjustedBalancedApproachShortfallsRule': [2.9, 3.0]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        mock_historical_first_difference_rule.return_value = pd.DataFrame({
            'FirstDifferenceRule': [1.5, 1.6],
            'AdjustedFirstDifferenceRule': [1.7, 1.8]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        mock_fetch_historical_fed_funds_rate.return_value = pd.DataFrame({
            'FedRate': [2.0, 2.1]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        indicators = EconomicIndicators(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate'
        )

        params = MonetaryPolicyRulesParameters(
            inflation_target=2.0,
            rho=0.9,
            apply_elb=True
        )

        historical_rates = calculate_historical_policy_rates(indicators, params)
        self.assertIsInstance(historical_rates, pd.DataFrame)
        self.assertEqual(historical_rates.shape, (2, 9))

    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.plt.show')
    def test_plot_historical_policy_rates(self, mock_show):
        historical_policy_rates = pd.DataFrame({
            'TaylorRule': [2.5, 2.6],
            'BalancedApproachRule': [3.0, 3.1],
            'BalancedApproachShortfallsRule': [2.7, 2.8],
            'FirstDifferenceRule': [1.5, 1.6],
            'FedRate': [2.0, 2.1],
            'AdjustedTaylorRule': [2.7, 2.8],
            'AdjustedBalancedApproachRule': [3.2, 3.3],
            'AdjustedBalancedApproachShortfallsRule': [2.9, 3.0],
            'AdjustedFirstDifferenceRule': [1.7, 1.8]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        params = MonetaryPolicyRulesParameters(
            inflation_target=2.0,
            rho=0.9,
            apply_elb=True
        )

        # Test unadjusted plot
        plot_historical_rule_estimates(historical_policy_rates, params)
        self.assertTrue(mock_show.called)

        # Test adjusted plot
        plot_historical_rule_estimates(historical_policy_rates, params)
        self.assertTrue(mock_show.called)

    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'verbose_monetary_policy_rules')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'fred_client.get_latest_value')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'taylor_rule')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'balanced_approach_rule')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'first_difference_rule')
    def test_calculate_policy_rule_estimates_with_none_fed_rate(
        self, mock_first_difference_rule, mock_balanced_approach_rule,
        mock_taylor_rule, mock_get_latest_value,
        mock_verbose_monetary_policy_rules
    ):
        mock_get_latest_value.return_value = 2.0
        mock_taylor_rule.return_value = 2.5
        mock_balanced_approach_rule.return_value = 3.0
        mock_first_difference_rule.return_value = 1.5

        indicators = EconomicIndicators(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate'
        )

        params = MonetaryPolicyRulesParameters(
            inflation_target=2.0,
            rho=0.9,
            apply_elb=True,
            verbose=True  # Ensure verbose is True
        )

        # Test with current_fed_rate as None
        estimates = calculate_policy_rule_estimates(indicators, params)
        self.assertIsInstance(estimates, pd.DataFrame)
        self.assertEqual(estimates.shape, (4, 1))
        self.assertTrue(mock_verbose_monetary_policy_rules.called)

    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'verbose_monetary_policy_rules')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'fred_client.get_latest_value')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'taylor_rule')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'balanced_approach_rule')
    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.'
           'first_difference_rule')
    def test_calculate_policy_rule_estimates_verbose_only(
        self, mock_first_difference_rule, mock_balanced_approach_rule,
        mock_taylor_rule, mock_get_latest_value,
        mock_verbose_monetary_policy_rules
    ):
        mock_get_latest_value.return_value = 2.0
        mock_taylor_rule.return_value = 2.5
        mock_balanced_approach_rule.return_value = 3.0
        mock_first_difference_rule.return_value = 1.5

        indicators = EconomicIndicators(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate'
        )

        params = MonetaryPolicyRulesParameters(
            inflation_target=2.0,
            rho=0.0,
            apply_elb=False,
            verbose=True  # Ensure verbose is True
        )

        # Test with verbose only (rho=0.0 and apply_elb=False)
        estimates = calculate_policy_rule_estimates(indicators, params)
        self.assertIsInstance(estimates, pd.DataFrame)
        self.assertEqual(estimates.shape, (4, 1))
        self.assertTrue(mock_verbose_monetary_policy_rules.called)

        # Reset mock call count before next test
        mock_verbose_monetary_policy_rules.reset_mock()

        # Test with verbose set to False
        params.verbose = False
        estimates = calculate_policy_rule_estimates(indicators, params)
        self.assertIsInstance(estimates, pd.DataFrame)
        self.assertEqual(estimates.shape, (4, 1))
        self.assertFalse(mock_verbose_monetary_policy_rules.called)


if __name__ == '__main__':
    unittest.main()
