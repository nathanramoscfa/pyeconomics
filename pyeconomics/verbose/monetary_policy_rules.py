# pyeconomics/verbose/test_ai_monetary_policy_rules.py

from datetime import datetime

import pandas as pd

from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import MonetaryPolicyRulesParameters
from pyeconomics.ai.monetary_policy_rules import monetary_policy_rules
from pyeconomics.utils.utils import wrap_text


def verbose_monetary_policy_rules(
    estimates: pd.DataFrame,
    indicators: EconomicIndicators,
    params: MonetaryPolicyRulesParameters,
) -> None:
    """
    Format and print the verbose output of the interest rate policy estimates.

    Args:
        estimates (pd.DataFrame): DataFrame containing the policy estimates.
            Generated by the calculate_policy_rule_estimates function in
            models/monetary_policy/test_ai_monetary_policy_rules.py.
        indicators (EconomicIndicators): Instance containing economic
            indicators.
        params (MonetaryPolicyRulesParameters): Instance containing the policy
            rule parameters.

    Returns:
        None
    """
    print("verbose_monetary_policy_rules called")  # Add this line for debugging

    # Formatting and printing the verbose output
    width = 89  # Total width of the box
    as_of_date = params.as_of_date or datetime.now().strftime("%B %d, %Y")
    adjusted = params.rho > 0.0 or params.apply_elb
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
        line = f"    {rule:70} {row['Estimate (%)']:.2f}%"
        print(f"│{line:<{width - 2}}│")
    print("├" + "─" * (width - 2) + "┤")

    ffr_description = "Federal Funds Rate (FFR)"
    ffr_value = f"{indicators.current_fed_rate:.2f}%"
    line = f"    {ffr_description:<64} {ffr_value:>11}"
    print(f"│{line:<{width - 2}}│")

    print("├" + "─" * (width - 2) + "┤")

    if adjusted:
        print(f"│{' Adjustment Parameters ':^{width - 2}}│")
        print("├" + "─" * (width - 2) + "┤")
        elb = f"{params.elb:.2f}%"
        line = f"    Effective Lower Bound (ELB) {elb:>48}"
        print(f"│{line:<{width - 2}}│")

        rho = f"{params.rho:.2f}"
        line = f"    Policy Inertia (Rho) {rho:>54}"
        print(f"│{line:<{width - 2}}│")
        print("├" + "─" * (width - 2) + "┤")

    line = f"    As of Date {as_of_date:>65}"
    print(f"│{line:<{width - 2}}│")

    print("├" + "─" * (width - 2) + "┤")

    # Optionally include AI-generated analysis
    if params.include_ai_analysis:
        print("│" + ai_prescription_title.center(width - 2) + "│")
        print("├" + "─" * (width - 2) + "┤")
        estimates_dict = estimates.to_dict()['Estimate (%)']
        analysis = monetary_policy_rules(estimates_dict, indicators, params)
        analysis = wrap_text(analysis, width=width - 6, indent=3)

        for line in analysis.split('\n'):
            print("│ " + line.ljust(width - 4) + " │")

        caution = (f"*Generated with {params.model}. Use with caution. "
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
            rate_difference = row['Estimate (%)'] - indicators.current_fed_rate
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
            full_suggestion = f"    {rule} {suggestion}"
            print(f"│{full_suggestion:<{width - 2}}│")

    print("└" + "─" * (width - 2) + "┘")
    print("")
