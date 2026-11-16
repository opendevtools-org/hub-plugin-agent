# Hub plugin agent

Download this repository. It is the agent that turns a project you already
have into a Hub plugin, in a catalog you choose.

Anyone can use it. The plugin stays in your catalog.

## Download

```bash
git clone https://github.com/opendevtools-org/hub-plugin-agent.git
```

Open that folder in Cursor and tell the agent:

- the source repository (`owner/name` or its GitHub URL)
- a GitHub token that can read the source
- the catalog repository that should contain the plugin

The instructions the agent follows are in `AGENTS.md` and in
`.cursor/skills/hub-plugin/SKILL.md`.

To use the same agent inside another project, copy
`.cursor/skills/hub-plugin` to that project's `.cursor/skills/hub-plugin`.

## What the agent writes

In the catalog, under `plugins/<id>/`:

- `docker-compose.backend.yml` and `docker-compose.frontend.yml`
- a Flutter Android client, when the source has no mobile language
- the web page Hub opens, the CLI, the MCP server, and the OpenAPI file
- SSO for Hub
- custom mode: `server` stays empty, so Hub installs the images; if you
  pass an `http` or `https` URL, Hub opens that address and starts no
  container
- Dockerfiles that build `ghcr.io/<catalog-owner>/<id>:hub` and `:hub-web`

If the source already publishes an image, `:hub` starts `FROM` that image
and keeps the application's command. The token is only used to read the
source. It is not stored in the plugin.

## Remote server and VPN

When the plugin already runs on your machine and you only need the catalog
row plus a WireGuard config for the Hub machine:

```bash
python add_plugin.py \
  --source https://github.com/owner/project \
  --server http://127.0.0.1:8080 \
  --vpn-endpoint plugin-host:51820 \
  --catalog owner/your-plugin-catalog \
  --push
```

The script writes `vpn/<id>-pi.conf` and `vpn/<id>-server.conf`. Those
files hold private keys and are not committed. `server` in the catalog is
the address on the tunnel. Frontend and backend REST both use that
address. On the Hub machine, save the first config as
`/etc/wireguard/wg-<id>.conf` and bring it up with `wg-quick`. On the
plugin machine, do the same with the server config. The plugin process
must listen on all interfaces, not only on localhost.
