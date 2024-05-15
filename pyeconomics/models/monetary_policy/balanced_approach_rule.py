import pandas as pd

from pyeconomics.api import fred_client, fetch_historical_fed_funds_rate
from pyeconomics.utils import verbose_balanced_approach_rule


def balanced_approach_rule(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10',
        current_inflation_rate: float = None,
        current_unemployment_rate: float = None,
        natural_unemployment_rate: float = None,
        long_term_real_interest_rate: float = None,
        fed_rate: float = None,
        inflation_target: float = 2.0,
        alpha: float = 0.5,
        beta: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False,
        use_shortfalls_rule: bool = False,
        verbose: bool = False
) -> float:
    """
    Computes the Balanced Approach Rule interest rate based on economic
    indicators.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.
        current_inflation_rate (float): Current inflation rate. If not
            provided, fetched from FRED.
        current_unemployment_rate (float): Current unemployment rate. If not
            provided, fetched from FRED.
        natural_unemployment_rate (float): Natural unemployment rate. If not
            provided, fetched from FRED.
        long_term_real_interest_rate (float): Long-term real interest rate. If
            not provided, fetched from FRED.
        fed_rate (float): Current Federal Funds Target Rate. If not provided,
            fetched from FRED.
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound. If the interest rate estimate is
            below this value, the central bank will set the interest rate to
            this value. Defaults to 0.125.
        apply_elb (bool): Whether to apply the effective lower bound.
        use_shortfalls_rule (bool): Whether to use the Balanced Approach Rule
            with shortfalls. If True, the rule will emphasize only shortfalls
            in employment, not surpassing natural employment levels.
        verbose (bool): Whether to print verbose output.

    Returns:
        float: Balanced Approach Rule interest rate estimate.
    """
    # Fetch data if not provided
    current_inflation_rate = fred_client.get_data_or_fetch(
        current_inflation_rate, inflation_series_id)
    current_unemployment_rate = fred_client.get_data_or_fetch(
        current_unemployment_rate, unemployment_rate_series_id)
    natural_unemployment_rate = fred_client.get_data_or_fetch(
        natural_unemployment_rate, natural_unemployment_series_id)
    long_term_real_interest_rate = fred_client.get_data_or_fetch(
        long_term_real_interest_rate, real_interest_rate_series_id)

    if fed_rate is None:
        fed_rate = fred_client.get_latest_value('DFEDTARU')

    if None in (current_inflation_rate, current_unemployment_rate,
                natural_unemployment_rate, long_term_real_interest_rate,
                fed_rate):
        raise ValueError("Required economic data is missing.")

    # Calculate gaps
    inflation_gap = current_inflation_rate - inflation_target
    unemployment_gap = natural_unemployment_rate - current_unemployment_rate

    # Apply shortfalls rule
    if use_shortfalls_rule:
        unemployment_gap = min(0, unemployment_gap)

    # Balanced Approach Rule estimate
    unadjusted_bar = (long_term_real_interest_rate +
                      current_inflation_rate +
                      alpha * inflation_gap +
                      beta * unemployment_gap)

    # Apply effective lower bound
    if apply_elb:
        adjusted_bar_after_elb = max(unadjusted_bar, elb)
    else:
        adjusted_bar_after_elb = unadjusted_bar

    # Apply policy inertia
    adjusted_bar_after_inertia = (
            (1 - rho) * adjusted_bar_after_elb + rho * fed_rate
    )

    # Verbose output
    if verbose:
        data = {
            'current_inflation_rate': current_inflation_rate,
            'inflation_target': inflation_target,
            'current_unemployment_rate': current_unemployment_rate,
            'natural_unemployment_rate': natural_unemployment_rate,
            'long_term_real_interest_rate': long_term_real_interest_rate,
            'fed_rate': fed_rate,
            'inflation_gap': inflation_gap,
            'unemployment_gap': unemployment_gap,
            'unadjusted_bar_rule': unadjusted_bar,
            'adjusted_bar_after_elb': adjusted_bar_after_elb,
            'adjusted_bar_after_inertia': adjusted_bar_after_inertia,
            'rho': rho,
            'alpha': alpha,
            'beta': beta,
            'elb': elb,
            'apply_elb': apply_elb,
            'use_shortfalls_rule': use_shortfalls_rule
        }
        verbose_balanced_approach_rule(data)

    return round(adjusted_bar_after_inertia, 2)


def historical_balanced_approach_rule(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10',
        inflation_target: float = 2.0,
        alpha: float = 0.5,
        beta: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False,
        use_shortfalls_rule: bool = False
) -> pd.DataFrame:
    """
    Computes historical Balanced Approach Rule interest rates using
    economic indicators up to the last date with available
    real interest rate data.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound. If the interest rate estimate is
            below this value, the central bank will set the interest rate to
            this value. Defaults to 0.125.
        apply_elb (bool): Whether to apply the effective lower bound.
        use_shortfalls_rule (bool): Whether to use the Balanced Approach Rule
            with shortfalls. If True, the rule will emphasize only shortfalls
            in employment, not surpassing natural employment levels.

    Returns:
        pd.DataFrame: DataFrame with computed Balanced Approach Rule rates.
    """
    # Fetch historical data for all series
    inflation = fred_client.fetch_data(inflation_series_id)
    unemployment_rate = fred_client.fetch_data(unemployment_rate_series_id)
    natural_unemployment = fred_client.fetch_data(
        natural_unemployment_series_id)
    real_interest_rate = fred_client.fetch_data(real_interest_rate_series_id)
    fed_rate = fetch_historical_fed_funds_rate()

    # Combine into a DataFrame and ensure data alignment
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
    data['InflationGap'] = data['Inflation'] - inflation_target
    data['UnemploymentGap'] = (data['NaturalUnemploymentRate'] -
                               data['UnemploymentRate'])

    # Apply shortfalls rule
    if use_shortfalls_rule:
        data['UnemploymentGap'] = data['UnemploymentGap'].apply(
            lambda x: min(0, x))
        rule_name = 'BalancedApproachShortfallsRule'
    else:
        rule_name = 'BalancedApproachRule'

    data[rule_name] = (data['RealInterestRate'] +
                       data['Inflation'] +
                       alpha * data['InflationGap'] +
                       beta * data['UnemploymentGap'])

    adjusted_rule_name = 'Adjusted' + rule_name

    # Apply effective lower bound
    if apply_elb:
        data[adjusted_rule_name] = data[rule_name].apply(
            lambda x: max(x, elb))
    else:
        data[adjusted_rule_name] = data[rule_name]

    # Apply policy inertia
    data[adjusted_rule_name] = (
            rho * data['FedRate'] + (1 - rho) * data[adjusted_rule_name])

    return round(data, 2)
