---
name: hub-plugin
description: >-
  Turn one existing project into a Hub plugin in the catalog the user names.
  Use for /hub-plugin, "make this project a Hub plugin", or "add this repo
  to my plugin catalog". Writes the catalog row Hub can install: compose,
  clients, CLI, MCP, OpenAPI, and image Dockerfiles. A server URL registers
  the address and starts no container. The Hub shell is not given a new
  mobile client.
---

# Hub plugin

The user gives a source project, a token that can read it, and a plugin
catalog repository. Do not ask for a form when those three values are
already in the message.

## Inputs

| Input | Required | Value |
|-------|----------|--------|
| `SOURCE` | yes | `https://github.com/<owner>/<repo>` or `owner/repo` |
| `TOKEN` | yes | a GitHub token that can read `SOURCE` |
| `PLUGIN_REPO` | yes | `https://github.com/<owner>/<repo>` or `owner/repo` |

If one is missing, stop and ask for that value only. If `SOURCE` cannot be
read (401, 403, 404), stop. If `PLUGIN_REPO` cannot be read or written, stop.

Use the token only to read `SOURCE`. Do not print it. Do not write it into
a file, a commit, a Dockerfile, a script, or a log. After cloning, set the
git remote back to the URL without the token.

Do not copy `.env` files, passwords, or other secrets from the source.
Do not change the source repository. The token is read-only.

## Id and images

`id` matches `^[a-z][a-z0-9-]{1,62}$`, the same rule Hub enforces.

Start from the source repository name in lower case. Drop a `-v2` suffix.
Replace every other character with `-` and strip `-` from the ends. If the
result starts with a digit, prefix `p-`. Truncate to 63 characters. If it
still does not match, stop. If `plugins/<id>/` already exists, update it.

Images, when this plugin has them:

- `ghcr.io/<owner of PLUGIN_REPO>/<id>:hub`
- `ghcr.io/<owner of PLUGIN_REPO>/<id>:hub-web`

## Server URL

If the user gives an `http` or `https` URL, write only the `catalog.json`
row and stop. Do not write `plugins/<id>/`, compose files, or images.
`add_plugin.py` writes this same row.

```json
{
  "id": "<id>",
  "name": "<id>",
  "description": "Custom plugin from <owner/name>.",
  "version": "0.1.0",
  "homepage": "https://github.com/<owner>/<name>",
  "repo": "<PLUGIN_REPO>",
  "ref": "main",
  "server": "<url without a trailing slash>",
  "clients": [{ "kind": "web", "launchPath": "/" }]
}
```

Hub opens `server` and does not start a container. It does not read a
manifest, so it does not attach SSO. Do not name a place where Hub runs.
No port and no health path are required. No image is published.

## Where Hub reads the plugin

Hub derives the folder only from `install.composeFile`. It does not read a
`path` field. Every plugin that Hub starts uses:

`install.composeFile` = `plugins/<id>/docker-compose.backend.yml`

That file is the service Hub health-checks and publishes. A second file,
`docker-compose.frontend.yml`, is started only beside it, and only for
`role` `backend`. Hub reads `catalog.json` from `ref=main`. Push `main`.
If the catalog has no `main`, stop.

Record `role` on `install.role` and in `homelab-plugin.json`.

- `frontend` when the source has no backend service.
- `backend` when the source has a server.

Read the HTTP port and the health path from the source (compose,
Dockerfile, OpenAPI, or README) only when `role` is `backend`, or when a
custom frontend server exists. If they cannot be read in those cases,
stop. Do not invent them. The manifest `healthcheck` is that HTTP path.
Hub requests it. It is not the string `plugin-cli`.

A custom frontend server is a compose file, a Dockerfile, or an HTTP
server the source already documents for its UI.

The Hub shell does not contain plugin code. Do not create a Flutter,
Kotlin, Swift, or React Native client. Web, desktop, and phone open
`/p/<id>/`. Leave a mobile client that is already in the source where it
is. `clients` lists `web`. Add `desktop` only when the source already has
`downloadUrl` or `launchBundle`.

## Frontend

`role` `frontend` has one image, `:hub-web`, and one compose file,
`docker-compose.backend.yml`. The service is `<id>`, image `:hub-web`,
`pull_policy: always`, and `ports` set so the container side is the port
Hub should publish (`80` when this image is nginx). Do not set
`container_name`. Do not write `docker-compose.frontend.yml`, `:hub`, the
CLI, the MCP server, or OpenAPI.

`homelab-plugin.json` has `id`, `name`, `version` `0.1.0`, `homepage` set
to `SOURCE`, `launchPath` `/`, `role` `frontend`, `healthcheck` `/`,
`compose` (`image` is `:hub-web`, `containerPort`, `file` is
`docker-compose.backend.yml`, `service` is `<id>`), and
`sso` `{ "path": "/api/auth/sso", "token": "bearer" }`. `clients` is the
list above. No `officialImage`.

`server` stays `""`.

When the source has no web frontend, `clients/web/index.html` is the SSO
gate and, after the token is stored, the screen itself. Do not iframe
`/ui/`. There is no upstream.

When the source has a web frontend, `:hub-web` builds it. nginx serves the
gate at `/` and the build at `/ui/` and `/assets/`, as in the separate
frontend layout below. After the token is stored the gate opens iframe
`ui/` (relative).

When a custom frontend server exists, `docker-compose.backend.yml` still
holds `<id>` on `:hub-web`. Add the source's server as another service in
that same file. `UPSTREAM` is `http://<that service>:<port>`. The manifest
service stays `<id>`, `containerPort` is `80`, and `healthcheck` is `/`.
nginx uses the upstream layout below. Do not point `install.composeFile`
at `docker-compose.frontend.yml`: Hub health-checks the backend file's
published port, not the frontend file's.

`README.md` says Hub installs `docker-compose.backend.yml`, that the only
tag is `:hub-web`, and whether the web page was created.

## Backend

Run these in order. Skip a step that is already done.

1. **Read `SOURCE`.** Clone it with the token, or call the GitHub contents
   API. Note the language, compose files, Dockerfiles, port, health path,
   whether the process already serves an HTML UI, and any image the
   project already publishes.
2. **Compose.** `docker-compose.backend.yml`: service `<id>`, image `:hub`,
   `pull_policy: always`, `ports` whose container side is the HTTP port,
   and a healthcheck that runs `plugin-cli health`. No `container_name`.
   `docker-compose.frontend.yml`: service `<id>-web`, image `:hub-web`,
   `pull_policy: always`, `UPSTREAM=http://<id>:<port>`. If a file exists,
   update it to this shape.
3. **Clients.** `homelab-plugin.json` has `id`, `name`, `version` `0.1.0`,
   `homepage` set to `SOURCE`, `launchPath` `/`, `role` `backend`,
   `healthcheck` set to the HTTP path, and `compose` (`image` is `:hub`,
   `containerPort`, `file` is `docker-compose.backend.yml`, `service` is
   `<id>`). Add `officialImage` only when the source already publishes an
   image. `sso` is `{ "path": "/api/auth/sso", "token": "bearer" }`.
   `web.image` is `:hub-web`. `clients` is the list in the section above.
   `clients/web/index.html` is the SSO gate below. After the token is
   stored it opens an iframe at `ui/` (relative, so the address stays
   under `/p/<id>/`).
4. **CLI, MCP, OpenAPI.** `src/cli/plugin_cli.py` and `src/mcp/server.py`
   use the Python standard library. `plugin-cli health` and
   `plugin-cli get <path>` call `PLUGIN_API_BASE`. The health path is
   `PLUGIN_HEALTH_PATH`. The MCP server speaks stdio with
   `Content-Length` framing and exposes tools `health` and `get`.
   `openapi.yaml` has `GET` on the health path and `POST /api/auth/sso`.
   If the source already has an OpenAPI or Swagger file, also include the
   operations that file already declares. Do not invent the rest of the API.
5. **Custom mode.** The `catalog.json` row includes `"server": ""`. Empty
   means Hub installs the compose files and pulls the images. Do not set
   an isolation mode. The SSO path stays `/api/auth/sso`.
6. **Image Dockerfiles.** The build context is always the plugin directory.
   `docker build -f src/Dockerfile .` from `plugins/<id>`. `COPY src/cli`
   reads this plugin, not the source checkout.

   `src/Dockerfile` builds `:hub`. When the source already publishes an
   image, `:hub` is `ARG OFFICIAL_IMAGE` and `FROM ${OFFICIAL_IMAGE}`. Do
   not set `ENTRYPOINT` or `CMD`. Copy the CLI, the MCP server,
   `openapi.yaml`, and `src/sso.json` to `/opt/opendevtools/`. Symlink
   `plugin-cli` and `plugin-mcp`. Set `HUB_SSO=1`,
   `HUB_SSO_PATH=/api/auth/sso`, `PLUGIN_NAME`,
   `PLUGIN_API_BASE=http://127.0.0.1:<port>`, and `PLUGIN_HEALTH_PATH`.
   If that image has no Python, install it in a `RUN`.

   When the source publishes no image, `src/publish.sh` clones `SOURCE`
   into `src/app/` with `gh` before the build. Do not write the token into
   the Dockerfile, the script, or the commit. Add `src/app/` to
   `.gitignore`. The Dockerfile copies `src/app` and uses the base image
   and the `ENTRYPOINT` or `CMD` the source Dockerfile already uses. It
   also copies the CLI, the MCP server, OpenAPI, and `sso.json` as above.

   `src/web/Dockerfile` builds `:hub-web` from this same plugin directory.
   Use the layout below. `entrypoint.sh` replaces `__UPSTREAM__` with
   `$UPSTREAM`. `src/sso.json` has `enabled` true, method `POST`, path
   `/api/auth/sso`, token `bearer`, and scope `plugin`, `space`, `user`.
   `src/publish.sh` and `src/publish.ps1` build and push both tags.
7. **Catalog and README.** Add or update the row in `catalog.json`:
   `id`, `homepage` = `SOURCE`, `repo` = `PLUGIN_REPO`, `ref` `main`,
   `server` `""`, and `install` `{ "kind": "compose", "role": "backend",
   "composeFile": "plugins/<id>/docker-compose.backend.yml" }`.
   `clients` matches the manifest.
   `README.md` says what Hub installs, the two tags, whether `:hub` starts
   from a published image or from `src/app`, which web layout was used,
   how `server` stays empty, and how to run `publish`.

## SSO gate

`clients/web/index.html` is copied to `/usr/share/nginx/html/index.html`.
Hub opens it at `/p/<id>/`.

Hub does not put the bearer token in `?sso=`. On the HTML document (`/`
or `index.html`) it sets the cookie `homelab_sso_<id>` to a one-time code.
A script Hub injects at the start of `<head>` copies `sso_code` from the
query, or that cookie, into `sessionStorage` under
`homelab_sso_pending_<id>`. A phone WebView that loaded the page with
`hub_ticket` is redirected to `?sso_code=`. Other document loads are not
redirected.

The page script is inline at the end of `<body>`, so it runs after Hub's
script:

1. `sso` from the query, or from `#sso=`. Store it in `sessionStorage` as
   `hub_sso`.
2. Otherwise the code from `sso_code` in the query, else the cookie
   `homelab_sso_<id>`, else `homelab_sso_pending_<id>`. `POST`
   `api/auth/sso/browser-exchange` with JSON `{ "code", "app_id": "<id>" }`.
   The URL is relative. Store `access_token` as `hub_sso`. The code works
   once. Do not exchange it again from the app.
3. Otherwise the screen says `Missing the Hub SSO token.`

Set `hub_sso` before showing the app. For a backend, and for a frontend
whose web build is served at `/ui/`, showing the app is an iframe whose
`src` is `ui/`. For a frontend page this agent created because the source
had no web UI, showing the app is the screen itself.

The app document reads `hub_sso` and adds `Authorization: Bearer <token>`
on `fetch` and `XMLHttpRequest`, unless that header is already set. The
iframe is same-origin with the gate, so it sees `sessionStorage`. Put this
script in the built `index.html`. When `/ui/` is proxied, inject the same
script into proxied HTML before `</head>`.

SSO is also the contract in `sso.json`, the environment, and OpenAPI.
Do not implement a JWT check.

## Web image

Two layouts. Pick from the source.

**The backend, or the custom frontend server, already serves the UI.**
nginx in `:hub-web`:

- `/api/` uses `proxy_pass __UPSTREAM__;` and keeps the `/api` prefix.
  Forward `Authorization` and `Host`.
- `/ui/` uses `proxy_pass __UPSTREAM__/;` so `/ui/…` is the upstream `/…`.
  Forward `Authorization` and `Host`. Set `Accept-Encoding` to empty and
  insert the token script before `</head>` (`sub_filter`, once).
- `/` is the SSO gate (`try_files` to `/index.html`).

**The backend has no UI and the source has a separate web frontend.**
Build that frontend with the tool the source already uses. Do not change
the source repository. The production base is `/`, so the built HTML
refers to absolute `/assets/...` and the built script calls absolute
`/api/...`. Do not set a relative base. Hub inserts
`<base href="/p/<id>/">` and rewrites absolute `/assets` and `/api` onto
that prefix. A relative `./assets` is requested at `/assets/`, never at
`/ui/assets/`. If the source calls the API with a relative URL, rewrite
those calls to absolute `/api/...` inside the image build only.

Copy the build's `index.html` to `/usr/share/nginx/html/ui/index.html`
and its asset directory to `/usr/share/nginx/html/assets`. The token
script is in that `index.html`.

`default.conf.template`:

- `/api/` uses `proxy_pass __UPSTREAM__;` and keeps the `/api` prefix.
- `/assets/` is the built asset directory, from
  `/usr/share/nginx/html/assets`.
- `/ui/` is the built app, from `/usr/share/nginx/html/ui/index.html`,
  with `try_files` back to that index for client routes.
- `/` is the SSO gate.

Do not proxy `/ui/` to the backend. The backend has no UI.

`FROM nginx:1.27-alpine` unless the source already publishes a frontend
image. A published frontend image can be an earlier build stage. The
final stage is still this nginx layout, including the gate. Copy
`clients/web/index.html` to `/usr/share/nginx/html/index.html`.

## Git and publish

Commit on the catalog repository with the user's git identity. The branch
is `main`. Message: `feat(<id>): add the Hub plugin`, or
`feat(<id>): update the Hub plugin` when the folder already existed.
Push `main`.

When the plugin has image Dockerfiles and `docker info` works, run
`src/publish.sh`. A frontend plugin publishes `:hub-web` only. If Docker
is off, stop and give the user that command. Do not change the visibility
of the registry package. A server-URL row has no publish step.

## Done

Tell the user: `SOURCE`, `PLUGIN_REPO`, `id`, `role`, the image tags that
exist, whether `docker-compose.backend.yml` was created, whether a
separate web layout or an upstream `/ui/` proxy was used, whether the web
page was created, whether `server` is empty or a URL, the commit URL, and
whether the image push worked. Do not include the token.
