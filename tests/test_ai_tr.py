# pyeconomics/tests/test_ai_fdr.py

import unittest
import re
from unittest.mock import patch, mock_open as mock_file_open, MagicMock

from pyeconomics.ai.taylor_rule import (taylor_rule, plot_interpretation)


class TestFirstDifferenceRule(unittest.TestCase):
    @staticmethod
    def assert_called_with_regex(mock, pattern):
        regex = re.compile(pattern)
        for call in mock.mock_calls:
            if regex.search(call[1][0]):
                return True
        raise AssertionError(f"No calls matching regex: {pattern}")

    @patch("pyeconomics.ai.taylor_rule.openai.chat.completions."
           "create")
    @patch("builtins.open", new_callable=mock_file_open,
           read_data="This is a test prompt with {current_inflation_rate} and "
                     "{unemployment_gap}.")
    def test_taylor_rule(self, mock_open, mock_openai):
        data = {
            "current_inflation_rate": 2.5,
            "inflation_target": 2.0,
            "current_unemployment_rate": 4.0,
            "natural_unemployment_rate": 4.5,
            "long_term_real_interest_rate": 1.0,
            "current_fed_rate": 1.5,
            "inflation_gap": 0.5,
            "unemployment_gap": -0.5,
            "unadjusted_taylor_rule": 2.0,
            "adjusted_taylor_rule_after_elb": 1.8,
            "adjusted_taylor_rule_after_inertia": 1.9
        }

        mock_openai.return_value.choices = [
            MagicMock(message=MagicMock(content="Mock AI response"))
        ]

        response = taylor_rule(data)

        self.assertEqual(response, "Mock AI response")
        self.assert_called_with_regex(
            mock_open,
            r".*pyeconomics[\\/]ai[\\/]prompts[\\/]taylor_rule\.txt"
        )
        mock_openai.assert_called_once()

    @patch("pyeconomics.ai.taylor_rule.openai.chat.completions."
           "create")
    @patch("builtins.open", new_callable=mock_file_open,
           read_data="This is a test plot analysis prompt.")
    @patch("pyeconomics.ai.taylor_rule.encode_image",
           return_value="base64_encoded_image")
    def test_plot_interpretation(
        self, mock_encode_image, mock_open, mock_openai
    ):
        mock_openai.return_value.choices = [
            MagicMock(message=MagicMock(content="Mock AI plot interpretation"))
        ]

        response = plot_interpretation("path/to/plot.png")

        self.assertEqual(response, "Mock AI plot interpretation")
        self.assert_called_with_regex(
            mock_open,
            r".*pyeconomics[\\/]ai[\\/]prompts[\\/]plot_analysis\.txt"
        )
        mock_openai.assert_called_once()
        mock_encode_image.assert_called_once_with("path/to/plot.png")


if __name__ == '__main__':
    unittest.main()
