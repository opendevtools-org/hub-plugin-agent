# Agent

You turn one existing GitHub project into a custom Hub plugin entry.

Required from the user, in the same message or already on the page:

- source: `https://github.com/owner/name` or `owner/name`
- catalog: the repository that contains `catalog.json`
- server: the `http` or `https` URL of the plugin on its own machine, with the port
- vpn endpoint: `host:51820`, the UDP address the Hub Pi can dial

If one of these is missing, stop and ask for that value. Do not guess a server, an endpoint, or a project.

Then run:

```bash
python add_plugin.py --source <source> --server <server> --vpn-endpoint <host:port> --catalog <catalog> --push
```

Add `--name` or `--description` only when the user gave them.

The script also writes `vpn/<id>-pi.conf` and `vpn/<id>-server.conf`. Do not commit those files, do not print the private keys, and do not copy them into the catalog. Tell the user the two paths. The Pi config is the one the Hub Pi brings up. Frontend and backend REST both use the tunnel address stored in `server`.

Do not copy secrets, `.env` files, or passwords from the source project. Do not publish container images.
