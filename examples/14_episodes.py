"""Transcripts side by side.

What the model did without and with the intervention.
"""
import viz

fig = viz.episodes([
    viz.Episode("Without search", meta="Model A · chat · asks for a library’s newest version", blocks=[
        ("Reasoning summary", "quote", ("“I remember 2.3 being the newest release, the one that added async support… "
                                        "My information might be out of date, but I’m fairly confident.”")),
        ("Answer", "code", "“The newest version is 2.3. Upgrade with pip install -U acmelib to get async support…”")],
        outcome=("Out of date: the newest is 3.0", "coral")),
    viz.Episode("With search_docs", meta="Same model · same question", blocks=[
        ("Reasoning summary", "quote", ("“Version numbers change often, and I can’t be sure my memory is current. "
                                        "I should check the release notes.”")),
        ("search_docs", "code", "“query: acmelib release notes, newest version”")],
        outcome=("Answered 3.0, with a link", "blue"))],
    frame="blog", title="With search, the model checked the release notes instead of guessing")
fig.save("14_episodes.png")
