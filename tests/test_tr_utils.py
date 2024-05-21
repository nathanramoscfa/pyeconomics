# pyeconomics/tests/test_tr_utils.py
import pytest

from pyeconomics.utils.tr_utils import verbose_taylor_rule


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
        'okun_factor': 2.0,
        'unadjusted_taylor_rule': 1.0,
        'adjusted_taylor_rule_after_elb': 1.0,
        'apply_elb': False,
        'elb': 0.0,
        'rho': 0.5,
        'adjusted_taylor_rule_after_inertia': 0.75
    }


def test_verbose_taylor_rule(capsys, mock_data):
    verbose_taylor_rule(mock_data)

    captured = capsys.readouterr()
    output = captured.out

    expected_output = (
        "==== Economic Indicators "
        "=================================================\n"
        "Current Inflation:                               2.50%\n"
        "Target Inflation:                                2.00%\n"
        "Current Unemployment Rate:                       4.00%\n"
        "Natural Unemployment Rate:                       4.50%\n"
        "Long-Term Real Interest Rate:                    2.00%\n"
        "Current Fed Rate:                                0.50%\n"
        "As of Date:                                      May 21, 2024\n"
        "\n==== Gaps "
        "================================================================\n"
        "Inflation Gap:                                   0.50%\n"
        "Unemployment Gap:                                0.50%\n"
        "\n==== Taylor Rule "
        "=========================================================\n"
        "  Long-Term Real Interest Rate:                  2.00%\n"
        "  Current Inflation:                             + 2.50%\n"
        "  Alpha * Inflation Gap:                         + 0.50 * 0.50%\n"
        "  Beta * Okun Factor * Unemployment Gap:         "
        "+ 0.50 * 2.00 * 0.50%\n"
        "-------------------------------------"
        "-------------------------------------\n"
        "  Unadjusted Taylor Rule Estimate:               1.00%\n"
        "\n==== Adjusted Taylor Rule "
        "================================================\n"
        "\n  Policy Inertia Adjustment:              \n"
        "  Policy Inertia Coefficient (rho):              0.50\n"
        "  Current Fed Rate:                              * 0.50%\n"
        "  Adjustment Coefficient (1 - rho):              + (1 - 0.50)\n"
        "  Taylor Rule Adjusted for ELB:                  * 1.00%\n"
        "-------------------------------------"
        "-------------------------------------\n"
        "  Adjusted Taylor Rule Estimate:                 0.75%\n"
        "\n==== Policy Prescription "
        "=================================================\n"
        "  The Adjusted Taylor Rule Estimate is 0.25% higher than the "
        "Current \n  Fed Rate. The Fed should consider raising the interest "
        "rate by 0.25%."
    )

    # Comparing the captured output with the expected output
    assert output.strip() == expected_output.strip()


if __name__ == '__main__':
    pytest.main()
