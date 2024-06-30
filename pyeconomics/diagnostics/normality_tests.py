# pyeconomics/diagnostics/normality_tests.py

import pandas as pd
import statsmodels.api as sm
from scipy.stats import anderson, kstest, normaltest, shapiro


def shapiro_wilk_test(residuals: pd.Series) -> None:
    """
    Perform Shapiro-Wilk test for normality of residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    sw_test_stat, sw_test_p = shapiro(residuals[:5000])
    print("\nShapiro-Wilk Test for Normality of Residuals:")
    print(f"  Shapiro-Wilk test statistic: {sw_test_stat:.3f}, p-value: "
          f"{sw_test_p:.3e}")
    if sw_test_p < 0.05:
        print("  Interpretation: The residuals are not normally distributed.")
    else:
        print("  Interpretation: The residuals are normally distributed.")


def kolmogorov_smirnov_test(residuals: pd.Series) -> None:
    """
    Perform Kolmogorov-Smirnov test for normality of residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    ks_test_stat, ks_test_p = kstest(
        residuals, 'norm', args=(residuals.mean(), residuals.std())
    )
    print("\nKolmogorov-Smirnov Test for Normality of Residuals:")
    print(f"  Kolmogorov-Smirnov test statistic: {ks_test_stat:.3f}, p-value: "
          f"{ks_test_p:.3e}")
    if ks_test_p < 0.05:
        print("  Interpretation: The residuals are not normally distributed.")
    else:
        print("  Interpretation: The residuals are normally distributed.")


def anderson_darling_test(residuals: pd.Series) -> None:
    """
    Perform Anderson-Darling test for normality of residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    ad_test = anderson(residuals)
    print("\nAnderson-Darling Test for Normality of Residuals:")
    print(f"  Anderson-Darling test statistic: {ad_test.statistic:.3f}")
    for i in range(len(ad_test.critical_values)):
        sl, cv = ad_test.significance_level[i], ad_test.critical_values[i]
        print(f"  Significance Level: {sl:.1f}%, Critical Value: {cv:.3f}")
    if ad_test.statistic > ad_test.critical_values[2]:  # 5% significance level
        print("  Interpretation: The residuals are not normally distributed.")
    else:
        print("  Interpretation: The residuals are normally distributed.")


def jarque_bera_test(residuals: pd.Series) -> None:
    """
    Perform Jarque-Bera test for normality of residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    jb_test_stat, jb_test_p, _, _ = sm.stats.jarque_bera(residuals)
    print("\nJarque-Bera Test for Normality of Residuals:")
    print(f"  Jarque-Bera test statistic: {jb_test_stat:.3f}, p-value: "
          f"{jb_test_p:.3e}")
    if jb_test_p < 0.05:
        print("  Interpretation: The residuals are not normally distributed.")
    else:
        print("  Interpretation: The residuals are normally distributed.")


def dagostino_k_squared_test(residuals: pd.Series) -> None:
    """
    Perform D'Agostino's K-squared test for normality of residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    dagostino_test_stat, dagostino_test_p = normaltest(residuals)
    print("\nD'Agostino's K-squared Test for Normality of Residuals:")
    print(f"  D'Agostino's K-squared test statistic: "
          f"{dagostino_test_stat:.3f}, p-value: {dagostino_test_p:.3e}")
    if dagostino_test_p < 0.05:
        print("  Interpretation: The residuals are not normally distributed.")
    else:
        print("  Interpretation: The residuals are normally distributed.")


def normality_tests(residuals: pd.Series) -> None:
    """
    Perform all normality tests for residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    shapiro_wilk_test(residuals)
    kolmogorov_smirnov_test(residuals)
    anderson_darling_test(residuals)
    jarque_bera_test(residuals)
    dagostino_k_squared_test(residuals)
