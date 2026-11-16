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

Write `plugins/<id>/` in the catalog: backend compose, frontend compose,
web client, CLI, MCP, OpenAPI, SSO, custom mode (`server` empty unless
the user gave an URL), and the Dockerfiles that build `:hub` and
`:hub-web`. If the source has no mobile language, add a Flutter Android
client. If it already has one, leave it.

A server URL is optional. When the user gives an `http` or `https` URL,
set `server` on the catalog row so Hub opens that address and does not
start containers. Do not name a place where Hub runs.
