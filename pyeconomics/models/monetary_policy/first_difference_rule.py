import pandas as pd

from pyeconomics.api import fred_client, fetch_historical_fed_funds_rate
from pyeconomics.utils import verbose_first_difference_rule


def first_difference_rule(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        current_inflation_rate: float = None,
        current_unemployment_rate: float = None,
        natural_unemployment_rate: float = None,
        lagged_unemployment_rate: float = None,
        lagged_natural_unemployment_rate: float = None,
        fed_rate: float = None,
        inflation_target: float = 2.0,
        alpha: float = 0.5,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False,
        verbose: bool = False
) -> float:
    """
    Computes the First-Difference Rule interest rate based on economic
    indicators.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        current_inflation_rate (float): Current inflation rate. If None,
            the latest value from FRED is fetched.
        current_unemployment_rate (float): Current unemployment rate. If None,
            the latest value from FRED is fetched.
        natural_unemployment_rate (float): Natural unemployment rate. If None,
            the latest value from FRED is fetched.
        lagged_unemployment_rate (float): Unemployment rate from four periods
            ago.
        lagged_natural_unemployment_rate (float): Natural unemployment rate from
            four periods ago.
        fed_rate (float): Current Federal Funds Target Rate. If None, the latest
            value from FRED is fetched.
        inflation_target (float): Long-term target inflation rate.
        alpha (float): Coefficient for the inflation gap.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to the First-Difference Rule
            estimate. A value of 1.0 would mean full inertia and immediate
            central bank adjustment to the First-Difference Rule estimate.
        elb (float): Effective lower bound for the interest rate.
        apply_elb (bool): Whether to apply the effective lower bound constraint
            to the First-Difference Rule estimate.
        verbose (bool): Whether to print verbose output.
    Returns:
        float: First-Difference Rule interest rate estimate.
    """
    # Fetch current economic data
    current_inflation_rate = fred_client.get_data_or_fetch(
        current_inflation_rate, inflation_series_id)
    current_unemployment_rate = fred_client.get_data_or_fetch(
        current_unemployment_rate, unemployment_rate_series_id)
    natural_unemployment_rate = fred_client.get_data_or_fetch(
        natural_unemployment_rate, natural_unemployment_series_id)
    fed_rate = fred_client.get_data_or_fetch(fed_rate, 'DFEDTARU')

    # Fetch historical data from 12 months ago
    lagged_unemployment_rate = fred_client.get_data_or_fetch(
        lagged_unemployment_rate, unemployment_rate_series_id,
        periods=-12)
    lagged_natural_unemployment_rate = fred_client.get_data_or_fetch(
        lagged_natural_unemployment_rate, natural_unemployment_series_id,
        periods=-12)

    # Calculate components of the First-Difference Rule
    inflation_gap = current_inflation_rate - inflation_target
    current_unemployment_gap = (
            natural_unemployment_rate - current_unemployment_rate)
    lagged_unemployment_gap = (
            lagged_natural_unemployment_rate - lagged_unemployment_rate)

    unadjusted_fdr_rule = (fed_rate +
                           (alpha * inflation_gap) +
                           current_unemployment_gap -
                           lagged_unemployment_gap)

    # Apply an effective lower bound (ELB)
    if apply_elb:
        adjusted_fdr_rule_after_elb = max(unadjusted_fdr_rule, elb)
    else:
        adjusted_fdr_rule_after_elb = unadjusted_fdr_rule

    # Apply policy inertia
    adjusted_fdr_rule_after_inertia = (
            rho * fed_rate + (1 - rho) * adjusted_fdr_rule_after_elb)

    # Verbose output
    if verbose:
        data = {
            'current_inflation_rate': current_inflation_rate,
            'inflation_target': inflation_target,
            'current_unemployment_rate': current_unemployment_rate,
            'lagged_unemployment_rate': lagged_unemployment_rate,
            'natural_unemployment_rate': natural_unemployment_rate,
            'lagged_natural_unemployment_rate':
                lagged_natural_unemployment_rate,
            'fed_rate': fed_rate,
            'inflation_gap': inflation_gap,
            'current_unemployment_gap': current_unemployment_gap,
            'lagged_unemployment_gap': lagged_unemployment_gap,
            'unadjusted_fdr_rule': unadjusted_fdr_rule,
            'adjusted_fdr_rule_after_elb': adjusted_fdr_rule_after_elb,
            'adjusted_fdr_rule_after_inertia': adjusted_fdr_rule_after_inertia,
            'alpha': alpha,
            'rho': rho,
            'elb': elb,
            'apply_elb': apply_elb
        }
        verbose_first_difference_rule(data)

    return round(adjusted_fdr_rule_after_inertia, 2)


def historical_first_difference_rule(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        inflation_target: float = 2.0,
        alpha: float = 0.5,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False
) -> pd.DataFrame:
    """
    Computes historical First Difference Rule interest rates using
    economic indicators up to the last date with available data.

    Args:
        inflation_series_id (str): Series ID for inflation data.
        unemployment_rate_series_id (str): Series ID for unemployment rate.
        natural_unemployment_series_id (str): Series ID for natural
            unemployment rate.
        inflation_target (float): Target inflation rate.
        alpha (float): Coefficient for the inflation gap.
        rho (float): Policy inertia coefficient.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound constraint.

    Returns:
        pd.DataFrame: DataFrame with computed First Difference Rule rates.
    """
    # Fetch historical data for all series
    inflation = fred_client.fetch_data(inflation_series_id)
    unemployment_rate = fred_client.fetch_data(unemployment_rate_series_id)
    lagged_unemployment_rate = unemployment_rate.shift(4)
    natural_unemployment = fred_client.fetch_data(
        natural_unemployment_series_id)
    lagged_natural_unemployment = natural_unemployment.shift(4)
    fed_rate = fetch_historical_fed_funds_rate()

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
            data['LaggedNaturalUnemploymentRate'].shift(12) -
            data['LaggedUnemploymentRate'].shift(12))

    # Determine the cutoff date based on FedRate data
    fed_rate_date = data['FedRate'].last_valid_index()
    data = data.loc[:fed_rate_date]

    # Handle missing data
    data.ffill(inplace=True)
    data.dropna(inplace=True)

    # Calculate historical gaps and First Difference Rule estimation
    data['InflationGap'] = data['Inflation'] - inflation_target
    data['UnemploymentGap'] = (
            data['NaturalUnemploymentRate'] - data['UnemploymentRate'])

    # First Difference Rule Calculation
    data['FirstDifferenceRule'] = (data['FedRate'] +
                                   alpha * data['InflationGap'] +
                                   data['UnemploymentGap'] -
                                   data['LaggedUnemploymentGap'])

    # Apply effective lower bound constraint
    if apply_elb:
        data['AdjustedFirstDifferenceRule'] = data['FirstDifferenceRule'].apply(
            lambda x: max(x, elb))
    else:
        data['AdjustedFirstDifferenceRule'] = data['FirstDifferenceRule']

    # Apply policy inertia
    data['AdjustedFirstDifferenceRule'] = (
            rho * data['FedRate'] +
            (1 - rho) * data['AdjustedFirstDifferenceRule'])

    return data.round(2)
