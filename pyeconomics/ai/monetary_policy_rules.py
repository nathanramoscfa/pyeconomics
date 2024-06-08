# pyeconomics/ai/monetary_policy_rules.py

import os

import openai

from pyeconomics.api.openai_api import load_prompt


def monetary_policy_rules(
    estimates: dict,
    current_fed_rate: float,
    ai_dict: dict = None,
) -> str:
    """
    Generate an AI-based analysis of the monetary policy rules calculation
    results.

    Args:
        estimates (dict): Dictionary containing the monetary policy rules
            estimates.
        current_fed_rate (float): The current Federal Funds Rate.
        ai_dict (dict): Dictionary containing the AI-parameters.

    Returns:
        str: AI-generated analysis paragraph.
    """
    if ai_dict['adjusted']:
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
        current_fed_rate=round(current_fed_rate, 2)
    )

    response = openai.chat.completions.create(
        model=ai_dict['model'],
        messages=[
            {"role": "system",
             "content": "Act as the Federal Open Market Committee (FOMC) of "
                        "the Federal Reserve System (the Fed) that is charged "
                        "with making key decisions about interest rates and "
                        "the growth of the United States money supply."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=ai_dict['max_tokens']
    )

    analysis = response.choices[0].message.content.strip()
    return analysis
