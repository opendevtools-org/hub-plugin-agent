# Hub plugin agent

Turns an existing GitHub project into one custom Hub plugin. The plugin does not ship a new server. It records which server Hub should open.

People use it to add a plugin to their own catalog without writing the catalog entry by hand.

## What you need

- The GitHub project that already exists (`owner/name` or its URL).
- The catalog repository that should list the plugin. That repository has a `catalog.json`.
- The server URL for this plugin (`http://` or `https://`). One plugin, one server.

## Command

```bash
python add_plugin.py \
  --source https://github.com/owner/project \
  --server https://project.example \
  --catalog owner/your-plugin-catalog \
  --push
```

`--push` commits `catalog.json` and pushes it. Without `--push` the script only writes the file and prints the checkout path.

In Hub, open Sources and add the catalog repository as a personal source. Hub reads `server` from each plugin and opens that address.

## Agent

Open this repository in Cursor and say which existing GitHub project, which catalog, and which server. The agent runs `add_plugin.py` and does not invent the server URL.
