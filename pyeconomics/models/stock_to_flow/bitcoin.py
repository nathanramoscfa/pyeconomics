# pyeconomics/models/stock_to_flow/bitcoin.py

from datetime import timedelta

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit


def power_law_function(x, a, b):
    """
    Power Law Function
    """
    return np.exp(a) * (x ** b)


def fit_model(data: pd.DataFrame):
    params, cov, _, _, _ = curve_fit(
        power_law_function,
        data.StocktoFlow.values,
        data.CapMrktCurUSD.values
    )
    return params


def calculate_model_values(data: pd.DataFrame, params) -> pd.DataFrame:
    data['ModelCapMrktCurUSD'] = (
            np.exp(params[0]) * (data['StocktoFlow'] ** params[1])
    ).round(4)
    data['ModelPriceUSD'] = data['ModelCapMrktCurUSD'] / data['SplyCur']
    data['Difference%'] = (data['ModelPriceUSD'] / data['PriceUSD'] - 1) * 100
    return data


def bitcoin_s2f_forecast(
    data: pd.DataFrame,
    params: tuple,
    years_to_project: int = 6
) -> pd.DataFrame:
    """
    Projects future Bitcoin stock-to-flow data and calculates future model
    values.

    Args:
        data (pd.DataFrame): The historical Bitcoin data.
        params (tuple): The fitted model parameters.
        years_to_project (int): The number of years to project into the future.

    Returns:
        pd.DataFrame: The combined historical and projected data.
    """
    # Calculate mean BlkCnt from April 19, 2024
    start_date = '2024-04-19'
    annual_average_mined = data.loc[start_date:]['Flow'].mean()

    # Project into the future, extending the end date to accommodate the
    # specified number of years
    end_date = pd.Timestamp(start_date) + pd.DateOffset(years=years_to_project)
    future_dates = pd.date_range(
        start=data.index[-1] + timedelta(days=1), end=end_date, freq='D'
    )
    future_data = pd.DataFrame(index=future_dates)

    # Define the last halving date before today
    last_halving_date = pd.Timestamp(start_date)

    # Estimate future halving dates (approx every 4 years, 1460 days)
    days_between_halvings = 1460
    num_halvings = int(
        (end_date - last_halving_date).days // days_between_halvings)
    halving_dates = [
        last_halving_date + timedelta(days=days_between_halvings * i)
        for i in range(1, num_halvings + 1)
    ]

    # Use mean Flow until the first halving date, then halve at each
    # subsequent halving date
    future_data['Flow'] = annual_average_mined
    for i, date in enumerate(halving_dates):
        future_data.loc[date:, 'Flow'] = annual_average_mined / (2 ** (i + 1))
        if i > 0:
            previous_halving_date = halving_dates[i - 1]
            future_data.loc[previous_halving_date:date, 'Flow'] = (
                annual_average_mined / (2 ** i)
            )

    # Compute future SplyCur
    initial_supply = data['SplyCur'].iloc[-1]
    future_data['SplyCur'] = initial_supply + future_data['Flow'].cumsum()

    # Combine historical and future data to compute StocktoFlow without NaNs
    combined_data = pd.concat([data[['SplyCur']], future_data[['SplyCur']]])
    combined_data['StocktoFlow'] = (
        combined_data['SplyCur'] /
        (combined_data['SplyCur'] - combined_data['SplyCur'].shift(365))
    )

    # Correct any potential NaNs
    combined_data['StocktoFlow'] = combined_data['StocktoFlow'].ffill()

    # Apply the model to future data
    future_data['StocktoFlow'] = combined_data['StocktoFlow'].loc[
        future_data.index
    ]
    future_data['ModelCapMrktCurUSD'] = (
        np.exp(params[0]) * (future_data['StocktoFlow'] ** params[1])
    ).round(4)
    future_data['ModelPriceUSD'] = (
        future_data['ModelCapMrktCurUSD'] / future_data['SplyCur']
    )

    # Concatenate historical and future data
    full_data = pd.concat([data, future_data])

    return full_data
