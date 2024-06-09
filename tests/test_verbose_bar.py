# tests/test_verbose_bar.py

import pytest
from datetime import datetime

from pyeconomics.verbose.balanced_approached_rule import (
    verbose_balanced_approach_rule
)


@pytest.fixture
def mock_data():
    return {
        'current_inflation_rate': 2.5,
        'inflation_target': 2.0,
        'current_unemployment_rate': 4.0,
        'natural_unemployment_rate': 4.5,
        'long_term_real_interest_rate': 2.0,
        'current_fed_rate': 0.5,
        'inflation_gap': 0.5,
        'unemployment_gap': 0.5,
        'alpha': 0.5,
        'beta': 0.5,
        'unadjusted_rate': 1.0,
        'adjusted_rate_after_elb': 1.0,
        'apply_elb': False,
        'elb': 0.0,
        'rho': 0.5,
        'adjusted_rate_after_inertia': 0.75,
        'use_shortfalls_rule': False,
        'include_ai_analysis': False,
        'max_tokens': 500,
        'model': 'chatgpt-4'
    }


def test_verbose_balanced_approach_rule(capsys, mock_data):
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "=============================================\n"
        "  Current Inflation:                             2.50%\n"
        "  Target Inflation:                              2.00%\n"
        "  Current Unemployment Rate:                     4.00%\n"
        "  Natural Unemployment Rate:                     4.50%\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Fed Rate:                              0.50%\n"
        f"  As of Date:                                    {as_of_date}\n"
        "\n==== Gaps "
        "============================================================\n"
        "  Inflation Gap:                                 0.50%\n"
        "  Unemployment Gap:                              0.50%\n"
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
    )

    assert output == expected_output


def test_verbose_balanced_approach_rule_shortfalls(capsys, mock_data):
    mock_data['use_shortfalls_rule'] = True
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "==============================================\n"
        "  Current Inflation:                             2.50%\n"
        "  Target Inflation:                              2.00%\n"
        "  Current Unemployment Rate:                     4.00%\n"
        "  Natural Unemployment Rate:                     4.50%\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Fed Rate:                              0.50%\n"
        f"  As of Date:                                    {as_of_date}\n"
        "\n==== Gaps "
        "=============================================================\n"
        "  Inflation Gap:                                 0.50%\n"
        "  Unemployment Shortfall Gap:                    0.50%\n"
        "\n==== Balanced Approach Shortfalls Rule (BASR) "
        "=========================\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Inflation:                             + 2.50%\n"
        "  Alpha * Inflation Gap:                         + 0.50 * 0.50%\n"
        "  Beta * Unemployment Gap:                       + 0.50 * 0.50%\n"
        "-----------------------------------"
        "------------------------------------\n"
        "  Unadjusted BASR Estimate:                      1.00%\n"
        "\n"
        "==== Adjusted Balanced Approach Shortfalls Rule (BASR) "
        "================\n"
        "\n  Policy Inertia Adjustment:              \n"
        "  Policy Inertia Coefficient (rho):              0.50\n"
        "  Current Fed Rate:                              * 0.50%\n"
        "  Adjustment Coefficient (1 - rho):              + (1 - 0.50)\n"
        "  BASR Adjusted for ELB:                         * 1.00%\n"
        "-----------------------------------"
        "------------------------------------\n"
        "  Adjusted BASR Estimate:                        0.75%\n"
        "\n==== Policy Prescription "
        "==============================================\n"
        "  The Adjusted BASR Estimate is 0.25% higher than the Current Fed \n"
        "  Rate. The Fed should consider raising the interest rate by 0.25%.\n"
        "\nNote:\n"
        "-BASR stands for Balanced Approach Shortfalls Rule.\n"
    )

    assert output == expected_output


def test_verbose_balanced_approach_rule_apply_elb(capsys, mock_data):
    mock_data['apply_elb'] = True
    mock_data['adjusted_rate_after_elb'] = 1.25
    mock_data['unadjusted_rate'] = 1.0
    mock_data['elb'] = 0.5
    mock_data['adjusted_rate_after_inertia'] = 0.88
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "=============================================\n"
        "  Current Inflation:                             2.50%\n"
        "  Target Inflation:                              2.00%\n"
        "  Current Unemployment Rate:                     4.00%\n"
        "  Natural Unemployment Rate:                     4.50%\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Fed Rate:                              0.50%\n"
        f"  As of Date:                                    {as_of_date}\n"
        "\n==== Gaps "
        "============================================================\n"
        "  Inflation Gap:                                 0.50%\n"
        "  Unemployment Gap:                              0.50%\n"
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
        "  Effective Lower Bound (ELB) Adjustment: \n"
        "  Maximum of BAR or ELB:                         max(1.00%, 0.50%)\n"
        "-----------------------------------"
        "-----------------------------------\n"
        "  BAR Adjusted for ELB:                          1.25%\n"
        "\n  Policy Inertia Adjustment:              \n"
        "  Policy Inertia Coefficient (rho):              0.50\n"
        "  Current Fed Rate:                              * 0.50%\n"
        "  Adjustment Coefficient (1 - rho):              + (1 - 0.50)\n"
        "  BAR Adjusted for ELB:                          * 1.25%\n"
        "-----------------------------------"
        "-----------------------------------\n"
        "  Adjusted BAR Estimate:                         0.88%\n"
        "\n==== Policy Prescription "
        "=============================================\n"
        "  The Adjusted BAR Estimate is 0.38% higher than the Current Fed \n"
        "  Rate. The Fed should consider raising the interest rate by 0.50%.\n"
        "\nNote:\n"
        "-BAR stands for Balanced Approach Rule.\n"
    )

    assert output == expected_output


def test_verbose_balanced_approach_rule_lower_rate(capsys, mock_data):
    mock_data['adjusted_rate_after_inertia'] = 0.25
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "=============================================\n"
        "  Current Inflation:                             2.50%\n"
        "  Target Inflation:                              2.00%\n"
        "  Current Unemployment Rate:                     4.00%\n"
        "  Natural Unemployment Rate:                     4.50%\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Fed Rate:                              0.50%\n"
        f"  As of Date:                                    {as_of_date}\n"
        "\n==== Gaps "
        "============================================================\n"
        "  Inflation Gap:                                 0.50%\n"
        "  Unemployment Gap:                              0.50%\n"
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
        "  Adjusted BAR Estimate:                         0.25%\n"
        "\n==== Policy Prescription "
        "=============================================\n"
        "  The Adjusted BAR Estimate is 0.25% lower than the Current Fed \n"
        "  Rate. The Fed should consider lowering the interest rate by 0.25%.\n"
        "\nNote:\n"
        "-BAR stands for Balanced Approach Rule.\n"
    )

    assert output == expected_output


def test_verbose_balanced_approach_rule_maintain_rate(capsys, mock_data):
    mock_data['adjusted_rate_after_inertia'] = 0.50
    verbose_balanced_approach_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    as_of_date = datetime.now().strftime("%B %d, %Y")
    expected_output = (
        "\n==== Economic Indicators "
        "=============================================\n"
        "  Current Inflation:                             2.50%\n"
        "  Target Inflation:                              2.00%\n"
        "  Current Unemployment Rate:                     4.00%\n"
        "  Natural Unemployment Rate:                     4.50%\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Fed Rate:                              0.50%\n"
        f"  As of Date:                                    {as_of_date}\n"
        "\n==== Gaps "
        "============================================================\n"
        "  Inflation Gap:                                 0.50%\n"
        "  Unemployment Gap:                              0.50%\n"
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
        "  Adjusted BAR Estimate:                         0.50%\n"
        "\n==== Policy Prescription "
        "=============================================\n"
        "  The Adjusted BAR Estimate is equal to the Current Fed Rate.\n"
        "  The Fed should maintain the current interest rate.\n"
        "\nNote:\n"
        "-BAR stands for Balanced Approach Rule.\n"
    )

    assert output == expected_output


if __name__ == '__main__':
    pytest.main()
