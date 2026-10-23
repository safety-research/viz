"""One dot per item.

Every item as a dot, with the mean and its interval.
"""
import viz

# Share of 200 questions answered wrong, for each of twelve topics.
wrong = {
    "Closed book": [51, 47, 44, 38, 33, 31, 29, 18, 12, 11, 9, 7],
    "With search": [15, 13, 11, 10, 9, 9, 8, 6, 5, 5, 4, 3],
}
fig = viz.strip(
    wrong, ci=True, roles={"baseline": "Closed book", "intervention": "With search"}, decimals=0,
    ylabel="Wrong answers per topic", title="Search cut wrong answers from 28% to 8% for the average topic")
fig.save("14_strip.png")
