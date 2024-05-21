Usage
=====

Here are some basic examples of how to use PyEconomics for calculating and visualizing monetary policy rules.

Example 1: Calculate Current Policy Rule Estimates
--------------------------------------------------

.. code-block:: python

   # Import pyeconomics modules
   from pyeconomics.models.monetary_policy import calculate_policy_rule_estimates

   # Calculate policy rule estimates
   policy_estimates = calculate_policy_rule_estimates(verbose=True)

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
