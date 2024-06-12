# pyeconomics/tests/test_ai_bar.py

import base64
import unittest
import re
from unittest.mock import patch, mock_open as mock_file_open, MagicMock

from pyeconomics.ai.balanced_approach_rule import (
    balanced_approach_rule, plot_interpretation, encode_image
)


class TestBalancedApproachRule(unittest.TestCase):
    @staticmethod
    def assert_called_with_regex(mock, pattern):
        regex = re.compile(pattern)
        for call in mock.mock_calls:
            if regex.search(call[1][0]):
                return True
        raise AssertionError(f"No calls matching regex: {pattern}")

    @patch("pyeconomics.ai.balanced_approach_rule.openai.chat.completions."
           "create")
    @patch("builtins.open", new_callable=mock_file_open,
           read_data="This is a test prompt with {current_inflation_rate} and "
                     "{unemployment_gap}.")
    def test_balanced_approach_rule(self, mock_open, mock_openai):
        data = {
            "current_inflation_rate": 2.5,
            "inflation_target": 2.0,
            "current_unemployment_rate": 4.0,
            "natural_unemployment_rate": 4.5,
            "long_term_real_interest_rate": 1.0,
            "current_fed_rate": 1.5,
            "inflation_gap": 0.5,
            "unemployment_gap": -0.5,
            "unadjusted_rate": 2.0,
            "adjusted_rate_after_elb": 1.8,
            "adjusted_rate_after_inertia": 1.9
        }

        mock_openai.return_value.choices = [
            MagicMock(message=MagicMock(content="Mock AI response"))
        ]

        response = balanced_approach_rule(data)

        self.assertEqual(response, "Mock AI response")
        self.assert_called_with_regex(
            mock_open,
            r".*pyeconomics[\\/]ai[\\/]prompts[\\/]balanced_approach_rule\.txt"
        )
        mock_openai.assert_called_once()

    @patch("pyeconomics.ai.balanced_approach_rule.openai.chat.completions."
           "create")
    @patch("builtins.open", new_callable=mock_file_open,
           read_data="This is a test plot analysis prompt.")
    @patch("pyeconomics.ai.balanced_approach_rule.encode_image",
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

    def test_encode_image(self):
        image_path = "path/to/sample_image.png"
        mock_content = b"mock image content"

        with patch("builtins.open", mock_file_open(read_data=mock_content),
                   create=True) as mock_file:
            encoded_image = encode_image(image_path)

            mock_file.assert_called_once_with(image_path, "rb")
            self.assertEqual(encoded_image,
                             base64.b64encode(mock_content).decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
