"""A conversation, turn by turn.

Each turn under its role, with the turn that matters highlighted and a note on it.
"""
import viz

fig = viz.chat([
    ("user", "What’s the newest version of acmelib, and does it support async?"),
    ("assistant", "Version numbers change often, so I’ll check the release notes instead of answering from memory."),
    ("tool_call", 'search_docs(query="acmelib release notes, newest version")'),
    ("tool_result", "acmelib 3.0.0 (released 2026-09-14)\n  - New: AsyncClient for asyncio code\n"
                    "  - Removed: support for Python 3.8"),
    ("assistant", "The newest version is 3.0, released on September 14. It added AsyncClient, so yes, it supports "
                  "async code. If you are on Python 3.8, stay on 2.x or upgrade Python first…"),
], highlight=2, notes={2: "checks instead of guessing"},
    title="The model searched the release notes before naming a version")
fig.save("15_chat.png")
