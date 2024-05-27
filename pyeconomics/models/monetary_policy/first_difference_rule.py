# pyeconomics/models/monetary_policy/first_difference_rule.py

import logging
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional

from pyeconomics.api import fetch_historical_fed_funds_rate, fred_client
from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import FirstDifferenceRuleParameters
from pyeconomics.utils import verbose_first_difference_rule


def first_difference_rule(
        indicators: EconomicIndicators = EconomicIndicators(),
        params: FirstDifferenceRuleParameters = FirstDifferenceRuleParameters(),
        verbose: Optional[bool] = None
) -> float:
    """
    Computes the First-Difference Rule interest rate based on economic
    indicators.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (FirstDifferenceRuleParameters): First Difference Rule
            parameters data class.
        verbose (bool, optional): Whether to print verbose output. If not
            provided, defaults to the value in params. Defaults to None.

    Returns:
        float: First-Difference Rule interest rate estimate.
    """
    try:
        # Override params.verbose if verbose is explicitly provided
        verbose = verbose if verbose is not None else params.verbose

        # Fetch data if not provided
        indicators.current_inflation_rate = fred_client.get_data_or_fetch(
            indicators.current_inflation_rate, indicators.inflation_series_id)
        indicators.current_unemployment_rate = fred_client.get_data_or_fetch(
            indicators.current_unemployment_rate,
            indicators.unemployment_rate_series_id)
        indicators.natural_unemployment_rate = fred_client.get_data_or_fetch(
            indicators.natural_unemployment_rate,
            indicators.natural_unemployment_series_id)
        indicators.current_fed_rate = fred_client.get_data_or_fetch(
            indicators.current_fed_rate, 'DFEDTARU')

        indicators.lagged_unemployment_rate = fred_client.get_data_or_fetch(
            indicators.lagged_unemployment_rate,
            indicators.unemployment_rate_series_id, periods=-12)
        indicators.lagged_natural_unemployment_rate = (
            fred_client.get_data_or_fetch(
                indicators.lagged_natural_unemployment_rate,
                indicators.natural_unemployment_series_id, periods=-4)
        )

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise ValueError("Missing or invalid data")

    # Calculate components of the First-Difference Rule
    inflation_gap = indicators.current_inflation_rate - params.inflation_target
    current_unemployment_gap = (indicators.natural_unemployment_rate -
                                indicators.current_unemployment_rate)
    lagged_unemployment_gap = (indicators.lagged_natural_unemployment_rate -
                               indicators.lagged_unemployment_rate)

    unadjusted_fdr_rule = (indicators.current_fed_rate +
                           params.alpha * inflation_gap +
                           current_unemployment_gap -
                           lagged_unemployment_gap)

    # Apply an effective lower bound (ELB)
    if params.apply_elb:
        adjusted_fdr_rule_after_elb = max(unadjusted_fdr_rule, params.elb)
    else:
        adjusted_fdr_rule_after_elb = unadjusted_fdr_rule

    # Apply policy inertia
    adjusted_fdr_rule_after_inertia = (
        params.rho * indicators.current_fed_rate +
        (1 - params.rho) * adjusted_fdr_rule_after_elb
    )

    # Verbose output
    if verbose:
        data = {
            'current_inflation_rate': indicators.current_inflation_rate,
            'inflation_target': params.inflation_target,
            'current_unemployment_rate': indicators.current_unemployment_rate,
            'lagged_unemployment_rate': indicators.lagged_unemployment_rate,
            'natural_unemployment_rate': indicators.natural_unemployment_rate,
            'lagged_natural_unemployment_rate':
                indicators.lagged_natural_unemployment_rate,
            'current_fed_rate': indicators.current_fed_rate,
            'inflation_gap': inflation_gap,
            'current_unemployment_gap': current_unemployment_gap,
            'lagged_unemployment_gap': lagged_unemployment_gap,
            'unadjusted_fdr_rule': unadjusted_fdr_rule,
            'adjusted_fdr_rule_after_elb': adjusted_fdr_rule_after_elb,
            'adjusted_fdr_rule_after_inertia': adjusted_fdr_rule_after_inertia,
            'alpha': params.alpha,
            'rho': params.rho,
            'elb': params.elb,
            'apply_elb': params.apply_elb
        }
        verbose_first_difference_rule(data)

    return round(adjusted_fdr_rule_after_inertia, 2)


def historical_first_difference_rule(
        indicators: EconomicIndicators,
        params: FirstDifferenceRuleParameters
) -> pd.DataFrame:
    """
    Computes historical First Difference Rule interest rates using economic
    indicators up to the last date with available data.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (FirstDifferenceRuleParameters): First Difference Rule
            parameters data class.

    Returns:
        pd.DataFrame: DataFrame with computed First Difference Rule rates.
    """
    try:
        # Fetch historical data for all series
        inflation = fred_client.fetch_data(indicators.inflation_series_id)
        unemployment_rate = fred_client.fetch_data(
            indicators.unemployment_rate_series_id)
        lagged_unemployment_rate = unemployment_rate.shift(12)
        natural_unemployment = fred_client.fetch_data(
            indicators.natural_unemployment_series_id)
        lagged_natural_unemployment = natural_unemployment.shift(4)
        fed_rate = fetch_historical_fed_funds_rate()

        # Check for missing data
        if (inflation is None or
                unemployment_rate is None or
                lagged_unemployment_rate is None or
                natural_unemployment is None or
                lagged_natural_unemployment is None or
                fed_rate is None):
            raise ValueError("Missing or invalid data")
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        raise ValueError("Missing or invalid data")

    # Combine into a DataFrame
    data = pd.DataFrame({
        'Inflation': inflation,
        'UnemploymentRate': unemployment_rate,
        'LaggedUnemploymentRate': lagged_unemployment_rate,
        'NaturalUnemploymentRate': natural_unemployment,
        'LaggedNaturalUnemploymentRate': lagged_natural_unemployment,
        'FedRate': fed_rate
    })

    # Compute lagged unemployment gap 12 months ago
    data['LaggedUnemploymentGap'] = (
        data['LaggedNaturalUnemploymentRate'] - data['LaggedUnemploymentRate'])

    # Determine the cutoff date based on FedRate data
    fed_rate_date = data['FedRate'].last_valid_index()
    data = data.loc[:fed_rate_date]

    # Handle missing data
    data.ffill(inplace=True)
    data.dropna(inplace=True)

    # Calculate historical gaps and First Difference Rule estimation
    data['InflationGap'] = data['Inflation'] - params.inflation_target
    data['UnemploymentGap'] = (
        data['NaturalUnemploymentRate'] - data['UnemploymentRate'])

    # First Difference Rule Calculation
    data['FirstDifferenceRule'] = (
        data['FedRate'] +
        params.alpha * data['InflationGap'] +
        data['UnemploymentGap'] -
        data['LaggedUnemploymentGap']
    )

    # Apply effective lower bound constraint
    if params.apply_elb:
        data['AdjustedFirstDifferenceRule'] = data['FirstDifferenceRule'].apply(
            lambda x: max(x, params.elb))
    else:
        data['AdjustedFirstDifferenceRule'] = data['FirstDifferenceRule']

    # Apply policy inertia
    data['AdjustedFirstDifferenceRule'] = (
        params.rho * data['FedRate'] +
        (1 - params.rho) * data['AdjustedFirstDifferenceRule'])

    return data.round(2)


def plot_historical_fdr(
        historical_rates: pd.DataFrame
) -> None:
    """
    Extracts the time range from the data and plots the First Difference
    Rule (FDR) estimates along with the Federal Funds Rate.

    Args:
        historical_rates (pd.DataFrame): DataFrame containing the
            historical rates including FDR estimates and the Federal
            Funds Rate.

    Returns:
        None
    """
    # Extracting the time range from the data
    start_date = historical_rates.dropna().index.min()
    end_date = historical_rates.dropna().index.max()
    date_range = (f"{start_date.strftime('%B %d, %Y')} to "
                  f"{end_date.strftime('%B %d, %Y')}")

    # Plotting First Difference Rule (FDR) estimates and the Federal Funds Rate
    historical_rates[['FirstDifferenceRule',
                      'AdjustedFirstDifferenceRule',
                      'FedRate']].dropna().plot(
        figsize=(10, 5),  # Specifies the figure size
        grid=True  # Enables grid lines for better readability
    )

    plt.title(f'First Difference Rule Estimates and Federal Funds Rate\n'
              f'{date_range}')

    plt.xlabel('Year')
    plt.ylabel('Interest Rate (%)')
    plt.legend(['First Difference Rule', 'Adjusted First Difference Rule',
                'Federal Funds Rate'])

    # Adding the citation as a footnote
    plt.figtext(
        x=0.25,
        y=-0.01,
        s="Data Source: Federal Reserve Economic Data (FRED)",
        ha="center"
    )

    plt.show()  # Display the plot
