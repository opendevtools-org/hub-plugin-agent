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

Hub finds an installable plugin only from
`install.composeFile` = `plugins/<id>/docker-compose.backend.yml`.
The catalog branch it reads is `main`.

`role` is `backend` when the source has a server, and `frontend` when it
does not.

For a backend, under `plugins/<id>/`:

- `docker-compose.backend.yml` for `ghcr.io/<catalog-owner>/<id>:hub`
- `docker-compose.frontend.yml` for `:hub-web`
- the CLI, the MCP server, the OpenAPI file, and the Dockerfiles
- the page Hub opens at `/p/<id>/`

`:hub-web` exchanges the one-time SSO code, stores the access token, and
opens `ui/`. The app sends that token as `Authorization`. It does not
exchange the code again.

When the backend already serves the UI, nginx proxies `/ui/` and `/api/`
to it. When the backend has no UI and the source has a separate web
frontend, nginx serves that build at `/ui/` and `/assets/` and proxies
only `/api/`.

For a frontend, the only image is `:hub-web`, and it is the service in
`docker-compose.backend.yml`. There is no second compose file. The web
page is created when the source has none.

The Hub shell does not contain plugin code. The agent does not add a
mobile client. Web, desktop, and phone open `/p/<id>/`.

The Docker build context is the plugin directory. When the source
publishes no image, publish clones it into `src/app/` and that directory
stays out of git. The token is only used to read the source. It is not
stored in the plugin.

If the source already publishes an image, `:hub` starts `FROM` that image
and keeps the application's command.

## Server

When the plugin already runs on a machine you control, pass its `http` or
`https` URL. Hub opens that `server` and does not start a container. It
does not attach SSO. The catalog does not say where Hub itself runs.

```bash
python add_plugin.py \
  --source https://github.com/owner/project \
  --server https://plugin.example \
  --catalog owner/your-plugin-catalog \
  --push
```

`add_plugin.py` writes that catalog row and nothing under `plugins/`.
The agent does the same when the message includes a server URL.
