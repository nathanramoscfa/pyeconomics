# pyeconomics/ai/taylor_rule.py

import os

import openai

from pyeconomics.api.openai_api import load_prompt
from pyeconomics.utils.utils import encode_image


def taylor_rule(
    data: dict,
    max_tokens: int = 500,
    model: str = 'gpt-4o'
) -> str:
    """
    Generate an AI-based analysis of the Taylor Rule calculation results.

    Args:
        data (dict): Dictionary containing the Taylor Rule calculation data.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.

    Returns:
        str: AI-generated analysis paragraph.
    """
    # Construct the full path to the prompt file
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        'taylor_rule.txt'
    )

    # Load the prompt template
    prompt_template = load_prompt(prompt_file_path)

    # Format the prompt with data
    prompt = prompt_template.format(
        current_inflation_rate=round(data['current_inflation_rate'], 2),
        inflation_target=round(data['inflation_target'], 2),
        current_unemployment_rate=round(data['current_unemployment_rate'], 2),
        natural_unemployment_rate=round(data['natural_unemployment_rate'], 2),
        long_term_real_interest_rate=round(
            data['long_term_real_interest_rate'], 2),
        current_fed_rate=round(data['current_fed_rate'], 2),
        inflation_gap=round(data['inflation_gap'], 2),
        unemployment_gap=round(data['unemployment_gap'], 2),
        unadjusted_taylor_rule=round(data['unadjusted_taylor_rule'], 2),
        adjusted_taylor_rule_after_elb=round(
            data['adjusted_taylor_rule_after_elb'], 2),
        adjusted_taylor_rule_after_inertia=round(
            data['adjusted_taylor_rule_after_inertia'], 2)
    )

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Act as the Federal Open Market Committee (FOMC) of "
                        "the Federal Reserve System (the Fed) that is charged "
                        "with making key decisions about interest rates and "
                        "the growth of the United States money supply."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )

    analysis = response.choices[0].message.content.strip()
    return analysis


def plot_interpretation(
    image_path: str,
    max_tokens: int = 500,
    model: str = 'gpt-4o'
) -> str:
    """
    Generate an AI-based interpretation of the plot data.

    Args:
        image_path (str): Path to the plot image file.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.

    Returns:
        str: AI-generated interpretation paragraph.
    """
    # Encode the image to base64
    base64_image = encode_image(image_path)

    # Load the prompt from the file
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        'plot_analysis.txt'
    )
    user_prompt = load_prompt(prompt_file_path)

    prompt = [
        {"type": "text", "text": user_prompt},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        }
    ]

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Act as the Federal Open Market Committee (FOMC) of "
                        "the Federal Reserve System (the Fed) that is charged "
                        "with making key decisions about interest rates and "
                        "the growth of the United States money supply."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )

    interpretation = response.choices[0].message.content.strip()
    return interpretation
