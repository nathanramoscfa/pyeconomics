from datetime import datetime


def verbose_first_difference_rule(data: dict):
    """
    Print verbose output for the First Difference Rule calculation.

    Args:
        data (dict): Dictionary containing the following keys:
            - current_inflation_rate (float): Current inflation rate.
            - inflation_target (float): Target inflation rate.
            - current_unemployment_rate (float): Current unemployment rate.
            - lagged_unemployment_rate (float): Lagged unemployment rate.
            - natural_unemployment_rate (float): Natural unemployment rate.
            - lagged_natural_unemployment_rate (float): Lagged natural
              unemployment rate.
            - fed_rate (float): Current Federal Reserve rate.
            - inflation_gap (float): Inflation gap.
            - current_unemployment_gap (float): Current unemployment gap.
            - lagged_unemployment_gap (float): Lagged unemployment gap.
            - alpha (float): Coefficient for the inflation gap.
            - rho (float): Policy inertia coefficient.
            - elb (float): Effective Lower Bound (ELB) rate.
            - apply_elb (bool): Whether to apply the ELB adjustment.
            - unadjusted_fdr_rule (float): Unadjusted First Difference Rule
              estimate.
            - adjusted_fdr_rule_after_elb (float): First Difference Rule
              adjusted for the Effective Lower Bound (ELB).
            - adjusted_fdr_rule_after_inertia (float): First Difference Rule
              adjusted for policy inertia.

    Returns:
        None
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    print(
        "\n==== Economic Indicators ==========================================="
        "=")
    print("Current Inflation:                               {:.2f}%".format(
        data['current_inflation_rate']))
    print("Target Inflation:                                {:.2f}%".format(
        data['inflation_target']))
    print("Current Unemployment Rate:                       {:.2f}%".format(
        data['current_unemployment_rate']))
    print("Lagged Unemployment Rate:                        {:.2f}%".format(
        data['lagged_unemployment_rate']))
    print("Natural Unemployment Rate:                       {:.2f}%".format(
        data['natural_unemployment_rate']))
    print("Lagged Natural Unemployment Rate:                {:.2f}%".format(
        data['lagged_natural_unemployment_rate']))
    print("Last Fed Rate:                                   {:.2f}%".format(
        data['fed_rate']))
    print("As of Date:                                      {}".format(
        current_date))

    print(
        "\n==== Gaps =========================================================="
        "=")
    print("Inflation Gap:                                   {:.2f}%".format(
        data['inflation_gap']))
    print("Current Unemployment Gap:                        {:.2f}%".format(
        data['current_unemployment_gap']))
    print("Lagged Unemployment Gap:                         {:.2f}%".format(
        data['lagged_unemployment_gap']))

    print(
        "\n==== First Difference Rule (FDR) ==================================="
        "=")
    print("  Last Fed Rate:                                 {:.2f}%".format(
        data['fed_rate']))
    print("  Alpha * Inflation Gap:                         "
          "+ {:.2f} * {:.2f}%".format(
            data['alpha'], data['inflation_gap']))
    print("  Current Unemployment Gap Adjustment:           + {:.2f}%".format(
        data['current_unemployment_gap']))
    print("  Last Year Unemployment Gap Adjustment:         - {:.2f}%".format(
        data['lagged_unemployment_gap']))
    print(
        "---------------------------------------------------------------------")
    print("  Unadjusted FDR Estimate:                       {:.2f}%".format(
        data['unadjusted_fdr_rule']))

    print(
        "\n==== Adjusted First Difference Rule ================================"
        "=")
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment:")
        print(
            "  Maximum of FDR or ELB:                         "
            "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_fdr_rule'], data['elb']))
        print(
            "------------------------------------------------------------------"
            "---")
        print("  FDR Adjusted for ELB:                          {:.2f}%".format(
            data['adjusted_fdr_rule_after_elb']))

    print("\n  Policy Inertia Adjustment:")
    print("  Policy Inertia Coefficient (rho):              {:.2f}".format(
        data['rho']))
    print("  Last Fed Rate:                                 * {:.2f}%".format(
        data['fed_rate']))
    print("  Adjustment Coefficient (1 - rho):              "
          "+ (1 - {:.2f})".format(data['rho']))
    print(f"  FDR Adjusted for ELB:                         "
          f" * {data['adjusted_fdr_rule_after_elb']:.2f}%")
    print(
        "---------------------------------------------------------------------")
    print("  Adjusted FDR Estimate:                         {:.2f}%".format(
        data['adjusted_fdr_rule_after_inertia']))

    # Policy Prescription section
    print("\n==== Policy Prescription ========================================="
          "========")
    rate_difference = (data['adjusted_fdr_rule_after_inertia'] -
                       data['fed_rate'])
    rounded_difference = round(rate_difference * 4) / 4

    if rounded_difference > 0.125:
        print(f"  The Adjusted FDR Estimate is "
              f"{rate_difference:.2f}% higher than the Current Fed \n"
              f"  Rate. The Fed should consider raising the interest "
              f"rate by {rounded_difference:.2f}%.")
    elif rounded_difference < -0.125:
        print(f"  The Adjusted FDR Estimate is "
              f"{abs(rate_difference):.2f}% lower than the Current Fed \n"
              f"  Rate. The Fed should consider lowering the interest "
              f"rate by {abs(rounded_difference):.2f}%.")
    else:
        print(f"  The Adjusted FDR Estimate is equal to the Current "
              f"Fed Rate.\n  The Fed should maintain the current interest "
              f"rate.")
