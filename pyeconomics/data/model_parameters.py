# pyeconomics/data/model_parameters.py

from dataclasses import dataclass


@dataclass
class TaylorRuleParameters:
    """
    Data class for storing Taylor Rule model parameters.

    Attributes:
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        okun_factor (float): Multiplier for the unemployment gap.
        rho (float): Policy inertia coefficient.
        elb (float): Effective lower bound for interest rates.
        apply_elb (bool): Whether to apply the effective lower bound
            constraint to the Taylor Rule estimate.
        verbose (bool): Whether to print verbose output.
        include_ai_analysis (bool): Whether to include AI-generated analysis.
            You must have OpenAI API credentials set up to use this feature. If
            not provided, defaults to False. Sign up for OpenAI at
            https://openai.com/index/openai-api/.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.
    """
    inflation_target: float = 2.0
    alpha: float = 0.5
    beta: float = 0.5
    okun_factor: float = 2.0
    rho: float = 0.0
    elb: float = 0.125
    apply_elb: bool = False
    verbose: bool = False
    include_ai_analysis: bool = False
    max_tokens: int = 500
    model: str = 'gpt-4o'


@dataclass
class BalancedApproachRuleParameters:
    """
    Data class for storing Balanced Approach Rule parameters.

    Attributes:
        inflation_target (float): Target inflation rate.
        alpha (float): Weight for inflation gap.
        beta (float): Weight for unemployment gap.
        rho (float): Policy inertia coefficient.
        elb (float): Effective lower bound.
        apply_elb (bool): Whether to apply the effective lower bound.
        use_shortfalls_rule (bool): Whether to use the Balanced Approach Rule
            with shortfalls.
        verbose (bool): Whether to print verbose output.
        include_ai_analysis (bool): Whether to include AI-generated analysis.
            You must have OpenAI API credentials set up to use this feature. If
            not provided, defaults to False. Sign up for OpenAI at
            https://openai.com/index/openai-api/.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.
    """
    inflation_target: float = 2.0
    alpha: float = 0.5
    beta: float = 2.0
    rho: float = 0.0
    elb: float = 0.125
    apply_elb: bool = False
    use_shortfalls_rule: bool = False
    verbose: bool = False
    include_ai_analysis: bool = False
    max_tokens: int = 500
    model: str = 'gpt-4o'


@dataclass
class FirstDifferenceRuleParameters:
    """
    Data class for storing First Difference Rule parameters.

    Attributes:
        inflation_target (float): Long-term target inflation rate.
        alpha (float): Coefficient for the inflation gap.
        rho (float): Policy inertia coefficient.
        elb (float): Effective lower bound for the interest rate.
        apply_elb (bool): Whether to apply the effective lower bound constraint.
        verbose (bool): Whether to print verbose output.
        include_ai_analysis (bool): Whether to include AI-generated analysis.
            You must have OpenAI API credentials set up to use this feature. If
            not provided, defaults to False. Sign up for OpenAI at
            https://openai.com/index/openai-api/.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.
    """
    inflation_target: float = 2.0
    alpha: float = 0.5
    rho: float = 0.0
    elb: float = 0.125
    apply_elb: bool = False
    verbose: bool = False
    include_ai_analysis: bool = False
    max_tokens: int = 500
    model: str = 'gpt-4o'


@dataclass
class MonetaryPolicyRulesParameters:
    """
    Data class for storing

    Attributes:
        inflation_target (float): Target inflation rate.
        rho (float): Policy inertia coefficient.
        elb (float): Effective lower bound for the interest rate.
        apply_elb (bool): Whether to apply the effective lower bound constraint.
        verbose (bool): Whether to print verbose output.
        include_ai_analysis (bool): Whether to include AI-generated analysis.
            You must have OpenAI API credentials set up to use this feature. If
            not provided, defaults to False. Sign up for OpenAI at
            https://openai.com/index/openai-api/.
        max_tokens (int): Maximum number of tokens for the AI response. Defaults
            to 500 which may cost a few cents per call. Adjust as needed. See
            https://openai.com/api/pricing/ for details.
        model (str): The OpenAI model to use for the analysis. Defaults to
            'gpt-4o'. Other models are available, such as 'gpt-4-turbo' and
            'gpt-3.5-turbo'. See https://platform.openai.com/docs/models for
            more information.
    """
    inflation_target: float = 2.0
    rho: float = 0.0
    elb: float = 0.125
    apply_elb: bool = False
    verbose: bool = False
    include_ai_analysis: bool = False
    max_tokens: int = 500
    model: str = 'gpt-4o'
    as_of_date: str = None
