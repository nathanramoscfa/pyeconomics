def verbose_taylor_rule(data):
    print("\n==== Economic Indicators ========================================="
          "=")
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
    print("\n==== Gaps ========================================================"
          "=")
    print("Inflation Gap:                            {:.2f}%".format(
        data['inflation_gap']))
    print("Unemployment Gap:                         {:.2f}%".format(
        data['unemployment_gap']))
    print("\n==== Taylor Rule ================================================="
          "=")
    print("  Long-Term Real Interest Rate:           {:.2f}%".format(
        data['long_term_real_interest_rate']))
    print("  Current Inflation:                      + {:.2f}%".format(
        data['current_inflation_rate']))
    print("  Alpha * Inflation Gap:                  + {:.2f} * {:.2f}%".format(
        data['alpha'], data['inflation_gap']))
    print("  Beta * Okun Factor * Unemployment Gap:  "
          "+ {:.2f} * {:.2f} * {:.2f}%".format(
            data['beta'], data['okun_factor'], data['unemployment_gap']))
    print("-------------------------------------------------------------------")
    print("  Unadjusted Taylor Rule Estimate:        {:.2f}%".format(
        data['unadjusted_taylor_rule']))
    print("\n==== Adjusted Taylor Rule ========================================"
          "=")
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment: ")
        print(
            "  Maximum of Taylor Rule or ELB:          "
            "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_taylor_rule'], data['elb']))
        print("----------------------------------------------------------------"
              "---")
        print("  Taylor Rule Adjusted for ELB:           {:.2f}%".format(
            data['adjusted_taylor_rule_after_elb']))
    print("\n  Policy Inertia Adjustment:              ")
    print("  Policy Inertia Coefficient (rho):       {:.2f}".format(
        data['rho']))
    print("  Current Fed Rate:                       * {:.2f}%".format(
        data['fed_rate']))
    print("  Adjustment Coefficient (1 - rho):       + (1 - {:.2f})".format(
        data['rho']))
    print("  Taylor Rule Adjusted for ELB:           * {:.2f}%".format(
        data['adjusted_taylor_rule_after_elb']))
    print("-------------------------------------------------------------------")
    print("  Adjusted Taylor Rule Estimate:          {:.2f}%".format(
        data['adjusted_taylor_rule_after_inertia']))
