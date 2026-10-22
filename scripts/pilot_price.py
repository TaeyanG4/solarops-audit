"""Arithmetic on explicit hypothetical pilot costs, not a market forecast."""

import argparse
import json

p = argparse.ArgumentParser()
for field, value in (
    ("revenue", 200000),
    ("hours", 4),
    ("hourly-cost", 25000),
    ("hosting", 20000),
    ("other-costs", 0),
):
    p.add_argument("--" + field, type=float, default=value)
a = p.parse_args()
if any(v < 0 for v in vars(a).values()):
    p.error("Inputs must be nonnegative")
cost = a.hours * a.hourly_cost + a.hosting + a.other_costs
print(
    json.dumps(
        {
            "status": "hypothesis_only",
            "currency": "KRW",
            "inputs": vars(a),
            "variable_cost": cost,
            "contribution_margin": a.revenue - cost,
            "tax_and_fixed_costs": "excluded",
        },
        indent=2,
    )
)
