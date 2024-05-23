from datetime import datetime


def verbose_balanced_approach_rule(data: dict):
    """
    Print verbose output for the Balanced Approach Rule calculation.

    Args:
        data (dict): Dictionary containing the following keys:
            - current_inflation_rate (float): Current inflation rate.
            - inflation_target (float): Target inflation rate.
            - current_unemployment_rate (float): Current unemployment rate.
            - natural_unemployment_rate (float): Natural unemployment rate.
            - long_term_real_interest_rate (float): Long-term real interest
              rate.
            - current_fed_rate (float): Current Federal Reserve rate.
            - inflation_gap (float): Inflation gap.
            - unemployment_gap (float): Unemployment gap.
            - unadjusted_bar_rule (float): Unadjusted Balanced Approach Rule
              estimate.
            - adjusted_bar_after_elb (float): Balanced Approach Rule adjusted
              for the Effective Lower Bound (ELB).
            - adjusted_bar_after_inertia (float): Balanced Approach Rule
              adjusted for policy inertia.
            - rho (float): Policy inertia coefficient.
            - alpha (float): Coefficient for the inflation gap.
            - beta (float): Coefficient for the unemployment gap.
            - elb (float): Effective Lower Bound (ELB) rate.
            - apply_elb (bool): Whether to apply the ELB adjustment.
            - use_shortfalls_rule (bool): Whether to use the shortfalls rule.
            - use_shortfalls (bool): Whether to use the shortfalls gap.

    Returns:
        None
    """
    # Get the current date
    current_date = datetime.now().strftime("%B %d, %Y")

    # Determine if the shortfalls rule is being used
    rule_suffix = "Shortfalls " \
        if data.get('use_shortfalls_rule', False) else ""
    rule_acronym = f"BASR" if rule_suffix else "BAR"
    rule_name = f"Balanced Approach {rule_suffix}Rule (BASR)" \
        if rule_suffix else "Balanced Approach Rule"

    # Calculate the length of the line based on the rule name
    line_length = 67 + len(rule_acronym)

    print("\n==== Economic Indicators " + "=" * (line_length - 25))
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
        data['current_fed_rate']))
    print("As of Date:                                      {}".format(
        current_date))
    print("\n==== Gaps " + "=" * (line_length - 10))
    print("Inflation Gap:                                   {:.2f}%".format(
        data['inflation_gap']))
    if data.get('use_shortfalls', False):
        print("Unemployment Shortfall Gap:                      {:.2f}%".format(
            data['unemployment_gap']))
    else:
        print("Unemployment Gap:                                {:.2f}%".format(
            data['unemployment_gap']))
    print("\n==== {} ".format(rule_name) + "=" *
          (line_length - 6 - len(rule_name)))
    print("  Long-Term Real Interest Rate:                  {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("  Current Inflation:                             + {:.2f}%".format(
        data['current_inflation_rate']))
    print("  Alpha * Inflation Gap:                         "
          "+ {:.2f} * {:.2f}%".format(
            data['alpha'], data['inflation_gap']))
    print("  Beta * Unemployment Gap:                       "
          "+ {:.2f} * {:.2f}%".format(
            data['beta'], data['unemployment_gap']))
    print("-" * line_length)
    print("  Unadjusted {} Estimate:".format(rule_acronym).ljust(49) +
          "{:.2f}%".format(data['unadjusted_bar_rule']))
    print("\n==== Adjusted {} ".format(rule_name) + "=" *
          (line_length - 15 - len(rule_name)))
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment: ")
        print("  Maximum of {} or ELB:".format(rule_acronym).ljust(49) +
              "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_bar_rule'], data['elb']))
        print("-" * line_length)
        print("  {} Adjusted for ELB:".format(rule_acronym).ljust(49) +
              "{:.2f}%".format(data['adjusted_bar_after_elb']))
    print("\n  Policy Inertia Adjustment:              ")
    print("  Policy Inertia Coefficient (rho):              {:.2f}".format(
        data['rho']))
    print("  Current Fed Rate:                              * {:.2f}%".format(
        data['current_fed_rate']))
    print("  Adjustment Coefficient (1 - rho):              "
          "+ (1 - {:.2f})".format(data['rho']))
    print(f"  {rule_acronym} Adjusted for ELB:".ljust(49) +
          f"* {data['adjusted_bar_after_elb']:.2f}%")
    print("-" * line_length)
    print("  Adjusted {} Estimate:".format(rule_acronym).ljust(49) +
          "{:.2f}%".format(data['adjusted_bar_after_inertia']))

    # Policy Prescription section
    print("\n==== Policy Prescription " + "=" * (line_length - 25))
    rate_difference = (data['adjusted_bar_after_inertia'] - data['current_fed_rate'])
    rounded_difference = round(rate_difference * 4) / 4

    if rounded_difference > 0.125:
        print(f"  The Adjusted {rule_acronym} Estimate is "
              f"{rate_difference:.2f}% higher than the Current Fed \n"
              f"  Rate. The Fed should consider raising the interest "
              f"rate by {rounded_difference:.2f}%.")
    elif rounded_difference < -0.125:
        print(f"  The Adjusted {rule_acronym} Estimate is "
              f"{abs(rate_difference):.2f}% lower than the Current Fed \n"
              f"  Rate. The Fed should consider lowering the interest "
              f"rate by {abs(rounded_difference):.2f}%.")
    else:
        print(f"  The Adjusted {rule_acronym} Estimate is equal to the Current "
              f"Fed Rate.\n  The Fed should maintain the current interest "
              f"rate.")

    # Adding a note explaining BAR and BASR
    print("\nNote:")
    print("-BAR stands for Balanced Approach Rule.")
    print("-BASR stands for Balanced Approach Shortfalls Rule.")
