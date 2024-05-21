# pyeconomics/tests/test_monetary_policy_rules.py
import unittest
from unittest.mock import patch

import pandas as pd

from pyeconomics.models.monetary_policy.monetary_policy_rules import (
    print_fred_series_names, print_verbose_output,
    calculate_policy_rule_estimates,
    calculate_historical_policy_rates, plot_historical_policy_rates
)


class TestMonetaryPolicyRules(unittest.TestCase):

    @patch(
        'pyeconomics.models.monetary_policy.'
        'monetary_policy_rules.fred_client.get_series_name')
    def test_print_fred_series_names(self, mock_get_series_name):
        mock_get_series_name.side_effect = lambda x: f"Mocked Name for {x}"
        print_fred_series_names()
        self.assertEqual(mock_get_series_name.call_count, 4)

    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.datetime')
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
        print_verbose_output(estimates, 2.0)
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
            self, mock_first_difference_rule, mock_balanced_approach_rule,
            mock_taylor_rule, mock_get_latest_value):
        mock_get_latest_value.return_value = 2.0
        mock_taylor_rule.return_value = 2.5
        mock_balanced_approach_rule.return_value = 3.0
        mock_first_difference_rule.return_value = 1.5

        estimates = calculate_policy_rule_estimates(verbose=True)
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
            self, mock_historical_first_difference_rule,
            mock_historical_balanced_approach_rule,
            mock_historical_taylor_rule, mock_fetch_historical_fed_funds_rate):
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

        historical_rates = calculate_historical_policy_rates(rho=0.7,
                                                             apply_elb=True)
        self.assertIsInstance(historical_rates, pd.DataFrame)
        self.assertEqual(historical_rates.shape,
                         (2, 9))  # Adjusted for new columns

    @patch('pyeconomics.models.monetary_policy.monetary_policy_rules.plt.show')
    def test_plot_historical_policy_rates(self, mock_show):
        historical_policy_rates = pd.DataFrame({
            'TaylorRule': [2.5, 2.6],
            'BalancedApproachRule': [3.0, 3.1],
            'BalancedApproachShortfallsRule': [2.7, 2.8],
            'FirstDifferenceRule': [1.5, 1.6],
            'FedRate': [2.0, 2.1]
        }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

        plot_historical_policy_rates(historical_policy_rates)
        self.assertTrue(mock_show.called)


if __name__ == '__main__':
    unittest.main()
