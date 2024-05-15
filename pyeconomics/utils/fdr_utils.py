def verbose_first_difference_rule(data):
    print(
        "\n==== Economic Indicators ========================================")
    print("Current Inflation:                           {:.2f}%".format(
        data['current_inflation_rate']))
    print("Target Inflation:                            {:.2f}%".format(
        data['inflation_target']))
    print("Current Unemployment Rate:                   {:.2f}%".format(
        data['current_unemployment_rate']))
    print("Lagged Unemployment Rate:                 {:.2f}%".format(
        data['lagged_unemployment_rate']))
    print("Natural Unemployment Rate:                   {:.2f}%".format(
        data['natural_unemployment_rate']))
    print("Lagged Natural Unemployment Rate:         {:.2f}%".format(
        data['lagged_natural_unemployment_rate']))
    print("Last Fed Rate:                               {:.2f}%".format(
        data['fed_rate']))

    print(
        "\n==== Gaps =======================================================")
    print("Inflation Gap:                               {:.2f}%".format(
        data['inflation_gap']))
    print("Current Unemployment Gap:                    {:.2f}%".format(
        data['current_unemployment_gap']))
    print("Lagged Unemployment Gap:                     {:.2f}%".format(
        data['lagged_unemployment_gap']))

    print(
        "\n==== First Difference Rule (FDR) ================================")
    print("  Last Fed Rate:                             {:.2f}%".format(
        data['fed_rate']))
    print("  Alpha * Inflation Gap:                     "
          "+ {:.2f} * {:.2f}%".format(
            data['alpha'], data['inflation_gap']))
    print("  Current Unemployment Gap Adjustment:       + {:.2f}%".format(
        data['current_unemployment_gap']))
    print("  Last Year Unemployment Gap Adjustment:     - {:.2f}%".format(
        data['lagged_unemployment_gap']))
    print(
        "-----------------------------------------------------------------")
    print("  Unadjusted FDR Estimate:                   {:.2f}%".format(
        data['unadjusted_fdr_rule']))

    print(
        "\n==== Adjusted First Difference Rule =============================")
    if data['apply_elb']:
        print("  Effective Lower Bound (ELB) Adjustment:")
        print(
            "  Maximum of FDR or ELB:                     "
            "max({:.2f}%, {:.2f}%)".format(
                data['unadjusted_fdr_rule'], data['elb']))
        print(
            "-----------------------------------------------------------------")
        print("  FDR Adjusted for ELB:                      {:.2f}%".format(
            data['adjusted_fdr_rule_after_elb']))

    print("\n  Policy Inertia Adjustment:")
    print("  Policy Inertia Coefficient (rho):          {:.2f}".format(
        data['rho']))
    print("  Last Fed Rate:                             * {:.2f}%".format(
        data['fed_rate']))
    print("  Adjustment Coefficient (1 - rho):          + (1 - {:.2f})".format(
        data['rho']))
    print(f"  FDR Adjusted for ELB:                      "
          f"* {data['adjusted_fdr_rule_after_elb']:.2f}%")
    print(
        "-----------------------------------------------------------------")
    print("  Adjusted FDR Estimate:                     {:.2f}%".format(
        data['adjusted_fdr_rule_after_inertia']))
