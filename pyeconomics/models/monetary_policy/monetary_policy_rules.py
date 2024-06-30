# pyeconomics/models/monetary_policy/monetary_policy_rules.py

import copy
import matplotlib.pyplot as plt
import pandas as pd

from .balanced_approach_rule import (
    balanced_approach_rule, historical_balanced_approach_rule)
from .taylor_rule import taylor_rule, historical_taylor_rule
from .first_difference_rule import (
    first_difference_rule, historical_first_difference_rule)
from ...api import fred_client
from ...data.economic_indicators import EconomicIndicators
from ...data.model_parameters import (
    BalancedApproachRuleParameters,
    FirstDifferenceRuleParameters,
    TaylorRuleParameters,
    MonetaryPolicyRulesParameters
)
from ...verbose.monetary_policy_rules import verbose_monetary_policy_rules
from ...utils.fred import fetch_historical_fed_funds_rate


def calculate_policy_rule_estimates(
    indicators: EconomicIndicators = EconomicIndicators(),
    params: MonetaryPolicyRulesParameters = MonetaryPolicyRulesParameters()
) -> pd.DataFrame:
    """
    Calculate and return the monetary policy rule estimates as a DataFrame.

    Args:
        indicators (EconomicIndicators): Instance containing economic
            indicators.
        params (MonetaryPolicyRulesParameters): Instance containing the policy
            rule parameters.

    Returns:
        pd.DataFrame: DataFrame containing the policy estimates.
    """
    # Fetch the current Federal Funds Rate if not provided
    if indicators.current_fed_rate is None:
        indicators.current_fed_rate = fred_client.get_latest_value('DFEDTARU')

    tr_params = TaylorRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    fdr_params = FirstDifferenceRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    bar_params = BalancedApproachRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    # Current Balanced Approach (Shortfalls) Rule calculation using FRED data
    basr_params = copy.deepcopy(bar_params)  # Make a deep copy
    basr_params.use_shortfalls_rule = True

    # Current Taylor Rule calculation using FRED data
    tr_estimate = taylor_rule(indicators, tr_params)

    # Current Balanced Approach Rule calculation using FRED data
    bar_estimate = balanced_approach_rule(indicators, bar_params)

    # Current Balanced Approach (Shortfalls) Rule calculation using FRED data
    basr_estimate = balanced_approach_rule(indicators, basr_params)

    # Current First Difference Rule calculation using FRED data
    fdr_estimate = first_difference_rule(indicators, fdr_params)

    # Compile the estimates into a DataFrame
    estimates = pd.DataFrame(
        data=[
            tr_estimate,
            bar_estimate,
            basr_estimate,
            fdr_estimate,
        ],
        columns=['Estimate (%)'],
        index=[
            'Taylor Rule (TR)',
            'Balanced Approach Rule (BAR)',
            'Balanced Approach Shortfalls Rule (BASR)',
            'First Difference Rule (FDR)'
        ]
    )

    if params.verbose:
        verbose_monetary_policy_rules(estimates, indicators, params)
    return estimates


def calculate_historical_policy_rates(
    indicators: EconomicIndicators = EconomicIndicators(),
    params: MonetaryPolicyRulesParameters = MonetaryPolicyRulesParameters()
) -> pd.DataFrame:
    """
    Calculate and return the historical monetary policy rule estimates as a
    DataFrame.

    Args:
        indicators (EconomicIndicators): Instance containing economic
            indicators.
        params (MonetaryPolicyRulesParameters): Instance containing the policy
            rule parameters.

    Returns:
        pd.DataFrame: DataFrame containing the historical policy estimates.
    """
    tr_params = TaylorRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    bar_params = BalancedApproachRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    fdr_params = FirstDifferenceRuleParameters(
        inflation_target=params.inflation_target,
        rho=params.rho,
        elb=params.elb,
        apply_elb=params.apply_elb
    )

    # Historical Taylor Rule calculation using FRED data
    historical_tr = historical_taylor_rule(indicators, tr_params)

    # Historical BAR calculation using FRED data
    historical_bar = historical_balanced_approach_rule(indicators, bar_params)

    # Historical BASR calculation using FRED data
    basr_params = bar_params
    basr_params.use_shortfalls_rule = True
    historical_basr = historical_balanced_approach_rule(
        indicators, basr_params)

    # Historical First Difference Rule (FDR) calculation using FRED data
    historical_fdr = historical_first_difference_rule(indicators, fdr_params)

    # Combine historical rates into a single DataFrame
    historical_policy_rates = pd.concat([
        historical_tr['TaylorRule'],
        historical_tr['AdjustedTaylorRule'],
        historical_bar['BalancedApproachRule'],
        historical_bar['AdjustedBalancedApproachRule'],
        historical_basr['BalancedApproachShortfallsRule'],
        historical_basr['AdjustedBalancedApproachShortfallsRule'],
        historical_fdr['FirstDifferenceRule'],
        historical_fdr['AdjustedFirstDifferenceRule'],
        fetch_historical_fed_funds_rate()
    ], axis=1)

    return historical_policy_rates


def plot_historical_rule_estimates(
        historical_policy_rates: pd.DataFrame,
        params: MonetaryPolicyRulesParameters
) -> None:
    """
    Extract the time range from the data, plot the (adjusted or unadjusted)
    policy rules and the Federal Funds Rate, and return the date range.

    Args:
        historical_policy_rates (pd.DataFrame): DataFrame containing the
            historical policy rates.
        params (MonetaryPolicyRulesParameters): Instance containing the policy
            rule parameters.

    Returns:
        None
    """
    # Determine which columns to use based on the adjusted parameter
    adjusted = params.rho > 0.0 or params.apply_elb
    if adjusted:
        columns = [
            'AdjustedTaylorRule',
            'AdjustedBalancedApproachRule',
            'AdjustedBalancedApproachShortfallsRule',
            'AdjustedFirstDifferenceRule',
            'FedRate'
        ]
    else:
        columns = [
            'TaylorRule',
            'BalancedApproachRule',
            'BalancedApproachShortfallsRule',
            'FirstDifferenceRule',
            'FedRate'
        ]

    # Extracting the time range from the data
    start_date = historical_policy_rates.dropna().index.min()
    end_date = historical_policy_rates.dropna().index.max()
    date_range = (f"{start_date.strftime('%B %d, %Y')} to "
                  f"{end_date.strftime('%B %d, %Y')}")

    # Plotting Policy Rules and the Federal Funds Rate
    historical_policy_rates[columns].dropna().plot(
        figsize=(10, 5),  # Specifies the figure size
        grid=True  # Enables grid lines for better readability
    )

    title_prefix = 'Adjusted' if adjusted else 'Monetary'
    plt.title(
        f'{title_prefix} Policy Rule Estimates and Federal Funds Rate\n'
        f'{date_range}')
    plt.xlabel('Year')
    plt.ylabel('Interest Rate (%)')
    plt.legend([
        'Adjusted Taylor Rule' if adjusted
        else 'Taylor Rule',
        'Adjusted Balanced Approach Rule' if adjusted
        else 'Balanced Approach Rule',
        'Adjusted Balanced Approach (Shortfalls) Rule' if adjusted
        else 'Balanced Approach (Shortfalls) Rule',
        'Adjusted First Difference Rule' if adjusted
        else 'First Difference Rule',
        'Federal Funds Rate'
    ])

    # Adding the citation as a footnote
    plt.figtext(
        x=0.25,
        y=-0.01,
        s="Data Source: Federal Reserve Economic Data (FRED)",
        ha="center"
    )

    plt.show()  # Display the plot
