import pytest
import unittest
from unittest.mock import patch
from pyeconomics.ai.monetary_policy_rules import monetary_policy_rules
from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import MonetaryPolicyRulesParameters


# Helper function to mock openai.chat.completions.create
def mock_openai_chat_completions_create(model, messages, max_tokens):
    # Mark the arguments as used to avoid warnings
    _ = model
    _ = messages
    _ = max_tokens

    class Choice:
        def __init__(self, message):
            self.message = message

    class Message:
        def __init__(self, content):
            self.content = content

    class Response:
        def __init__(self, choices):
            self.choices = choices

    return Response([Choice(Message("This is a test response"))])


@pytest.fixture
def mock_load_prompt():
    with patch(
        'pyeconomics.ai.monetary_policy_rules.load_prompt',
        return_value="Mock prompt with {taylor_rule}%, "
                     "{balanced_approach_rule}%, "
                     "{balanced_approach_shortfalls_rule}%, "
                     "{first_difference_rule}%, "
                     "and {current_fed_rate}%"
    ) as mock:
        yield mock


@pytest.fixture
def mock_openai_chat():
    with patch(
        'openai.chat.completions.create',
        side_effect=mock_openai_chat_completions_create
    ) as mock:
        yield mock


@pytest.fixture
def estimates():
    return {
        'Taylor Rule (TR)': 2.5,
        'Balanced Approach Rule (BAR)': 3.0,
        'Balanced Approach Shortfalls Rule (BASR)': 3.5,
        'First Difference Rule (FDR)': 2.0
    }


@pytest.fixture
def indicators():
    return EconomicIndicators(
        current_fed_rate=2.25
    )


@pytest.fixture
def params():
    return MonetaryPolicyRulesParameters(
        model='gpt-3.5-turbo',
        max_tokens=100,
        rho=0.5,
        apply_elb=True
    )


def test_monetary_policy_rules(
    mock_load_prompt, mock_openai_chat, estimates, indicators, params
):
    analysis = monetary_policy_rules(estimates, indicators, params)
    assert analysis == "This is a test response"
    mock_load_prompt.assert_called_once()
    mock_openai_chat.assert_called_once()
    assert ('Mock prompt with 2.5%, 3.0%, 3.5%, 2.0%, and 2.25%' in
            mock_openai_chat.call_args[1]['messages'][1]['content'])


def test_monetary_policy_rules_no_adjustments(
    mock_load_prompt, mock_openai_chat, estimates, indicators
):
    params = MonetaryPolicyRulesParameters(
        model='gpt-3.5-turbo',
        max_tokens=100,
        rho=0.0,
        apply_elb=False
    )
    analysis = monetary_policy_rules(estimates, indicators, params)
    assert analysis == "This is a test response"
    mock_load_prompt.assert_called_once()
    mock_openai_chat.assert_called_once()
    assert ('Mock prompt with 2.5%, 3.0%, 3.5%, 2.0%, and 2.25%' in
            mock_openai_chat.call_args[1]['messages'][1]['content'])


def test_monetary_policy_rules_invalid_model(mock_load_prompt):
    params = MonetaryPolicyRulesParameters(
        model='invalid-model',
        max_tokens=100,
        rho=0.5,
        apply_elb=True
    )

    with patch(
        'openai.chat.completions.create',
        side_effect=Exception("Invalid model")
    ) as mock_openai_chat:
        with pytest.raises(Exception, match="Invalid model"):
            monetary_policy_rules(
                {
                    'Taylor Rule (TR)': 2.5,
                    'Balanced Approach Rule (BAR)': 3.0,
                    'Balanced Approach Shortfalls Rule (BASR)': 3.5,
                    'First Difference Rule (FDR)': 2.0
                },
                EconomicIndicators(current_fed_rate=2.25),
                params
            )
        mock_load_prompt.assert_called_once()
        mock_openai_chat.assert_called_once()


if __name__ == '__main__':
    unittest.main()
