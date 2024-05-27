# Import standard libraries
import os
import sys

# Configure system path
sys.path.insert(0, os.path.abspath('../../'))

# Import third-party libraries
import matplotlib.pyplot as plt
import pandas as pd

# Import pyeconomics modules
from pyeconomics.api import fetch_historical_fed_funds_rate, fred_client
from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import BalancedApproachRuleParameters
from pyeconomics.utils import verbose_balanced_approach_rule


def balanced_approach_rule(
        indicators: EconomicIndicators,
        params: BalancedApproachRuleParameters
) -> float:
    """
    Computes the Balanced Approach Rule interest rate based on economic
    indicators.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (BalancedApproachRuleParameters): Balanced Approach Rule
            parameters data class.

    Returns:
        float: Balanced Approach Rule interest rate estimate.
    """
    # Fetch data if not provided
    indicators.current_inflation_rate = fred_client.get_data_or_fetch(
        indicators.current_inflation_rate, indicators.inflation_series_id)
    indicators.current_unemployment_rate = fred_client.get_data_or_fetch(
        indicators.current_unemployment_rate,
        indicators.unemployment_rate_series_id)
    indicators.natural_unemployment_rate = fred_client.get_data_or_fetch(
        indicators.natural_unemployment_rate,
        indicators.natural_unemployment_series_id)
    indicators.long_term_real_interest_rate = fred_client.get_data_or_fetch(
        indicators.long_term_real_interest_rate,
        indicators.real_interest_rate_series_id)

    if indicators.current_fed_rate is None:
        indicators.current_fed_rate = fred_client.get_latest_value('DFEDTARU')

    if None in (indicators.current_inflation_rate,
                indicators.current_unemployment_rate,
                indicators.natural_unemployment_rate,
                indicators.long_term_real_interest_rate,
                indicators.current_fed_rate):
        raise ValueError("Required economic data is missing.")

    # Calculate gaps and Balanced Approach Rule estimate
    inflation_gap = indicators.current_inflation_rate - params.inflation_target
    unemployment_gap = (indicators.natural_unemployment_rate -
                        indicators.current_unemployment_rate)

    # Apply shortfalls rule
    if params.use_shortfalls_rule:
        unemployment_gap = min(0.0, unemployment_gap)

    unadjusted_rate = (indicators.long_term_real_interest_rate +
                       indicators.current_inflation_rate +
                       params.alpha * inflation_gap +
                       params.beta * unemployment_gap)

    # Apply effective lower bound constraint
    if params.apply_elb:
        adjusted_rate_after_elb = max(unadjusted_rate, params.elb)
    else:
        adjusted_rate_after_elb = unadjusted_rate

    # Apply policy inertia
    adjusted_rate_after_inertia = (
            params.rho * indicators.current_fed_rate +
            (1 - params.rho) * adjusted_rate_after_elb
    )

    # Verbose output
    if params.verbose:
        data = {
            'current_inflation_rate': indicators.current_inflation_rate,
            'inflation_target': params.inflation_target,
            'current_unemployment_rate': indicators.current_unemployment_rate,
            'natural_unemployment_rate': indicators.natural_unemployment_rate,
            'long_term_real_interest_rate':
                indicators.long_term_real_interest_rate,
            'current_fed_rate': indicators.current_fed_rate,
            'inflation_gap': inflation_gap,
            'unemployment_gap': unemployment_gap,
            'unadjusted_rate': unadjusted_rate,
            'adjusted_rate_after_elb': adjusted_rate_after_elb,
            'adjusted_rate_after_inertia': adjusted_rate_after_inertia,
            'rho': params.rho,
            'alpha': params.alpha,
            'beta': params.beta,
            'elb': params.elb,
            'apply_elb': params.apply_elb,
            'use_shortfalls_rule': params.use_shortfalls_rule
        }
        verbose_balanced_approach_rule(data)

    return round(adjusted_rate_after_inertia, 2)


def historical_balanced_approach_rule(
        indicators: EconomicIndicators,
        params: BalancedApproachRuleParameters
) -> pd.DataFrame:
    """
    Computes historical Balanced Approach Rule interest rates using economic
    indicators up to the last date with available real interest rate data.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (BalancedApproachRuleParameters): Balanced Approach Rule
            parameters data class.

    Returns:
        pd.DataFrame: DataFrame with computed Balanced Approach Rule rates.
    """
    # Fetch historical data for all series
    inflation = fred_client.fetch_data(indicators.inflation_series_id)
    unemployment_rate = fred_client.fetch_data(
        indicators.unemployment_rate_series_id)
    natural_unemployment = fred_client.fetch_data(
        indicators.natural_unemployment_series_id)
    real_interest_rate = fred_client.fetch_data(
        indicators.real_interest_rate_series_id)
    fed_rate = fetch_historical_fed_funds_rate()

    # Combine into a DataFrame
    data = pd.DataFrame({
        'Inflation': inflation,
        'UnemploymentRate': unemployment_rate,
        'NaturalUnemploymentRate': natural_unemployment,
        'RealInterestRate': real_interest_rate,
        'FedRate': fed_rate
    })

    # Determine the cutoff date based on RealInterestRate data
    last_real_interest_date = data['RealInterestRate'].last_valid_index()
    data = data.loc[:last_real_interest_date]

    # Handle missing data
    data.ffill(inplace=True)
    data.dropna(inplace=True)

    # Calculate gaps and Balanced Approach Rule estimation
    data['InflationGap'] = data['Inflation'] - params.inflation_target
    data['UnemploymentGap'] = (data['NaturalUnemploymentRate'] -
                               data['UnemploymentRate'])

    # Apply shortfalls rule
    if params.use_shortfalls_rule:
        data['UnemploymentGap'] = data['UnemploymentGap'].apply(
            lambda x: min(0, x))
        rule_name = 'BalancedApproachShortfallsRule'
    else:
        rule_name = 'BalancedApproachRule'

    data[rule_name] = (data['RealInterestRate'] +
                       data['Inflation'] +
                       params.alpha * data['InflationGap'] +
                       params.beta * data['UnemploymentGap'])

    adjusted_rule_name = 'Adjusted' + rule_name

    # Apply effective lower bound
    if params.apply_elb:
        data[adjusted_rule_name] = data[rule_name].apply(
            lambda x: max(x, params.elb))
    else:
        data[adjusted_rule_name] = data[rule_name]

    # Apply policy inertia
    data[adjusted_rule_name] = (
            params.rho * data['FedRate'] +
            (1 - params.rho) * data[adjusted_rule_name])

    return data.round(2)


def plot_historical_bar_basr_rule(
    historical_rates: pd.DataFrame,
    adjusted: bool = False
) -> None:
    """
    Extract the time range from the data, plot either the Balanced Approach
    Rule (BAR) and Balanced Approach Shortfalls Rule (BASR) estimates or their
    adjusted versions along with the Federal Funds Rate, and display the date
    range in the plot title.

    Args:
        historical_rates (pd.DataFrame): DataFrame containing the historical
            rates including BAR, BASR estimates, and the Federal Funds Rate,
            along with their adjusted versions if applicable.
        adjusted (bool): A flag to determine whether to plot the adjusted or
            unadjusted rates.

    Returns:
        None
    """
    if adjusted:
        columns = [
            'AdjustedBalancedApproachRule',
            'AdjustedBalancedApproachShortfallsRule',
            'FedRate'
        ]
        title_prefix = "Adjusted "
    else:
        columns = [
            'BalancedApproachRule',
            'BalancedApproachShortfallsRule',
            'FedRate'
        ]
        title_prefix = ""

    # Select relevant data
    plot_data = historical_rates[columns].copy()

    # Extracting the time range from the data
    start_date = plot_data.dropna().index.min()
    end_date = plot_data.dropna().index.max()
    date_range = (f"{start_date.strftime('%B %d, %Y')} to "
                  f"{end_date.strftime('%B %d, %Y')}")

    # Plotting BAR and BASR Rule estimates and the Federal Funds Rate
    plot_data.dropna().plot(
        figsize=(10, 5),  # Specifies the figure size
        grid=True  # Enables grid lines for better readability
    )

    plt.title(f'{title_prefix}BAR and BASR Rule Estimates and Federal Funds '
              f'Rate\n{date_range}')
    plt.xlabel('Year')
    plt.ylabel('Interest Rate (%)')
    plt.legend([
        f'{title_prefix}BAR Rule',
        f'{title_prefix}BASR Rule',
        'Federal Funds Rate']
    )

    # Adding the citation as a footnote
    plt.figtext(
        x=0.25,
        y=-0.01,
        s="Data Source: Federal Reserve Economic Data (FRED)",
        ha="center"
    )

    plt.show()  # Display the plot
