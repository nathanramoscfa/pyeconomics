def verbose_bar_rule(data):
    # Determine if the shortfalls rule is being used
    rule_suffix = "Shortfalls " \
        if data.get('use_shortfalls_rule', False) else ""
    rule_name = f"BASR" if rule_suffix else "BAR"

    # Calculate the length of the line based on the rule name
    line_length = 65 + len(rule_name)

    print("\n==== Economic Indicators " + "=" * (line_length - 25))
    print("Current Inflation:                        {:.2f}%".format(
        data['current_inflation_rate']))
    print("Target Inflation:                         {:.2f}%".format(
        data['inflation_target']))
    print("Current Unemployment Rate:                {:.2f}%".format(
        data['current_unemployment_rate']))
    print("Natural Unemployment Rate:                {:.2f}%".format(
        data['natural_unemployment_rate']))
    print("Long-Term Real Interest Rate:             {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("Current Fed Rate:                         {:.2f}%".format(
        data['fed_rate']))
    print("\n==== Gaps " + "=" * (line_length - 10))
    print("Inflation Gap:                            {:.2f}%".format(
        data['inflation_gap']))
    if data.get('use_shortfalls', False):
        print("Unemployment Shortfall Gap:               {:.2f}%".format(
            data['unemployment_gap']))
    else:
        print("Unemployment Gap:                         {:.2f}%".format(
            data['unemployment_gap']))
    print("\n==== {} ".format(rule_name) + "=" *
          (line_length - 6 - len(rule_name)))
    print("  Long-Term Real Interest Rate:           {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("  Current Inflation:                      + {:.2f}%".format(
        data['current_inflation_rate']))
    print("  Alpha * Inflation Gap:                  + {:.2f} * {:.2f}%".format(
        data['alpha'], data['inflation_gap']))
    print("  Beta * Unemployment Gap:                + {:.2f} * {:.2f}%".format(
        data['beta'], data['unemployment_gap']))
    print("-" * line_length)
    print("  Unadjusted {} Estimate:".format(rule_name).ljust(42) +
          "{:.2f}%".format(data['unadjusted_bar_rule']))
    print("\n==== Adjusted {} ".format(rule_name) + "=" *
          (line_length - 15 - len(rule_name)))
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment: ")
        print("  Maximum of {} or ELB:".format(rule_name).ljust(42) +
              "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_bar_rule'], data['elb']))
        print("-" * line_length)
        print("  {} Adjusted for ELB:".format(rule_name).ljust(42) +
              "{:.2f}%".format(data['adjusted_bar_after_elb']))
    print("\n  Policy Inertia Adjustment:              ")
    print("  Policy Inertia Coefficient (rho):       {:.2f}".format(
        data['rho']))
    print("  Current Fed Rate:                       * {:.2f}%".format(
        data['fed_rate']))
    print("  Adjustment Coefficient (1 - rho):       + (1 - {:.2f})".format(
        data['rho']))
    print(f"  {rule_name} Adjusted for ELB:".ljust(42) +
          f"* {data['adjusted_bar_after_elb']:.2f}%")
    print("-" * line_length)
    print("  Adjusted {} Estimate:".format(rule_name).ljust(42) +
          "{:.2f}%".format(data['adjusted_bar_after_inertia']))
    # Adding a note explaining BAR and BASR
    print("\nNote:")
    print("BAR stands for Balanced Approach Rule.")
    print("BASR stands for Balanced Approach Shortfalls Rule.")
