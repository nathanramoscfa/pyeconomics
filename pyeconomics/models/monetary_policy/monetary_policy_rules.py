# pyeconomics/models/monetary_policy/monetary_policy_rules.py
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from .taylor_rule import taylor_rule, historical_taylor_rule
from .balanced_approach_rule import (
    balanced_approach_rule, historical_balanced_approach_rule)
from .first_difference_rule import (
    first_difference_rule, historical_first_difference_rule)
from ...api.fred_data import fetch_historical_fed_funds_rate
from ...api import fred_client


def print_fred_series_names(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10'
) -> None:
    """
    Print the FRED series IDs and their corresponding names for various economic
    indicators.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.

    Returns:
        None
    """
    # Print the series names and their IDs
    print(
        f"Inflation Series ID:               "
        f"{fred_client.get_series_name(inflation_series_id)}")
    print(
        f"Unemployment Rate Series ID:       "
        f"{fred_client.get_series_name(unemployment_rate_series_id)}")
    print(
        f"Natural Unemployment Series ID:    "
        f"{fred_client.get_series_name(natural_unemployment_series_id)}")
    print(
        f"Real Interest Rate Series ID:      "
        f"{fred_client.get_series_name(real_interest_rate_series_id)}")


def print_verbose_output(
        estimates: pd.DataFrame,
        current_fed_rate: float,
        adjusted: bool = False
) -> None:
    """
    Format and print the verbose output of the interest rate policy estimates.

    Args:
        estimates (pd.DataFrame): DataFrame containing the policy estimates.
        current_fed_rate (float): The current Federal Funds Rate.
        adjusted (bool): Whether the output is for adjusted estimates.

    Returns:
        None
    """
    # Formatting and printing the verbose output
    as_of_date = datetime.now().strftime("%B %d, %Y")
    width = 85  # Total width of the box
    title = " Adjusted Interest Rate Policy Estimates " \
        if adjusted else " Interest Rate Policy Estimates "
    prescription_title = " Adjusted Policy Prescription " \
        if adjusted else " Policy Prescription "

    print("")
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + title.center(width - 2) + "│")
    print("├" + "─" * (width - 2) + "┤")
    for rule, row in estimates.iterrows():
        line = f" {rule:69} {row['Estimate (%)']:.2f}%"
        print(f"│{line:<{width - 2}}│")
    print("├" + "─" * (width - 2) + "┤")
    ffr_description = "Federal Funds Rate (FFR)"
    ffr_value = f"{current_fed_rate:.2f}%"
    line = f" {ffr_description:<62} {ffr_value:>12}"
    print(f"│{line:<{width - 2}}│")
    print("├" + "─" * (width - 2) + "┤")
    line = f" As of Date {as_of_date:>64}"
    print(f"│{line:<{width - 2}}│")
    print("├" + "─" * (width - 2) + "┤")
    print("│" + prescription_title.center(width - 2) + "│")
    print("├" + "─" * (width - 2) + "┤")

    # Calculate the difference between each estimate and the current Fed rate
    for rule, row in estimates.iterrows():
        rate_difference = row['Estimate (%)'] - current_fed_rate
        rounded_difference = round(rate_difference * 4) / 4

        if rounded_difference > 0.125:
            suggestion = (f"suggests raising the rate by "
                          f"{rounded_difference:.2f}%.")
        elif rounded_difference < -0.125:
            suggestion = (f"suggests lowering the rate by "
                          f"{abs(rounded_difference):.2f}%.")
        else:
            suggestion = "suggests maintaining the current rate."

        # Combine rule and suggestion into one sentence and pad to fit the width
        full_suggestion = f" {rule} {suggestion}"
        print(f"│{full_suggestion:<{width - 2}}│")

    print("└" + "─" * (width - 2) + "┘")
    print("")


def calculate_policy_rule_estimates(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10',
        current_inflation_rate: float = None,
        current_unemployment_rate: float = None,
        natural_unemployment_rate: float = None,
        lagged_unemployment_rate: float = None,
        lagged_natural_unemployment_rate: float = None,
        long_term_real_interest_rate: float = None,
        current_fed_rate: float = None,
        inflation_target: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False,
        verbose: bool = False
) -> pd.DataFrame:
    """
    Calculate and return the monetary policy rule estimates as a DataFrame.

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
        lagged_unemployment_rate (float): Unemployment rate from four periods
            ago.
        lagged_natural_unemployment_rate (float): Natural unemployment rate from
            four periods ago.
        long_term_real_interest_rate (float): Long-term real interest rate. If
            not provided, the latest value from FRED is fetched.
        current_fed_rate (float): Current Federal Funds Target Rate. If not
            provided, the latest value from FRED is fetched.
        inflation_target (float): Target inflation rate.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound
            constraint to the Taylor Rule estimate.
        verbose (bool): Whether to print verbose output.

    Returns:
        pd.DataFrame: DataFrame containing the policy estimates.

    """
    # Fetch the current Federal Funds Rate if not provided
    if current_fed_rate is None:
        current_fed_rate = fred_client.get_latest_value('DFEDTARU')

    # Create a dictionary to store common parameters
    params = {
        'inflation_series_id': inflation_series_id,
        'unemployment_rate_series_id': unemployment_rate_series_id,
        'natural_unemployment_series_id': natural_unemployment_series_id,
        'real_interest_rate_series_id': real_interest_rate_series_id,
        'current_inflation_rate': current_inflation_rate,
        'current_unemployment_rate': current_unemployment_rate,
        'natural_unemployment_rate': natural_unemployment_rate,
        'long_term_real_interest_rate': long_term_real_interest_rate,
        'current_fed_rate': current_fed_rate,
        'inflation_target': inflation_target,
        'rho': rho,
        'elb': elb,
        'apply_elb': apply_elb
    }

    # Current Taylor Rule calculation using FRED data
    tr_estimate = taylor_rule(**params)

    # Current Balanced Approach Rule calculation using FRED data
    bar_estimate = balanced_approach_rule(**params)

    # Current Balanced Approach (Shortfalls) Rule calculation using FRED data
    basr_estimate = balanced_approach_rule(use_shortfalls_rule=True, **params)

    # Create a copy of params for First Difference Rule and remove unnecessary
    # keys
    fdr_params = params.copy()
    fdr_params.update({
        'lagged_unemployment_rate': lagged_unemployment_rate,
        'lagged_natural_unemployment_rate': lagged_natural_unemployment_rate
    })
    del fdr_params['real_interest_rate_series_id']
    del fdr_params['long_term_real_interest_rate']
    del fdr_params['current_fed_rate']

    # Current First Difference Rule calculation using FRED data
    fdr_estimate = first_difference_rule(**fdr_params)

    # Compile the estimates into a DataFrame
    estimates = pd.DataFrame(
        data=[
            tr_estimate,
            bar_estimate,
            basr_estimate,
            fdr_estimate
        ],
        columns=['Estimate (%)'],
        index=[
            'Taylor Rule (TR)',
            'Balanced Approach Rule (BAR)',
            'Balanced Approach Shortfalls Rule (BASR)',
            'First Difference Rule (FDR)'
        ]
    )

    if verbose & (rho > 0.0) or apply_elb:
        print_verbose_output(estimates, current_fed_rate, adjusted=True)
        print("")
    else:
        if verbose:
            print_verbose_output(estimates, current_fed_rate)
    return estimates


def calculate_historical_policy_rates(
        inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id: str = 'UNRATE',
        natural_unemployment_series_id: str = 'NROU',
        real_interest_rate_series_id: str = 'DFII10',
        inflation_target: float = 2.0,
        rho: float = 0.0,
        elb: float = 0.125,
        apply_elb: bool = False
) -> pd.DataFrame:
    """
    Calculate and return the historical monetary policy rule estimates as a
    DataFrame.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.
        inflation_target (float): Target inflation rate.
        rho (float): Policy inertia coefficient. Defaults to 0.0 which means
            no inertia and no adjustment is made to Taylor Rule estimate. A
            value of 1.0 would mean full inertia and immediate central bank
            adjustment to the Taylor Rule estimate.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound
            constraint to the Taylor Rule estimate.

    Returns:
        pd.DataFrame: DataFrame containing the historical policy estimates.
    """
    # Create a dictionary to store common parameters
    params = {
        'inflation_series_id': inflation_series_id,
        'unemployment_rate_series_id': unemployment_rate_series_id,
        'natural_unemployment_series_id': natural_unemployment_series_id,
        'real_interest_rate_series_id': real_interest_rate_series_id,
        'inflation_target': inflation_target,
        'rho': rho,
        'elb': elb,
        'apply_elb': apply_elb
    }

    # Historical Taylor Rule calculation using FRED data
    historical_tr = historical_taylor_rule(**params)

    # Historical BAR calculation using FRED data
    historical_bar = historical_balanced_approach_rule(**params)

    # Historical BASR calculation using FRED data
    historical_basr = historical_balanced_approach_rule(
        use_shortfalls_rule=True,
        **params
    )

    # Create a copy of params for First Difference Rule and remove unnecessary
    # keys
    fdr_params = params.copy()
    del fdr_params['real_interest_rate_series_id']

    # Historical First Difference Rule (FDR) calculation using FRED data
    historical_fdr = historical_first_difference_rule(**fdr_params)

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


def plot_historical_policy_rates(
        historical_policy_rates: pd.DataFrame,
        adjusted: bool = False
) -> None:
    """
    Extract the time range from the data, plot the (adjusted or unadjusted)
    policy rules and the Federal Funds Rate, and return the date range.

    Args:
        historical_policy_rates (pd.DataFrame): DataFrame containing the
            historical policy rates.
        adjusted (bool): If True, plot the adjusted policy rates. If False,
            plot the unadjusted policy rates.

    Returns:
        None
    """
    # Determine which columns to use based on the adjusted parameter
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
