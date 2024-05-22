# pyeconomics/tests/test_bar_utils.py
import pytest
from datetime import datetime

from pyeconomics.utils.bar_utils import verbose_balanced_approach_rule


@pytest.fixture
def mock_data():
    return {
        'current_inflation_rate': 2.5,
        'inflation_target': 2.0,
        'current_unemployment_rate': 4.0,
        'natural_unemployment_rate': 4.5,
        'long_term_real_interest_rate': 2.0,
        'fed_rate': 0.5,
        'inflation_gap': 0.5,
        'unemployment_gap': 0.5,
        'alpha': 0.5,
        'beta': 0.5,
        'unadjusted_bar_rule': 1.0,
        'adjusted_bar_after_elb': 1.0,
        'apply_elb': False,
        'elb': 0.0,
        'rho': 0.5,
        'adjusted_bar_after_inertia': 0.75,
        'use_shortfalls_rule': False,
        'use_shortfalls': False
    }


def test_verbose_balanced_approach_rule(capsys, mock_data):
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "=============================================\n"
        "Current Inflation:                               2.50%\n"
        "Target Inflation:                                2.00%\n"
        "Current Unemployment Rate:                       4.00%\n"
        "Natural Unemployment Rate:                       4.50%\n"
        "Long-Term Real Interest Rate:                    2.00%\n"
        "Current Fed Rate:                                0.50%\n"
        f"As of Date:                                      {as_of_date}\n"
        "\n==== Gaps "
        "============================================================\n"
        "Inflation Gap:                                   0.50%\n"
        "Unemployment Gap:                                0.50%\n"
        "\n==== Balanced Approach Rule "
        "==========================================\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Inflation:                             + 2.50%\n"
        "  Alpha * Inflation Gap:                         + 0.50 * 0.50%\n"
        "  Beta * Unemployment Gap:                       + 0.50 * 0.50%\n"
        "-----------------------------------"
        "-----------------------------------\n"
        "  Unadjusted BAR Estimate:                       1.00%\n"
        "\n==== Adjusted Balanced Approach Rule "
        "=================================\n"
        "\n  Policy Inertia Adjustment:              \n"
        "  Policy Inertia Coefficient (rho):              0.50\n"
        "  Current Fed Rate:                              * 0.50%\n"
        "  Adjustment Coefficient (1 - rho):              + (1 - 0.50)\n"
        "  BAR Adjusted for ELB:                          * 1.00%\n"
        "-----------------------------------"
        "-----------------------------------\n"
        "  Adjusted BAR Estimate:                         0.75%\n"
        "\n==== Policy Prescription "
        "=============================================\n"
        "  The Adjusted BAR Estimate is 0.25% higher than the Current Fed \n"
        "  Rate. The Fed should consider raising the interest rate by 0.25%.\n"
        "\nNote:\n"
        "-BAR stands for Balanced Approach Rule.\n"
        "-BASR stands for Balanced Approach Shortfalls Rule.\n"
    )

    # Comparing the captured output with the expected output
    assert output == expected_output


if __name__ == '__main__':
    pytest.main()
