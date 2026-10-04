# pyeconomics/ai/taylor_rule.py

import os

from pyeconomics.api.openai_api import load_prompt, initialize_openai_client
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
        max_tokens (int): Maximum number of tokens for the AI response. 
            Defaults to 500 which may cost a few cents per call. Adjust as 
            needed. See https://openai.com/api/pricing/ for details.
        model (str): The OpenAI ai_model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.

    Returns:
        str: AI-generated analysis paragraph.
    """
    # Ensure the OpenAI client is initialized only when this function is called
    client = initialize_openai_client()

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
            data['adjusted_taylor_rule_after_inertia'], 2),
        rho=round(data['rho'], 2),
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Act as the Federal Open Market Committee (FOMC) of "
                        "the Federal Reserve System (the Fed) that is charged "
                        "with making key decisions about interest rates and "
                        "the growth of the United States money supply."
             },
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )

    analysis = response.choices[0].message.content
    return analysis if analysis else ""


def plot_interpretation(
    image_path: str,
    max_tokens: int = 500,
    model: str = 'gpt-4o'
) -> str:
    """
    Generate an AI-based interpretation of the plot data.

    Args:
        image_path (str): Path to the plot image file.
        max_tokens (int): Maximum number of tokens for the AI response. 
            Defaults to 500 which may cost a few cents per call. Adjust as 
            needed. See https://openai.com/api/pricing/ for details.
        model (str): The OpenAI ai_model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.

    Returns:
        str: AI-generated interpretation paragraph.
    """
    # Initialize OpenAI client
    client = initialize_openai_client()
    
    # Encode the image to base64
    base64_image = encode_image(image_path)

    # Load the prompt from the file
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        'plot_analysis.txt'
    )
    user_prompt = load_prompt(prompt_file_path)

    system_content = (
        "Act as the Federal Open Market Committee (FOMC) of the Federal "
        "Reserve System (the Fed) that is charged with making key decisions "
        "about interest rates and the growth of the US money supply."
    )

    # For gpt-4-vision models, we need specific formatting
    if 'vision' in model or 'gpt-4o' in model:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=max_tokens
        )
    else:
        # Fallback to text-only models
        no_image_msg = (
            f"{user_prompt}\n\n"
            "[Note: Unable to process image with this model. "
            "Please use a vision-capable model for image analysis.]"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user", 
                    "content": no_image_msg
                }
            ],
            max_tokens=max_tokens
        )

    interpretation = response.choices[0].message.content
    return interpretation if interpretation else ""


def gaps_interpretation(
    image_path: str,
    max_tokens: int = 500,
    model: str = 'gpt-4o'
) -> str:
    """
    Generate an AI-based interpretation of the plot data.

    Args:
        image_path (str): Path to the plot image file.
        max_tokens (int): Maximum number of tokens for the AI response. 
            Defaults to 500 which may cost a few cents per call. Adjust as 
            needed. See https://openai.com/api/pricing/ for details.
        model (str): The OpenAI ai_model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.

    Returns:
        str: AI-generated interpretation paragraph.
    """
    # Initialize OpenAI client
    client = initialize_openai_client()
    
    # Encode the image to base64
    base64_image = encode_image(image_path)

    # Load the prompt from the file
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        'gaps_analysis.txt'
    )
    user_prompt = load_prompt(prompt_file_path)

    system_content = (
        "Act as the Federal Open Market Committee (FOMC) of the Federal "
        "Reserve System (the Fed) that is charged with making key decisions "
        "about interest rates and the growth of the US money supply."
    )

    # For gpt-4-vision models, we need specific formatting
    if 'vision' in model or 'gpt-4o' in model:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=max_tokens
        )
    else:
        # Fallback to text-only models
        no_image_msg = (
            f"{user_prompt}\n\n"
            "[Note: Unable to process image with this model. "
            "Please use a vision-capable model for image analysis.]"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user", 
                    "content": no_image_msg
                }
            ],
            max_tokens=max_tokens
        )

    interpretation = response.choices[0].message.content
    return interpretation if interpretation else ""
