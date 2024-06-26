.. PyEconomics documentation master file, created by
   sphinx-quickstart on Sun May 23 2024.

Welcome to PyEconomics's documentation!
========================================

.. image:: _static/logo.png
   :alt: PyEconomics Logo

**PyEconomics** is a Python library for economic and financial analysis,
designed to provide tools and models for analyzing various aspects of economic,
financial, and fiscal policy. Whether you're a developer, economist, financial
analyst, or researcher, PyEconomics aims to be your go-to resource for
sophisticated economic modeling and analysis.

.. list-table::
   :header-rows: 1

   * - Category
     - Badge
   * - **Testing**
     - .. raw:: html

           <a href="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/tests.yml"><img src="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/tests.yml/badge.svg" alt="pytest"></a>
           <a href="https://codecov.io/gh/nathanramoscfa/pyeconomics"><img src="https://codecov.io/gh/nathanramoscfa/pyeconomics/graph/badge.svg?token=I1CRHDN73S" alt="codecov"></a>
   * - **Package**
     - .. raw:: html

           <a href="https://pypi.org/project/pyeconomics/"><img src="https://img.shields.io/pypi/v/pyeconomics.svg" alt="PyPI Latest Release"></a>
           <img src="https://img.shields.io/pypi/pyversions/pyeconomics" alt="Python Version">
           <a href="https://pepy.tech/project/pyeconomics"><img src="https://static.pepy.tech/badge/pyeconomics" alt="PyPI Downloads"></a>
           <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-brightgreen.svg" alt="License: MIT"></a>
   * - **Documentation**
     - .. raw:: html

           <a href="https://pyeconomics.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/pyeconomics/badge/?version=latest" alt="Documentation Status"></a>
   * - **Release**
     - .. raw:: html

           <a href="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/release.yml"><img src="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/release.yml/badge.svg" alt="Release Status"></a>
   * - **Build Status**
     - .. raw:: html

           <a href="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/tests.yml"><img src="https://github.com/nathanramoscfa/pyeconomics/actions/workflows/tests.yml/badge.svg" alt="Build Status"></a>
   * - **Maintainability**
     - .. raw:: html

           <a href="https://codeclimate.com/github/nathanramoscfa/pyeconomics/maintainability"><img src="https://api.codeclimate.com/v1/badges/8d0d8b5a5bed8fe94814/maintainability" alt="Maintainability"></a>
   * - **Code Style**
     - .. raw:: html

           <a href="https://github.com/PyCQA/flake8"><img src="https://img.shields.io/badge/code%20style-flake8-brightgreen.svg" alt="Code Style: Flake8"></a>
   * - **Dependencies**
     - .. raw:: html

           <a href="https://libraries.io/github/nathanramoscfa/pyeconomics"><img src="https://img.shields.io/librariesio/github/nathanramoscfa/pyeconomics" alt="Dependency Status"></a>
   * - **Security**
     - .. raw:: html

           <a href="https://snyk.io/test/github/nathanramoscfa/pyeconomics"><img src="https://snyk.io/test/github/nathanramoscfa/pyeconomics/badge.svg" alt="Security Status"></a>

Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   features
   installation
   api_key
   usage
   docker
   roadmap
   contributing
   contact

Introduction
============

PyEconomics is a versatile and comprehensive library that integrates various
economic and financial models. It is designed to support the development and
analysis of monetary policy rules, exchange rate models, macroeconomic and
microeconomic models, discounted cash flow models, and much more.

Features
========

Current Features
----------------

- **Monetary Policy Rules**: Implementation of well-known monetary policy rules.
- **Cache Management**: Efficient caching for API calls to improve performance
  and reduce redundant data fetching.

Planned Features
----------------

- **Exchange Rate Models**: Models for predicting future exchange rates.
- **Macroeconomic Models**: Comprehensive macroeconomic models.
- **Microeconomic Models**: Detailed microeconomic models.
- **Discounted Cash Flow Models**: Advanced models for discounted cash flow
  analysis.
- **Financial Models**: Including CAPM and portfolio optimization.
- **Fiscal Policy Models**: Tools to analyze taxation, government spending, and
  public debt.
- **Additional Economic Models**: Support for behavioral economics, agent-based
  models, and international trade models.

Installation
============

To install PyEconomics, use ``pip``:

.. code-block:: sh

   pip install pyeconomics

From Source
-----------

If you want to install the package from the source code, follow these steps:

1. Clone the repository:

    .. code-block:: sh

       git clone https://github.com/nathanramoscfa/pyeconomics.git

2. Change to the project directory:

    .. code-block:: sh

       cd pyeconomics

3. Install the package:

    .. code-block:: sh

       pip install .

API Key
=======

Some features of PyEconomics require access to the FRED API. To use these
features, you need to configure your FRED API access.

A detailed step-by-step guide on obtaining and securely storing your FRED API
key is available here:

- `FRED API Key Configuration Guide (Markdown) <markdown/FRED_API_CONFIGURATION.md>`_
- `FRED API Key Configuration Guide (Jupyter Notebook) <examples/api_configuration/fred_api_configuration.ipynb>`_

Usage
=====

Here are some basic examples of how to use PyEconomics for calculating and visualizing monetary policy rules.

Example 1: Calculate Current Policy Rule Estimates
--------------------------------------------------

.. code-block:: python

   # Import pyeconomics
   import pyeconomics as pyecon

   # Calculate policy rule estimates
   policy_estimates = pyecon.calculate_policy_rule_estimates(verbose=True)

Verbose Print Statement:

.. code-block:: none

   ┌───────────────────────────────────────────────────────────────────────────────────┐
   │                           Interest Rate Policy Estimates                          │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Taylor Rule (TR)                                                      6.17%       │
   │ Balanced Approach Rule (BAR)                                          6.68%       │
   │ Balanced Approach Shortfalls Rule (BASR)                              5.66%       │
   │ First Difference Rule (FDR)                                           5.97%       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Federal Funds Rate (FFR)                                              5.50%       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ As of Date                                                     May 20, 2024       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │                                Policy Prescription                                │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Taylor Rule (TR) suggests raising the rate by 0.75%.                              │
   │ Balanced Approach Rule (BAR) suggests raising the rate by 1.25%.                  │
   │ Balanced Approach Shortfalls Rule (BASR) suggests raising the rate by 0.25%.      │
   │ First Difference Rule (FDR) suggests raising the rate by 0.50%.                   │
   └───────────────────────────────────────────────────────────────────────────────────┘

Example 2: Adjust Taylor Rule for Effective Lower Bound (ELB) and Policy Inertia
--------------------------------------------------------------------------------

.. code-block:: python

   # Import pyeconomics
   import pyeconomics as pyecon

   # Adjustment Parameters
   rho = 0.7  # Policy Inertia Coefficient
   apply_elb = True  # Apply Effective Lower Bound

   adjusted_policy_estimates = pyecon.calculate_policy_rule_estimates(
       rho=rho,
       apply_elb=apply_elb,
       verbose=True
   )

Verbose Print Statement:

.. code-block:: none

   ┌───────────────────────────────────────────────────────────────────────────────────┐
   │                      Adjusted Interest Rate Policy Estimates                      │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Taylor Rule (TR)                                                      5.70%       │
   │ Balanced Approach Rule (BAR)                                          5.86%       │
   │ Balanced Approach Shortfalls Rule (BASR)                              5.55%       │
   │ First Difference Rule (FDR)                                           5.64%       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Federal Funds Rate (FFR)                                              5.50%       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ As of Date                                                     May 21, 2024       │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │                            Adjusted Policy Prescription                           │
   ├───────────────────────────────────────────────────────────────────────────────────┤
   │ Taylor Rule (TR) suggests raising the rate by 0.25%.                              │
   │ Balanced Approach Rule (BAR) suggests raising the rate by 0.25%.                  │
   │ Balanced Approach Shortfalls Rule (BASR) suggests maintaining the current rate.   │
   │ First Difference Rule (FDR) suggests raising the rate by 0.25%.                   │
   └───────────────────────────────────────────────────────────────────────────────────┘

Example 3: Calculate Current Taylor Rule Estimates
--------------------------------------------------

.. code-block:: python

   # Import pyeconomics modules
   import pyeconomics as pyecon

   # Calculate policy rule estimates
   policy_estimates = pyecon.taylor_rule(verbose=True)

Verbose Print Statement:

.. code-block:: none

   ==== Economic Indicators =================================================
   Current Inflation:                               3.04%
   Target Inflation:                                2.00%
   Current Unemployment Rate:                       3.90%
   Natural Unemployment Rate:                       4.41%
   Long-Term Real Interest Rate:                    2.10%
   Current Fed Rate:                                5.50%
   As of Date:                                      May 21, 2024

   ==== Gaps ================================================================
   Inflation Gap:                                   1.04%
   Unemployment Gap:                                0.51%

   ==== Taylor Rule =========================================================
     Long-Term Real Interest Rate:                  2.10%
     Current Inflation:                             + 3.04%
     Alpha * Inflation Gap:                         + 0.50 * 1.04%
     Beta * Okun Factor * Unemployment Gap:         + 0.50 * 2.00 * 0.51%
   --------------------------------------------------------------------------
     Unadjusted Taylor Rule Estimate:               6.17%

   ==== Adjusted Taylor Rule ================================================
     Effective Lower Bound (ELB) Adjustment:
     Maximum of Taylor Rule or ELB:                 max(6.17%, 0.12%)
   --------------------------------------------------------------------------
     Taylor Rule Adjusted for ELB:                  6.17%

     Policy Inertia Adjustment:
     Policy Inertia Coefficient (rho):              0.70
     Current Fed Rate:                              * 5.50%
     Adjustment Coefficient (1 - rho):              + (1 - 0.70)
     Taylor Rule Adjusted for ELB:                  * 6.17%
   --------------------------------------------------------------------------
     Adjusted Taylor Rule Estimate:                 5.70%

   ==== Policy Prescription =================================================
     The Adjusted Taylor Rule Estimate is 0.20% higher than the Current
     Fed Rate. The Fed should consider raising the interest rate by 0.25%.

Example 4: Calculate and Plot Historical Policy Rule Estimates
--------------------------------------------------------------

.. code-block:: python

   # Import pyeconomics modules
   import pyeconomics as pyecon

   # Calculate historical policy rates
   historical_policy_estimates = pyecon.calculate_historical_policy_rates().dropna()

   # Plot historical policy rates
   pyecon.plot_historical_rule_estimates(historical_policy_estimates)

.. image:: ../media/plot_historical_policy_rates.png

Example 5: Calculate and Plot the Adjusted Historical Policy Rules
------------------------------------------------------------------

.. code-block:: python

   # Import pyeconomics modules
   import pyeconomics as pyecon

   # Adjustment Parameters
   rho = 0.7  # Policy Inertia Coefficient
   apply_elb = True  # Apply Effective Lower Bound

   # Calculate adjusted historical policy rates
   adjusted_historical_policy_estimates = pyecon.calculate_historical_policy_rates(
       rho=rho,
       apply_elb=apply_elb
   ).dropna()

   # Plot adjusted historical policy rates
   pyecon.plot_historical_rule_estimates(
       adjusted_historical_policy_estimates,
       adjusted=True
   )

.. image:: ../media/plot_adj_historical_rates.png

Examples
========

For more comprehensive examples, refer to the `examples <examples>`_ directory in
the repository.

Roadmap
=======

The following models and categories are planned for future development.
`Contributions <contributing>`_ are welcome!

.. rubric:: Monetary Policy Models

- Taylor Rule
- Balanced Approach Rule
- First Difference Rule
- McCallum Rule
- Orphanides Rule
- Friedman Rule
- Interest Rate Smoothing Models

.. rubric:: Quantity of Money Theory

- Fisher Equation
- Cambridge Equation
- Velocity of Money Models
- Quantity Theory of Money (QTM)
- Money Demand Function (Md)

.. rubric:: Economic Models to Predict Future Exchange Rates

- Purchasing Power Parity (PPP)
- Interest Rate Parity (IRP)
- Monetary Models of Exchange Rates
- Portfolio Balance Models
- Behavioral Equilibrium Exchange Rate (BEER)
- Fundamental Equilibrium Exchange Rate (FEER)

.. rubric:: Macroeconomic Models

- IS-LM Model
- AD-AS Model
- Solow Growth Model
- New Keynesian Models
- RBC (Real Business Cycle) Model
- DSGE (Dynamic Stochastic General Equilibrium) Models

.. rubric:: Microeconomic Models

- Supply and Demand Models
- Consumer Choice Theory
- Production Theory
- Cost Functions
- Game Theory Models
- Market Structure Models (Perfect Competition, Monopoly, Oligopoly)

.. rubric:: Discounted Cash Flow Models

- Dividend Discount Model (DDM)
- Free Cash Flow to Equity (FCFE)
- Free Cash Flow to Firm (FCFF)
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Adjusted Present Value (APV)

.. rubric:: Financial Models

- Capital Asset Pricing Model (CAPM)
- Arbitrage Pricing Theory (APT)
- Black-Scholes Option Pricing Model
- Bond Valuation Models
- Credit Risk Models (e.g., Merton Model)
- Portfolio Optimization Models (e.g., Markowitz Model)

.. rubric:: Fiscal Policy Models

- Taxation and Government Spending Models
- Budget Deficit Models
- Public Debt Models
- Fiscal Multiplier Models
- Laffer Curve
- Ricardian Equivalence

.. rubric:: Other Well-Known Economic Models

- Behavioral Economics Models
- Agent-Based Models
- Environmental Economics Models
- International Trade Models (e.g., Heckscher-Ohlin Model)
- Labor Market Models
- Health Economics Models

Contributing
============

Contributions are welcome! If you have a model you'd like to implement or an
improvement to an existing model, please refer to our detailed
`Contributing Guide <markdown/CONTRIBUTING.md>`_.

By participating in this project, you agree to abide by the
`Code of Conduct <markdown/CODE_OF_CONDUCT.md>`_.

Thank you for your contributions!

Contact
=======

If you have any questions, suggestions, or need support, feel free to reach out.

Nathan Ramos, CFA
-----------------

Welcome to my GitHub! I'm Nathan, an independent Fintech Developer with a
Chartered Financial Analyst (CFA) designation, specializing in Python-based
financial analysis, quantitative strategies, and automated trading programs.
Currently, I'm a fintech consultant open to new clients. Schedule a meeting
with me to discuss collaborating on your next project or to learn more about
my services.

📅 `Schedule a Meeting with Me <https://calendly.com/nrcapitalmanagement/github-meeting>`_

Connect with Me
---------------

- **Email**: `nathan.ramos.github@gmail.com <mailto:nathan.ramos.github@gmail.com>`_
- **Twitter**: `@nathanramoscfa <https://twitter.com/nathanramoscfa>`_

Feel free to connect with me for any inquiries or collaboration opportunities.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
