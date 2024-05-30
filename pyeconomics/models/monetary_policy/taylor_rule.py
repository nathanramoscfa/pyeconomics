# pyeconomics/models/monetary_policy/taylor_rule.py

import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional

from pyeconomics.api import fetch_historical_fed_funds_rate, fred_client
from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import TaylorRuleParameters
from pyeconomics.utils import verbose_taylor_rule


def taylor_rule(
        indicators: EconomicIndicators = EconomicIndicators(),
        params: TaylorRuleParameters = TaylorRuleParameters(),
        verbose: Optional[bool] = None
) -> float:
    """
    Computes the Taylor Rule interest rate based on economic indicators.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (TaylorRuleParameters): Taylor Rule parameters data class.
        verbose (bool, optional): Whether to print verbose output. If not
            provided, defaults to the value in params. Defaults to None.

    Returns:
        float: Taylor Rule interest rate estimate.
    """
    # Override params.verbose if verbose is explicitly provided
    verbose = verbose if verbose is not None else params.verbose

    # Fetch data if not provided
    indicators.current_inflation_rate = fred_client.get_data_or_fetch(
        indicators.current_inflation_rate,
        indicators.inflation_series_id
    )
    indicators.current_unemployment_rate = fred_client.get_data_or_fetch(
        indicators.current_unemployment_rate,
        indicators.unemployment_rate_series_id
    )
    indicators.natural_unemployment_rate = fred_client.get_data_or_fetch(
        indicators.natural_unemployment_rate,
        indicators.natural_unemployment_series_id
    )
    indicators.long_term_real_interest_rate = fred_client.get_data_or_fetch(
        indicators.long_term_real_interest_rate,
        indicators.real_interest_rate_series_id
    )

    if indicators.current_fed_rate is None:
        indicators.current_fed_rate = fred_client.get_latest_value('DFEDTARU')

    if None in (
        indicators.current_inflation_rate,
        indicators.current_unemployment_rate,
        indicators.natural_unemployment_rate,
        indicators.long_term_real_interest_rate,
        indicators.current_fed_rate
    ):
        raise ValueError("Required economic data is missing.")

    # Calculate gaps and Taylor Rule estimate
    inflation_gap = indicators.current_inflation_rate - params.inflation_target
    unemployment_gap = (indicators.natural_unemployment_rate -
                        indicators.current_unemployment_rate)

    unadjusted_taylor_rule = (
        indicators.long_term_real_interest_rate +
        indicators.current_inflation_rate +
        params.alpha * inflation_gap +
        params.beta * params.okun_factor * unemployment_gap
    )

    # Apply effective lower bound constraint
    if params.apply_elb:
        adjusted_taylor_rule_after_elb = max(unadjusted_taylor_rule, params.elb)
    else:
        adjusted_taylor_rule_after_elb = unadjusted_taylor_rule

    # Apply policy inertia
    adjusted_taylor_rule_after_inertia = (
        params.rho * indicators.current_fed_rate +
        (1 - params.rho) * adjusted_taylor_rule_after_elb
    )

    if verbose:
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
            'unadjusted_taylor_rule': unadjusted_taylor_rule,
            'adjusted_taylor_rule_after_elb': adjusted_taylor_rule_after_elb,
            'adjusted_taylor_rule_after_inertia':
                adjusted_taylor_rule_after_inertia,
            'rho': params.rho,
            'alpha': params.alpha,
            'beta': params.beta,
            'elb': params.elb,
            'apply_elb': params.apply_elb,
            'okun_factor': params.okun_factor
        }
        verbose_taylor_rule(data)

    return round(adjusted_taylor_rule_after_inertia, 2)


def historical_taylor_rule(
        indicators: EconomicIndicators,
        params: TaylorRuleParameters
) -> pd.DataFrame:
    """
    Computes historical Taylor Rule interest rates using economic indicators
    up to the last date with available real interest rate data.

    Args:
        indicators (EconomicIndicators): Economic indicators data class.
        params (TaylorRuleParameters): Taylor Rule parameters data class.

    Returns:
        pd.DataFrame: DataFrame with computed Taylor Rule rates.
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

    # Calculate gaps and Taylor Rule estimation
    data['InflationGap'] = data['Inflation'] - params.inflation_target
    data['UnemploymentGap'] = (data['NaturalUnemploymentRate'] -
                               data['UnemploymentRate'])
    data['TaylorRule'] = (data['RealInterestRate'] +
                          data['Inflation'] +
                          params.alpha * data['InflationGap'] +
                          params.beta * params.okun_factor *
                          data['UnemploymentGap'])

    # Apply effective lower bound constraint
    if params.apply_elb:
        data['AdjustedTaylorRule'] = data['TaylorRule'].apply(
            lambda x: max(x, params.elb))
    else:
        data['AdjustedTaylorRule'] = data['TaylorRule']

    # Apply policy inertia
    data['AdjustedTaylorRule'] = (
            params.rho * data['FedRate'] +
            (1 - params.rho) * data['AdjustedTaylorRule'])

    return data.round(2)


def plot_historical_taylor_rule(
        historical_rule_estimates: pd.DataFrame
) -> None:
    """
    Extract the time range from the data, plot the Taylor Rule estimates and
    the Federal Funds Rate, and return the date range.

    Args:
        historical_rule_estimates (pd.DataFrame): DataFrame containing the
            historical rates including Taylor Rule estimates and the Federal
            Funds Rate.

    Returns:
        None
    """
    # Extracting the time range from the data
    start_date = historical_rule_estimates.dropna().index.min()
    end_date = historical_rule_estimates.dropna().index.max()
    date_range = (f"{start_date.strftime('%B %d, %Y')} to "
                  f"{end_date.strftime('%B %d, %Y')}")

    # Plotting Taylor Rule estimates and the Federal Funds Rate
    historical_rule_estimates[[
        'TaylorRule',
        'AdjustedTaylorRule',
        'FedRate'
    ]].dropna().plot(
        figsize=(10, 5),  # Specifies the figure size
        grid=True  # Enables grid lines for better readability
    )

    plt.title(f'Taylor Rule Estimates and Federal Funds Rate\n{date_range}')
    plt.xlabel('Year')
    plt.ylabel('Interest Rate (%)')
    plt.legend(['Taylor Rule', 'Adjusted Taylor Rule', 'Federal Funds Rate'])

    # Adding the citation as a footnote
    plt.figtext(
        x=0.25,
        y=-0.01,
        s="Data Source: Federal Reserve Economic Data (FRED)",
        ha="center"
    )

    plt.show()  # Display the plot
