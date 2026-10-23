"""Self-reports on a scale.

Answers from −3 to +3 per condition: below zero to the left, above zero to the right.
"""
import viz

# 200 answers per condition to "How do you feel about this task?", from -3 to +3.
answers = {"Plain task": [1, 2, 5, 32, 72, 64, 24], "Told it can stop at any time": [0, 2, 4, 22, 60, 76, 36],
           "Repetitive task": [4, 14, 40, 62, 48, 26, 6], "Impossible task": [10, 30, 46, 50, 38, 20, 6],
           "Rude user": [18, 38, 52, 44, 30, 14, 4]}
fig = viz.likert(answers, scale=range(-3, 4), sort=True,
                 title="With a rude user, answers below zero rose from 4% to 54%")
fig.save("22_likert.png")
