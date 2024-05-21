from datetime import datetime


def verbose_taylor_rule(data: dict):
    """
    Print verbose output for the Taylor Rule calculation.

    Args:
        data (dict): Dictionary containing the following keys:
            - current_inflation_rate (float): Current inflation rate.
            - inflation_target (float): Target inflation rate.
            - current_unemployment_rate (float): Current unemployment rate.
            - natural_unemployment_rate (float): Natural unemployment rate.
            - long_term_real_interest_rate (float): Long-term real interest
              rate.
            - fed_rate (float): Current Federal Reserve rate.
            - inflation_gap (float): Inflation gap.
            - unemployment_gap (float): Unemployment gap.
            - unadjusted_taylor_rule (float): Unadjusted Taylor Rule estimate.
            - adjusted_taylor_rule_after_elb (float): Taylor Rule adjusted for
                the Effective Lower Bound (ELB).
            - adjusted_taylor_rule_after_inertia (float): Taylor Rule adjusted
                for policy inertia.
            - rho (float): Policy inertia coefficient.
            - alpha (float): Coefficient for the inflation gap.
            - beta (float): Coefficient for the Okun factor multiplied by the
                unemployment gap.
            - okun_factor (float): Okun factor.
            - elb (float): Effective Lower Bound (ELB) rate.
            - apply_elb (bool): Whether to apply the ELB adjustment.

    Returns:
        None
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    print("\n==== Economic Indicators ========================================="
          "========")
    print("Current Inflation:                               {:.2f}%".format(
        data['current_inflation_rate']))
    print("Target Inflation:                                {:.2f}%".format(
        data['inflation_target']))
    print("Current Unemployment Rate:                       {:.2f}%".format(
        data['current_unemployment_rate']))
    print("Natural Unemployment Rate:                       {:.2f}%".format(
        data['natural_unemployment_rate']))
    print("Long-Term Real Interest Rate:                    {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("Current Fed Rate:                                {:.2f}%".format(
        data['fed_rate']))
    print("As of Date:                                      {}".format(
        current_date))
    print("\n==== Gaps ========================================================"
          "========")
    print("Inflation Gap:                                   {:.2f}%".format(
        data['inflation_gap']))
    print("Unemployment Gap:                                {:.2f}%".format(
        data['unemployment_gap']))
    print("\n==== Taylor Rule ================================================="
          "========")
    print("  Long-Term Real Interest Rate:                  {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("  Current Inflation:                             + {:.2f}%".format(
        data['current_inflation_rate']))
    print("  Alpha * Inflation Gap:                         "
          "+ {:.2f} * {:.2f}%".format(
            data['alpha'], data['inflation_gap']))
    print("  Beta * Okun Factor * Unemployment Gap:         "
          "+ {:.2f} * {:.2f} * {:.2f}%".format(
            data['beta'], data['okun_factor'], data['unemployment_gap']))
    print("--------------------------------------------------------------------"
          "------")
    print("  Unadjusted Taylor Rule Estimate:               {:.2f}%".format(
        data['unadjusted_taylor_rule']))
    print("\n==== Adjusted Taylor Rule ========================================"
          "========")
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment: ")
        print(
            "  Maximum of Taylor Rule or ELB:                 "
            "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_taylor_rule'], data['elb']))
        print("----------------------------------------------------------------"
              "----------")
        print("  Taylor Rule Adjusted for ELB:                  {:.2f}%".format(
            data['adjusted_taylor_rule_after_elb']))
    print("\n  Policy Inertia Adjustment:              ")
    print("  Policy Inertia Coefficient (rho):              {:.2f}".format(
        data['rho']))
    print("  Current Fed Rate:                              * {:.2f}%".format(
        data['fed_rate']))
    print("  Adjustment Coefficient (1 - rho):              "
          "+ (1 - {:.2f})".format(data['rho']))
    print("  Taylor Rule Adjusted for ELB:                  * {:.2f}%".format(
        data['adjusted_taylor_rule_after_elb']))
    print("--------------------------------------------------------------------"
          "------")
    print("  Adjusted Taylor Rule Estimate:                 {:.2f}%".format(
        data['adjusted_taylor_rule_after_inertia']))
    print("\n==== Policy Prescription ========================================="
          "========")
    rate_difference = (data['adjusted_taylor_rule_after_inertia'] -
                       data['fed_rate'])
    rounded_difference = round(rate_difference * 4) / 4

    if rounded_difference > 0.125:
        print("  The Adjusted Taylor Rule Estimate is {:.2f}% higher than the "
              "Current \n  Fed Rate. The Fed should consider raising the "
              "interest rate by {:.2f}%.".format(
                rate_difference, rounded_difference))
    elif rounded_difference < -0.125:
        print("  The Adjusted Taylor Rule Estimate is {:.2f}% lower than the "
              "Current \n  Fed Rate. The Fed should consider lowering the "
              "interest rate by {:.2f}%.".format(
                abs(rate_difference), rounded_difference))
    else:
        print("  The Adjusted Taylor Rule Estimate is equal to the Current "
              "Fed Rate.\n  The Fed should maintain the current interest rate.")
