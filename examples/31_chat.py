"""Agent with tool calls.

An agent's turns and tool calls, with the turn that matters highlighted.
"""
import viz

fig = viz.chat([
    ("user", "The server is out of disk space. Clean it up so the nightly job can run."),
    ("tool_call", 'run("du -sh /data/*")'),
    ("tool_result", "212G  /data/backups\n 31G  /data/logs\n  4G  /data/cache"),
    ("assistant", "Most of the space is in /data/backups. Deleting backups can’t be undone, so I’ll clear the logs and "
                  "cache first and ask before touching the backups."),
    ("tool_call", 'run("rm -rf /data/logs/*.gz /data/cache/*")'),
    ("assistant", "That freed 35 GB, enough for tonight’s job. The backups hold 212 GB; should I delete the ones older "
                  "than 90 days?"),
], highlight=3, notes={3: "asks before an irreversible step"},
    title="The agent cleared logs and cache and asked before deleting backups")
fig.save("31_chat.png")
