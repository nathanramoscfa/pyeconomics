# tests/test_verbose_fdr.py

import pytest
from datetime import datetime

from pyeconomics.verbose.first_difference_rule import (
    verbose_first_difference_rule)


@pytest.fixture
def mock_data():
    return {
        'current_inflation_rate': 2.5,
        'inflation_target': 2.0,
        'current_unemployment_rate': 4.0,
        'lagged_unemployment_rate': 4.2,
        'natural_unemployment_rate': 4.5,
        'lagged_natural_unemployment_rate': 4.6,
        'current_fed_rate': 0.5,
        'inflation_gap': 0.5,
        'current_unemployment_gap': 0.5,
        'lagged_unemployment_gap': 0.4,
        'alpha': 0.5,
        'unadjusted_fdr_rule': 1.0,
        'adjusted_fdr_rule_after_elb': 1.0,
        'apply_elb': False,
        'elb': 0.0,
        'rho': 0.5,
        'adjusted_fdr_rule_after_inertia': 0.75,
        'include_ai_analysis': False,
        'max_tokens': 500,
        'model': 'chatgpt-4o'
    }


def test_verbose_first_difference_rule(capsys, mock_data):
    verbose_first_difference_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "============================================\n"
        "  Current Inflation:                               2.50%\n"
        "  Target Inflation:                                2.00%\n"
        "  Current Unemployment Rate:                       4.00%\n"
        "  Lagged Unemployment Rate:                        4.20%\n"
        "  Natural Unemployment Rate:                       4.50%\n"
        "  Lagged Natural Unemployment Rate:                4.60%\n"
        "  Last Fed Rate:                                   0.50%\n"
        f"  As of Date:                                      {as_of_date}\n"
        "\n==== Gaps "
        "===========================================================\n"
        "  Inflation Gap:                                   0.50%\n"
        "  Current Unemployment Gap:                        0.50%\n"
        "  Lagged Unemployment Gap:                         0.40%\n"
        "\n==== First Difference Rule (FDR) "
        "====================================\n"
        "  Last Fed Rate:                                 0.50%\n"
        "  Alpha * Inflation Gap:                         + 0.50 * 0.50%\n"
        "  Current Unemployment Gap Adjustment:           + 0.50%\n"
        "  Last Year Unemployment Gap Adjustment:         - 0.40%\n"
        "-----------------------------------"
        "----------------------------------\n"
        "  Unadjusted FDR Estimate:                       1.00%\n"
        "\n==== Adjusted First Difference Rule "
        "=================================\n"
        "\n  Policy Inertia Adjustment:\n"
        "  Policy Inertia Coefficient (rho):              0.50\n"
        "  Last Fed Rate:                                 * 0.50%\n"
        "  Adjustment Coefficient (1 - rho):              + (1 - 0.50)\n"
        "  FDR Adjusted for ELB:                          * 1.00%\n"
        "-----------------------------------"
        "----------------------------------\n"
        "  Adjusted FDR Estimate:                         0.75%\n"
        "\n==== Policy Prescription "
        "=================================================\n"
        "  The Adjusted FDR Estimate is 0.25% higher than the Current Fed \n"
        "  Rate. The Fed should consider raising the interest rate by 0.25%.\n"
    )

    # Comparing the captured output with the expected output
    assert output == expected_output


def test_verbose_first_difference_rule_lower_rate(capsys, mock_data):
    mock_data['adjusted_fdr_rule_after_inertia'] = 0.0
    verbose_first_difference_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    assert ("The Adjusted FDR Estimate is 0.50% "
            "lower than the Current Fed") in output
    assert ("Rate. The Fed should consider lowering "
            "the interest rate by 0.50%.") in output


def test_verbose_first_difference_rule_equal_rate(capsys, mock_data):
    mock_data['adjusted_fdr_rule_after_inertia'] = 0.5
    verbose_first_difference_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    assert ("The Adjusted FDR Estimate is equal"
            " to the Current Fed Rate.") in output
    assert "The Fed should maintain the current interest rate." in output


if __name__ == '__main__':
    pytest.main()
