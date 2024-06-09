# pyeconomics/ai/monetary_policy_rules.py

import os

import openai

from pyeconomics.api.openai_api import load_prompt
from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import MonetaryPolicyRulesParameters


def monetary_policy_rules(
    estimates: dict,
    indicators: EconomicIndicators,
    params: MonetaryPolicyRulesParameters,
) -> str:
    """
    Generate an AI-based analysis of the monetary policy rules calculation
    results.

    Args:
        estimates (dict): Dictionary containing the monetary policy rules
            estimates.
        indicators (EconomicIndicators): Instance containing economic
            indicators.
        params (MonetaryPolicyRulesParameters): Instance containing the policy
            rule parameters.

    Returns:
        str: AI-generated analysis paragraph.
    """
    if params.rho > 0.0 or params.apply_elb:
        prompt_filepath = 'adjusted_monetary_policy_rules.txt'
    else:
        prompt_filepath = 'monetary_policy_rules.txt'

    # Construct the full path to the prompt file
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        prompt_filepath
    )

    # Load the prompt template
    prompt_template = load_prompt(prompt_file_path)

    # Format the prompt with data
    prompt = prompt_template.format(
        taylor_rule=round(estimates['Taylor Rule (TR)'], 2),
        balanced_approach_rule=round(
            estimates['Balanced Approach Rule (BAR)'], 2),
        balanced_approach_shortfalls_rule=round(
            estimates['Balanced Approach Shortfalls Rule (BASR)'], 2),
        first_difference_rule=round(
            estimates['First Difference Rule (FDR)'], 2),
        current_fed_rate=round(indicators.current_fed_rate, 2)
    )

    response = openai.chat.completions.create(
        model=params.model,
        messages=[
            {"role": "system",
             "content": "Act as the Federal Open Market Committee (FOMC) of "
                        "the Federal Reserve System (the Fed) that is charged "
                        "with making key decisions about interest rates and "
                        "the growth of the United States money supply."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=params.max_tokens
    )

    analysis = response.choices[0].message.content.strip()
    return analysis
