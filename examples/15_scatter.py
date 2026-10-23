"""One dot per dataset.

Two measures against each other, with a reference line and labels on the points that matter.
"""
import viz

# Per dataset: the share of questions that need recent facts, and searches per 100 questions.
searches = {
    "History Quiz": (3, 6), "Recipe Box": (5, 4), "Kids Questions": (6, 9), "Science Facts": (8, 14),
    "Law Basics": (12, 22), "Health FAQ": (14, 31), "Trivia Night": (17, 20), "City Guides": (21, 26),
    "Movie Buff": (24, 33), "Travel Tips": (27, 41), "Product Help": (31, 52), "Music Charts": (35, 29),
    "Sports Desk": (42, 37), "Election Facts": (46, 71), "Finance Q&A": (53, 64), "Tech News": (61, 78),
}
fig = viz.scatter(
    searches, xunit="%", xticks=[0, 10, 20, 30, 40, 50, 60, 70], yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80],
    labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk", "Recipe Box"],
    diagonal="one search per question that needs one",
    annotations=[(2, 76, "Above the line: more searches than\nquestions that needed them")],
    xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
    title="Datasets with more questions about recent events drew more searches")
fig.save("15_scatter.png")
