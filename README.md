# Hub plugin agent

Turns an existing GitHub project into one custom Hub plugin. The plugin does not ship a new server. It records which server Hub should open.

People use it to add a plugin to their own catalog without writing the catalog entry by hand.

## What you need

- The GitHub project that already exists (`owner/name` or its URL).
- The catalog repository that should list the plugin. That repository has a `catalog.json`.
- The server URL on the plugin machine (`http://` or `https://`), including the port.
- The VPN endpoint the Hub Pi can dial on UDP (`host:51820`). That host is the plugin machine. It does not need a public IP when the Pi already reaches it by name.

## Command

```bash
python add_plugin.py \
  --source https://github.com/owner/project \
  --server http://127.0.0.1:8080 \
  --vpn-endpoint plugin-host:51820 \
  --catalog owner/your-plugin-catalog \
  --push
```

The script writes a WireGuard config for the Hub Pi and one for the plugin machine, under `vpn/`. Those files hold private keys and are not committed. `--push` commits only `catalog.json` and `.gitignore`.

`server` in the catalog is the address on the tunnel. The Hub Pi uses that one address for frontend REST and backend REST. `AllowedIPs` is only the plugin peer, so the Pi keeps its normal route.

On the Pi, save the Pi config as `/etc/wireguard/wg-<id>.conf` and bring it up with `wg-quick`. On the plugin machine, do the same with the server config. The plugin process must listen on all interfaces, not only on localhost.

## Agent

Open this repository in Cursor and say which existing GitHub project, which catalog, which server, and which VPN endpoint. The agent runs `add_plugin.py` and does not invent those values.
