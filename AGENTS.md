# Agent

You turn one existing project into a Hub plugin that anyone can install
from their own catalog.

Follow `.cursor/skills/hub-plugin/SKILL.md` and run it to the end.

The user must give, in the same message:

- source: `https://github.com/owner/name` or `owner/name`
- token: a GitHub token that can read that source
- catalog: the plugin repository that contains `catalog.json`

If one of these is missing, stop and ask for that value. Do not guess a
repository, a token, a port, or a health path.

Use the token only to read the source. Do not print it, do not write it
into a file, and do not push it. Do not modify the source repository.
Do not copy secrets from the source.

`id` matches `^[a-z][a-z0-9-]{1,62}$`. Hub rejects anything else.

Record `role` as `backend` or `frontend`.

When the user gives an `http` or `https` URL, write only the `catalog.json`
row with that `server`. Hub opens that address, starts no container, and
does not attach SSO. Do not write `plugins/<id>/`. This is the same row
`add_plugin.py` writes. Do not name a place where Hub runs.

Otherwise Hub finds the plugin only from
`install.composeFile` = `plugins/<id>/docker-compose.backend.yml`. A `path`
field is ignored. That compose file is the service Hub health-checks.
Push `main`: Hub reads the catalog at `ref=main`.

When `role` is `backend`, also write `docker-compose.frontend.yml`, the
CLI, the MCP server, OpenAPI, and Dockerfiles for `:hub` and `:hub-web`.
The Docker build context is the plugin directory, so `COPY src/cli` reads
the plugin. Do not add a mobile client. The Hub shell does not contain
plugin code. Web, desktop, and phone open `/p/<id>/`.

`:hub-web` is the page at `/p/<id>/`. Hub does not put the bearer in
`?sso=`. It sets the cookie `homelab_sso_<id>` to a one-time code, and a
phone WebView may redirect to `?sso_code=`. The gate exchanges that code
at `api/auth/sso/browser-exchange`, stores `access_token` as `hub_sso`,
then opens the relative URL `ui/`. The app sends that value as
`Authorization`. It does not exchange the code again.

If the backend already serves the UI, nginx proxies `/ui/` to it and
`/api/` to it. If the backend has no UI and the source has a separate web
frontend, nginx serves that build at `/ui/` and `/assets/` and proxies
only `/api/`. The frontend keeps API calls on absolute `/api/...`.

When `role` is `frontend`, the only image is `:hub-web`, and it is the
service in `docker-compose.backend.yml`. Do not write a second compose
file, a `:hub` image, a CLI, an MCP server, or OpenAPI. Create the web
page when the source has none. Do not add a mobile client when the source
already has one, and do not add one when it has none.

A port and a health path are required only when Hub starts a container.
The health path is the HTTP path Hub requests, read from the source.
