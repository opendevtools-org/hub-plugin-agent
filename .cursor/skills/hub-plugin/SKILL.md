---
name: hub-plugin
description: >-
  Turn one existing project into a Hub plugin in the catalog the user names.
  Use for /hub-plugin, "make this project a Hub plugin", or "add this repo
  to my plugin catalog". Creates missing compose files, a Flutter mobile
  client when the project has no mobile language, and the Hub plugin
  pieces: clients, CLI, MCP, OpenAPI, custom mode, and image Dockerfiles.
---

# Hub plugin

The user gives a source project, a token that can read it, and a plugin
catalog repository. You write `plugins/<id>/` in that catalog. Do not ask
for a form when those three values are already in the message.

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

`id` is the source repository name in lower case, without a `-v2` suffix,
using only `[a-z0-9-]`. If `plugins/<id>/` already exists, update it.

Images:

- `ghcr.io/<owner of PLUGIN_REPO>/<id>:hub`
- `ghcr.io/<owner of PLUGIN_REPO>/<id>:hub-web`

Read the HTTP port and the health path from the source (compose,
Dockerfile, OpenAPI, or README). If they cannot be read, stop. Do not
invent them.

## Steps

Run these in order. Skip a step that is already done.

1. **Read `SOURCE`.** Clone it with the token, or call the GitHub contents
   API. Note the language, compose files, Dockerfiles, port, health path,
   and any image the project already publishes.
2. **Compose.** In the plugin folder, create `docker-compose.backend.yml`
   and `docker-compose.frontend.yml` when they are missing. The backend
   service is `<id>`, image `:hub`, `pull_policy: always`, the container
   port, and a healthcheck that runs `plugin-cli health`. The frontend
   service is `<id>-web`, image `:hub-web`, with
   `UPSTREAM=http://<id>:<port>`. If the files exist, update them to this
   shape.
3. **Mobile.** If the source already has a mobile client (Flutter, Kotlin,
   Java for Android, Swift, or React Native), do not write another one.
   If it has none of those, create `clients/android/` as a Flutter app for
   Android. One screen opens the plugin page. Without `sso` in the query
   or the hash, the screen says `Missing the Hub SSO token.` With the
   token, the app keeps it in memory and opens the page.
4. **Clients.** `homelab-plugin.json` has `id`, `name`, `version` `0.1.0`,
   `homepage` set to `SOURCE`, `launchPath` `/`, `healthcheck`, and
   `compose` (`image` is `:hub`, `containerPort`, `file` is
   `docker-compose.backend.yml`, `service` is `<id>`). Add
   `officialImage` only when the source already publishes an image.
   `clients` lists web, android, and desktop, each with `launchPath` `/`.
   `sso` is `{ "path": "/api/auth/sso", "token": "bearer" }`. `web.image`
   is `:hub-web`. `clients/web/index.html` is the page Hub opens: without
   `?sso=` or `#sso=` it says `Missing the Hub SSO token.`; with the token
   it stores it in `sessionStorage` under `hub_sso` and opens an iframe at
   `/ui/`.
5. **CLI, MCP, OpenAPI.** `src/cli/plugin_cli.py` and `src/mcp/server.py`
   use the Python standard library. `plugin-cli health` and
   `plugin-cli get <path>` call `PLUGIN_API_BASE`. The health path is
   `PLUGIN_HEALTH_PATH`. The MCP server speaks stdio with
   `Content-Length` framing and exposes tools `health` and `get`.
   `openapi.yaml` has `GET` on the health path and `POST /api/auth/sso`.
   If the source already has an OpenAPI or Swagger file, also include the
   operations that file already declares. Do not invent the rest of the API.
6. **Custom mode.** The `catalog.json` row includes `"server": ""`. Empty
   means Hub installs the compose files and pulls the images. If the user
   gave an `http` or `https` URL, put that URL in `server`: Hub does not
   start containers and opens that address instead. Do not set an
   isolation mode. The SSO path stays `/api/auth/sso`.
7. **Image Dockerfiles.** `src/Dockerfile` builds `:hub`.
   `src/web/Dockerfile` builds `:hub-web`. When the source already
   publishes an image, `:hub` is `ARG OFFICIAL_IMAGE` and
   `FROM ${OFFICIAL_IMAGE}`. Do not set `ENTRYPOINT` or `CMD`. Copy the
   CLI, the MCP server, `openapi.yaml`, and `src/sso.json` to
   `/opt/opendevtools/`. Symlink `plugin-cli` and `plugin-mcp`. Set
   `HUB_SSO=1`, `HUB_SSO_PATH=/api/auth/sso`, `PLUGIN_NAME`,
   `PLUGIN_API_BASE=http://127.0.0.1:<port>`, and `PLUGIN_HEALTH_PATH`.
   If that image has no Python, install it in a `RUN`. For `:hub-web`,
   `FROM` the published frontend image when one exists. Otherwise use
   `nginx:1.27-alpine`, a `default.conf.template` (`/api/` forwards the
   URI unchanged to `__UPSTREAM__`, `/ui/` uses
   `proxy_pass __UPSTREAM__/`, and every other path is the static page),
   and an `entrypoint.sh` that replaces `__UPSTREAM__` with `$UPSTREAM`.
   When the source publishes no image, both Dockerfiles build the local
   checkout of `SOURCE`. The build context is that checkout and the
   `-f` path points at the Dockerfile in the plugin. The token never
   appears in a Dockerfile. `src/sso.json` has `enabled` true, method
   `POST`, path `/api/auth/sso`, token `bearer`, and scope `plugin`,
   `space`, `user`. `src/publish.sh` and `src/publish.ps1` build and push
   both tags.
8. **Catalog and README.** Add or update the row in `catalog.json`:
   `id`, `homepage` = `SOURCE`, `repo` = `PLUGIN_REPO`, `ref` `main`,
   `server` empty or the URL the user gave, and
   `install.composeFile` = `plugins/<id>/docker-compose.backend.yml`.
   `README.md` in the plugin folder says what Hub installs, the two tags,
   whether the Dockerfiles start from a published image or build the
   source, whether a Flutter client was added, how custom mode works,
   and how to run `publish`.

SSO is the contract in `sso.json`, the environment, and OpenAPI. Do not
implement a JWT check.

## Git and publish

Commit on the catalog repository with the user's git identity. Message:
`feat(<id>): add the Hub plugin`, or `feat(<id>): update the Hub plugin`
when the folder already existed. Push the default branch.

If `docker info` works, run `src/publish.sh`. If Docker is off, stop and
give the user that command. Do not change the visibility of the registry
package.

## Done

Tell the user: `SOURCE`, `PLUGIN_REPO`, `id`, both image tags, whether
the compose files were created, whether the Flutter client was created,
whether `server` is empty or a URL, the commit URL, and whether the
image push worked. Do not include the token.
