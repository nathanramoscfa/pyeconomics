# pyeconomics/models/stock_to_flow/bitcoin.py

from datetime import timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.api as sm
from typing import Union

from pyeconomics.utils.utils import halving_dates_list
from pyeconomics.utils.utils import months_until_next_halving


def power_law_function(x, a, b):
    """
    Power Law Function
    """
    return np.exp(a) * (x ** b)


def fit_regression_model(
    endog: Union[pd.Series, pd.DataFrame],
    exog: Union[pd.Series, pd.DataFrame],
    **kwargs
) -> sm.regression.linear_model.RegressionResults:
    """
    Fit a linear regression model using the statsmodels package.

    Args:
        endog (Union[pd.Series, pd.DataFrame]): The dependent variable.
        exog (Union[pd.Series, pd.DataFrame]): The independent variable(s).
        **kwargs: Additional keyword arguments to pass to the OLS function.

    Returns:
        sm.regression.linear_model.RegressionResults: The fitted regression
            model.
    """
    return sm.OLS(endog, exog).fit(**kwargs)


def calculate_model_values(
    data: pd.DataFrame,
    params: Union[tuple, np.array]
) -> pd.DataFrame:
    data['ModelCapMrktCurUSD'] = (
            np.exp(params[0]) * (data['StocktoFlow'] ** params[1])
    ).round(4)
    data['ModelPriceUSD'] = data['ModelCapMrktCurUSD'] / data['SplyCur']
    data['Difference%'] = (data['ModelPriceUSD'] / data['PriceUSD'] - 1) * 100
    return data


def bitcoin_s2f_forecast(
    data: pd.DataFrame,
    params: Union[tuple, np.array],
    years_to_project: int = 6
) -> pd.DataFrame:
    """
    Projects future Bitcoin stock-to-flow data and calculates future ai_model
    values.

    Args:
        data (pd.DataFrame): The historical Bitcoin data.
        params (tuple): The fitted ai_model parameters.
        years_to_project (int): The number of years to project into the future.

    Returns:
        pd.DataFrame: The combined historical and projected data.
    """
    # Compute historical ai_model forecast
    data = calculate_model_values(data, params)

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

    # Apply the ai_model to future data
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


def plot_s2f_model(
    data: pd.DataFrame,
    model: sm.regression.linear_model.RegressionResults,
    gold_silver_s2f: pd.Series = None
):
    """
    Plot the Bitcoin Stock-to-Flow ai_model.

    Args:
        data (pd.DataFrame): The Bitcoin data.
        model (sm.regression.linear_model.RegressionResults): The fitted model.
        gold_silver_s2f (pd.Series): The stock-to-flow values for gold and
            silver.

    Returns:
        None: The plot is displayed
    """
    # Compute the months until the next halving date
    halving_dates = halving_dates_list()
    data['MonthsUntilHalving'] = data.index.to_series().apply(
        lambda date: months_until_next_halving(date, halving_dates))

    # Extract the ai_model parameters
    slope = model.params['StocktoFlow']
    intercept = model.params['const']
    r_squared = model.rsquared

    # Create the plot
    fig = px.scatter(
        data,
        x='StocktoFlow',
        y='CapMrktCurUSD',
        color='MonthsUntilHalving',
        color_continuous_scale=px.colors.sequential.Rainbow,
        title='Bitcoin Stock-to-Flow Model',
        labels={'StocktoFlow': 'Stock-to-Flow (scarcity)',
                'CapMrktCurUSD': 'Market Value (USD)'},
        log_x=True,
        log_y=True,
        template='plotly_dark'
    )

    # Add gold and silver data if provided
    if gold_silver_s2f is not None:
        fig.add_trace(
            go.Scatter(
                x=[gold_silver_s2f.loc['gold_s2f']],
                y=[gold_silver_s2f.loc['gold_market_value']],
                mode='markers', name='Gold',
                marker=dict(color='gold', symbol='circle', size=20),
                zorder=10
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[gold_silver_s2f.loc['silver_s2f']],
                y=[gold_silver_s2f.loc['silver_market_value']],
                mode='markers', name='Silver',
                marker=dict(color='silver', symbol='circle', size=20),
                zorder=10
            )
        )

    # Add the trendline
    x_vals = np.linspace(data['StocktoFlow'].min(),
                         data['StocktoFlow'].max() * 2.5, 100)
    y_vals = np.exp(slope * np.log(x_vals) + intercept)

    # Ensure the trendline is plotted last
    trendline = go.Scatter(x=x_vals, y=y_vals, mode='lines', name='Trendline',
                           line=dict(color='white', width=2))

    # Add the trendline equation and R^2 value as an annotation
    fig.add_annotation(
        x=0.05, y=0.95,
        text=f'ln(y) = {slope:.4f} ln(x) + {intercept:.4f}<br>R² = '
             f'{r_squared:.3f}',
        showarrow=False,
        xref='paper', yref='paper',
        font=dict(color='white', size=12),
        bgcolor='rgba(0, 0, 0, 0.5)'
    )

    # Update the layout
    height = 600
    width = 900
    colormap_len = height * 0.5
    fig.update_layout(
        height=height,
        width=width,
        xaxis=dict(title='Stock-to-Flow (Scarcity)', type='log', tickformat='d',
                   showgrid=True),
        yaxis=dict(title='Market Value (USD)', type='log', showgrid=True),
        coloraxis_colorbar=dict(
            title=dict(
                text='Months until halving',
                side='right',
                font=dict(size=12)
            ),
            tickvals=np.arange(0, 51, 10),
            ticks="outside",
            ticktext=[f"{i}" for i in range(0, 51, 10)],
            lenmode='pixels',
            len=colormap_len
        )
    )

    # Add trendline after layout update to ensure it's on top
    fig.add_trace(trendline)

    fig.show()


def plot_s2f_prediction_model(
    data: pd.DataFrame,
    model: sm.regression.linear_model.RegressionResults
):
    """
    Plot the Bitcoin Stock-to-Flow ai_model with future projections.

    Args:
        data (pd.DataFrame): The Bitcoin data.
        model (sm.regression.linear_model.RegressionResults): The fitted model.

    Returns:
        None: The plot is displayed
    """
    # Compute the months until the next halving date
    halving_dates = halving_dates_list()
    data['MonthsUntilHalving'] = data.index.to_series().apply(
        lambda date: months_until_next_halving(date, halving_dates))

    # Extract the ai_model parameters
    slope = model.params['StocktoFlow']
    intercept = model.params['const']
    rsquared = model.rsquared

    # Create a figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add ai_model price trace
    fig.add_trace(
        go.Scatter(x=data.index, y=data['ModelPriceUSD'],
                   mode='lines', name='Model Price',
                   line=dict(color='orange', dash='dash')),
        secondary_y=True
    )

    # Add stock-to-flow trace
    fig.add_trace(
        go.Scatter(x=data.index, y=data['StocktoFlow'], mode='lines',
                   name='Stock-to-Flow', line=dict(color='green')),
        secondary_y=False
    )

    # Add the trendline equation and R^2 value as an annotation
    fig.add_annotation(
        x=0.90, y=0.10,
        text=f'ln(y) = {slope:.4f} ln(x) + {intercept:.4f}<br>R² = '
             f'{rsquared:.3f}',
        showarrow=False,
        xref='paper', yref='paper',
        font=dict(color='white', size=12),
        bgcolor='rgba(0, 0, 0, 0.5)'
    )

    # Create scatter plot with color mapped to MonthsUntilHalving
    scatter = go.Scatter(
        x=data.index,
        y=data['PriceUSD'],
        mode='markers',
        marker=dict(
            color=data['MonthsUntilHalving'],
            colorscale=px.colors.sequential.Rainbow,
            colorbar=dict(
                title='Months until halving',
                titleside='right',
                tickvals=np.arange(0, 51, 10),
                ticktext=[f"{i}" for i in range(0, 51, 10)],
                lenmode='pixels',
                len=300
            ),
        ),
        name='PriceUSD'
    )

    # Add scatter plot to the figure
    fig.add_trace(scatter, secondary_y=True)

    # Update the layout
    fig.update_layout(
        height=600,
        width=900,
        title='Bitcoin Stock-to-Flow Model',
        xaxis_title='Date',
        yaxis_title='Stock-to-Flow',
        yaxis_type='log',
        yaxis2=dict(title='Price (USD)', type='log'),
        legend=dict(x=0.01, y=0.98, traceorder='normal'),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=80, b=40),
        xaxis=dict(range=[data.index.min() - timedelta(days=365),
                          data.index.max()])
    )

    # Update x-axis and y-axis to be visible
    fig.update_xaxes(showline=True, linewidth=1, linecolor='white', mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='white', mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='white', mirror=True,
                     secondary_y=True)

    # Ensure minor ticks are enabled and follow the default behavior
    fig.update_yaxes(minor=dict(ticklen=4, showgrid=True), secondary_y=False)

    # Show the plot
    fig.show()
