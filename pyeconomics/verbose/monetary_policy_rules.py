# pyeconomics/verbose/monetary_policy_rules.py

from datetime import datetime

import pandas as pd

from pyeconomics.ai.monetary_policy_rules import monetary_policy_rules
from pyeconomics.utils.utils import wrap_text


def verbose_monetary_policy_rules(
    estimates: pd.DataFrame,
    current_fed_rate: float,
    ai_dict: dict,
    adjusted: bool = False,
    **kwargs
) -> None:
    """
    Format and print the verbose output of the interest rate policy estimates.

    Args:
        estimates (pd.DataFrame): DataFrame containing the policy estimates.
        current_fed_rate (float): The current Federal Funds Rate.
        ai_dict (dict): Dictionary containing the AI-parameters.
        adjusted (bool): Whether the output is for adjusted estimates.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    # Formatting and printing the verbose output
    as_of_date = kwargs.get('as_of_date', datetime.now().strftime("%B %d, %Y"))
    width = 80  # Total width of the box
    title = " Adjusted Interest Rate Policy Estimates " \
        if adjusted else " Interest Rate Policy Estimates "
    prescription_title = " Adjusted Policy Prescription " \
        if adjusted else " Policy Prescription "
    ai_prescription_title = " AI-Generated Adjusted Policy Prescription " \
        if adjusted else " AI-Generated Policy Prescription "

    print("")
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + title.center(width - 2) + "│")
    print("├" + "─" * (width - 2) + "┤")

    for rule, row in estimates.iterrows():
        line = f"    {rule:65} {row['Estimate (%)']:.2f}%"
        print(f"│{line:<{width - 2}}│")
    print("├" + "─" * (width - 2) + "┤")

    ffr_description = "Federal Funds Rate (FFR)"
    ffr_value = f"{current_fed_rate:.2f}%"
    line = f"    {ffr_description:<59} {ffr_value:>11}"
    print(f"│{line:<{width - 2}}│")

    print("├" + "─" * (width - 2) + "┤")

    if adjusted:
        print(f"│{' Adjustment Parameters ':^{width - 2}}│")
        print("├" + "─" * (width - 2) + "┤")
        elb = f"{kwargs['elb']:.2f}%"
        line = f"    Effective Lower Bound (ELB) {elb:>43}"
        print(f"│{line:<{width - 2}}│")

        rho = f"{kwargs['rho']:.2f}"
        line = f"    Policy Inertia (Rho) {rho:>49}"
        print(f"│{line:<{width - 2}}│")
        print("├" + "─" * (width - 2) + "┤")

    line = f"    As of Date {as_of_date:>60}"
    print(f"│{line:<{width - 2}}│")

    print("├" + "─" * (width - 2) + "┤")

    # Optionally include AI-generated analysis
    if ai_dict['include_ai_analysis']:
        print("│" + ai_prescription_title.center(width - 2) + "│")
        print("├" + "─" * (width - 2) + "┤")
        estimates_dict = estimates.to_dict()['Estimate (%)']
        analysis = monetary_policy_rules(
            estimates_dict, current_fed_rate, ai_dict)
        analysis = wrap_text(analysis, width=width - 6, indent=3)

        for line in analysis.split('\n'):
            print("│ " + line.ljust(width - 4) + " │")

        caution = (f"*Generated with {ai_dict['model']}. Use with caution. "
                   f"ChatGPT can make mistakes. Check important info.")

        print("|" + " " * (width - 2) + "|")
        caution = wrap_text(caution, width=width - 4, indent=3)
        for line in caution.split('\n'):
            print("│ " + line.ljust(width - 4) + " │")

    else:
        print("│" + prescription_title.center(width - 2) + "│")
        print("├" + "─" * (width - 2) + "┤")

        # Calculate the difference between each estimate and
        # the current Fed rate
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

            # Combine rule and suggestion into one sentence and
            # pad to fit the width
            full_suggestion = f" {rule} {suggestion}"
            print(f"│{full_suggestion:<{width - 2}}│")

    print("└" + "─" * (width - 2) + "┘")
    print("")
