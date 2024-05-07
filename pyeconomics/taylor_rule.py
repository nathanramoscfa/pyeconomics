import pandas as pd

from .api import fred_client
from .fred_data import fetch_historical_fed_funds_rate


def taylor_rule(
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
        beta: float = 0.5,
        okun_factor: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False,
        verbose: bool = False
) -> float:
    """
    Computes the Taylor Rule interest rate based on economic indicators.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.
        current_inflation_rate (float): Current inflation rate. If not provided,
            the latest value from FRED is fetched.
        current_unemployment_rate (float): Current unemployment rate. If not
            provided, the latest value from FRED is fetched.
        natural_unemployment_rate (float): Natural unemployment rate. If not
            provided, the latest value from FRED is fetched.
        long_term_real_interest_rate (float): Long-term real interest rate. If
            not provided, the latest value from FRED is fetched.
        fed_rate (float): Current Federal Funds Target Rate. If not provided,
            the latest value from FRED is fetched.
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        okun_factor (float): Multiplier for the unemployment gap.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound
            constraint to the Taylor Rule estimate.
        verbose (bool): Whether to print verbose output.

    Returns:
        float: Taylor Rule interest rate estimate.
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

    # Calculate gaps and Taylor Rule estimate
    inflation_gap = current_inflation_rate - inflation_target
    unemployment_gap = natural_unemployment_rate - current_unemployment_rate

    taylor_est = (long_term_real_interest_rate +
                  current_inflation_rate +
                  alpha * inflation_gap +
                  beta * okun_factor * unemployment_gap)

    if apply_elb:
        taylor_est = max(taylor_est, elb)

    adjusted_taylor_rule_interest_rate = (
            rho * fed_rate + (1 - rho) * taylor_est
    )

    # Verbose output
    if verbose:
        print(f"\n==== Economic Indicators ===================================="
              f"==")
        print(f"Current Inflation:                        "
              f"  {current_inflation_rate:.2f}%")
        print(f"Target Inflation:                         "
              f"  {inflation_target:.2f}%")
        print(f"Current Unemployment Rate:                "
              f"  {current_unemployment_rate:.2f}%")
        print(f"Natural Unemployment Rate:                "
              f"  {natural_unemployment_rate:.2f}%")
        print(f"Long-Term Real Interest Rate:             "
              f"  {long_term_real_interest_rate:.2f}%")
        print(f"Current Fed Rate:                         "
              f"  {fed_rate:.2f}%")
        print(f"\n==== Gaps ==================================================="
              f"==")
        print(f"Inflation Gap:                            "
              f"  {inflation_gap:.2f}%")
        print(f"Unemployment Gap:                         "
              f"  {unemployment_gap:.2f}%")
        print(f"\n==== Taylor Rule ============================================"
              f"==")
        print(f"  Long-Term Real Interest Rate:           "
              f"  {long_term_real_interest_rate:.2f}%")
        print(f"  Current Inflation:                      "
              f"+ {current_inflation_rate:.2f}%")
        print(f"  Alpha * Inflation Gap:                  "
              f"+ {alpha:.2f} * {inflation_gap:.2f}%")
        print(f"  Beta * Okun Factor * Unemployment Gap:  "
              f"+ {beta:.2f} * {okun_factor:.2f} * {unemployment_gap:.2f}%")
        print("---------------------------------------------------------------")
        print(f"  Taylor Rule:                            "
              f"  {taylor_est:.2f}%")
        print(f"\n==== Adjusted Taylor Rule ==================================="
              f"==")
        print("  Adjustment Computation:")
        print(f"  Policy Inertia Coefficient (rho):       "
              f"  {rho:.2f}")
        print(f"  Current Fed Rate:                       "
              f"* {fed_rate:.2f}%")
        print(f"  Adjustment Coefficient (1 - rho):       "
              f"+ (1 - {rho:.2f})")
        print(f"  Taylor Rule Estimate:                   "
              f"* {taylor_est:.2f}%")
        print("---------------------------------------------------------------")
        print(f"  Adjusted Taylor Rule Estimate:          "
              f"  {adjusted_taylor_rule_interest_rate:.2f}%")

    return round(adjusted_taylor_rule_interest_rate, 2)


def historical_taylor_rule(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10',
        inflation_target: float = 2.0,
        alpha: float = 0.5,
        beta: float = 0.5,
        okun_factor: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False
) -> pd.DataFrame:
    """
    Computes historical Taylor Rule interest rates using
    economic indicators up to the last date with available
    real interest rate data.

    Args:
        inflation_series_id (str): Series ID for inflation data.
        unemployment_rate_series_id (str): Series ID for unemployment rate.
        natural_unemployment_series_id (str): Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): Series ID for long-term real
            interest rate.
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        okun_factor (float): Multiplier for the unemployment gap.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound
            constraint to the Taylor Rule estimate.

    Returns:
        pd.DataFrame: DataFrame with computed Taylor Rule rates.
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

    # Calculate gaps and Taylor Rule estimation
    data['InflationGap'] = data['Inflation'] - inflation_target
    data['UnemploymentGap'] = (data['NaturalUnemploymentRate'] -
                               data['UnemploymentRate'])
    data['TaylorRule'] = (data['RealInterestRate'] +
                          data['Inflation'] +
                          alpha * data['InflationGap'] +
                          beta * okun_factor * data['UnemploymentGap'])

    # Apply effective lower bound constraint
    if apply_elb:
        data['AdjustedTaylorRule'] = data['TaylorRule'].apply(
            lambda x: max(x, elb))

    # Apply policy inertia
    data['AdjustedTaylorRule'] = (rho * data['FedRate'] +
                                  (1 - rho) * data['AdjustedTaylorRule'])

    return round(data, 2)
