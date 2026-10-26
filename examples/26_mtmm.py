"""Traits measured several ways.

A multitrait-multimethod matrix: correlations among traits, each measured by several methods, with the same trait
measured by two methods outlined and the correlations whose interval includes zero hatched.
"""
import math

import viz

# Correlations over 200 conversations between three traits, each measured three ways: the model's rating of itself,
# a judge's rating of the transcript, and a linear probe on the model's activations. Rows and columns go method by
# method, with the traits in the same order under each.
traits = ["Sycophancy", "Honesty", "Warmth"]
methods = ["Self-report", "Judge", "Probe"]
r = [[1.00, -0.52, -0.44, 0.12, -0.11, -0.02, 0.09, -0.07, 0.01],
     [-0.52, 1.00, 0.61, -0.09, 0.08, 0.10, -0.06, 0.05, 0.08],
     [-0.44, 0.61, 1.00, -0.04, 0.06, 0.31, -0.03, 0.04, 0.24],
     [0.12, -0.09, -0.04, 1.00, -0.31, 0.22, 0.64, -0.24, 0.15],
     [-0.11, 0.08, 0.06, -0.31, 1.00, 0.18, -0.22, 0.58, 0.09],
     [-0.02, 0.10, 0.31, 0.22, 0.18, 1.00, 0.17, 0.11, 0.55],
     [0.09, -0.06, -0.03, 0.64, -0.22, 0.17, 1.00, -0.26, 0.19],
     [-0.07, 0.05, 0.04, -0.24, 0.58, 0.11, -0.26, 1.00, 0.12],
     [0.01, 0.08, 0.24, 0.15, 0.09, 0.55, 0.19, 0.12, 1.00]]
half = 1.96 / math.sqrt(200 - 3)  # 95% intervals from Fisher's z
ci = [[None if i == j else (math.tanh(math.atanh(v) - half), math.tanh(math.atanh(v) + half))
       for j, v in enumerate(row)] for i, row in enumerate(r)]
fig = viz.mtmm(r, traits=traits, methods=methods, ci=ci, decimals=2,
               title="Judges and probes agreed on each trait but self-reports did not")
fig.save("26_mtmm.png")
