#!/usr/bin/env python3
"""Add one existing GitHub project to a Hub catalog as a custom plugin."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from wireguard_config import (
    keypair,
    parse_endpoint,
    pi_config,
    server_config,
    tunnel_hosts,
    tunnel_http_url,
)


def github_repo(value: str) -> str:
    text = value.strip()
    if text.startswith("https://github.com/"):
        text = text.removeprefix("https://github.com/").strip("/")
        if text.endswith(".git"):
            text = text[:-4]
    owner, _sep, name = text.partition("/")
    if not owner or not name or "/" in name:
        raise SystemExit("Use owner/name or a https://github.com/owner/name URL.")
    return f"{owner}/{name}"


def plugin_id(repo: str) -> str:
    name = repo.split("/", 1)[1].lower()
    if name.endswith("-v2"):
        name = name[:-3]
    slug = re.sub(r"[^a-z0-9-]+", "-", name).strip("-")
    if not slug:
        raise SystemExit("The repository name cannot become a plugin id.")
    return slug


def server_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("Each plugin needs a server URL that starts with http:// or https://.")
    return value.strip().rstrip("/")


def load_catalog(path: Path) -> dict:
    if not path.is_file():
        return {"updatedAt": "", "plugins": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), list):
        raise SystemExit("catalog.json must be an object with a plugins list.")
    return data


def upsert(catalog: dict, entry: dict) -> None:
    plugins = catalog["plugins"]
    for index, raw in enumerate(plugins):
        if isinstance(raw, dict) and raw.get("id") == entry["id"]:
            plugins[index] = entry
            return
    plugins.append(entry)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Existing GitHub project")
    parser.add_argument(
        "--server",
        required=True,
        help="HTTP URL of the plugin on its own machine, including the port",
    )
    parser.add_argument(
        "--vpn-endpoint",
        required=True,
        help="UDP address the Hub Pi can dial, host:51820",
    )
    parser.add_argument("--catalog", required=True, help="Catalog repository that receives the plugin")
    parser.add_argument("--name", default="", help="Name shown in the catalog")
    parser.add_argument("--description", default="")
    parser.add_argument("--checkout", default="", help="Existing catalog clone. Empty clones a temporary copy.")
    parser.add_argument("--push", action="store_true", help="Commit and push catalog.json")
    args = parser.parse_args()
    source = github_repo(args.source)
    catalog_repo = github_repo(args.catalog)
    server = server_url(args.server)
    endpoint = parse_endpoint(args.vpn_endpoint)
    listen_port = int(endpoint.rsplit(":", 1)[1])
    slug = plugin_id(source)
    pi_ip, plugin_ip = tunnel_hosts(slug)
    pi_private, pi_public = keypair()
    plugin_private, plugin_public = keypair()
    reached = tunnel_http_url(server, plugin_ip)
    entry = {
        "id": slug,
        "name": args.name.strip() or slug,
        "description": args.description.strip() or f"Custom plugin from {source}.",
        "version": "0.1.0",
        "homepage": f"https://github.com/{source}",
        "repo": catalog_repo,
        "ref": "main",
        "visibility": "personal",
        "server": reached,
        "vpn": "wireguard",
        "clients": [{"kind": "web", "launchPath": "/"}],
    }
    cleanup_root: Path | None = None
    if args.checkout:
        checkout = Path(args.checkout)
    else:
        cleanup_root = Path(tempfile.mkdtemp(prefix="hub-plugin-"))
        checkout = cleanup_root
        clone = subprocess.run(["gh", "repo", "clone", catalog_repo, str(checkout)], check=False)
        if clone.returncode != 0:
            raise SystemExit("Could not clone the catalog. Check the name and your GitHub login.")
    catalog_path = checkout / "catalog.json"
    catalog = load_catalog(catalog_path)
    upsert(catalog, entry)
    catalog["updatedAt"] = date.today().isoformat()
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    vpn_dir = checkout / "vpn"
    vpn_dir.mkdir(exist_ok=True)
    ignore = checkout / ".gitignore"
    rules = ignore.read_text(encoding="utf-8") if ignore.is_file() else ""
    if "vpn/*.conf" not in rules:
        ignore.write_text(rules + "vpn/*.conf\n", encoding="utf-8")
    (vpn_dir / f"{slug}-pi.conf").write_text(
        pi_config(
            private_key=pi_private,
            address=pi_ip,
            peer_public=plugin_public,
            peer_ip=plugin_ip,
            endpoint=endpoint,
        ),
        encoding="utf-8",
    )
    (vpn_dir / f"{slug}-server.conf").write_text(
        server_config(
            private_key=plugin_private,
            address=plugin_ip,
            peer_public=pi_public,
            peer_ip=pi_ip,
            port=listen_port,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {slug} -> {reached}")
    print(f"Pi config: {vpn_dir / f'{slug}-pi.conf'}")
    print(f"Server config: {vpn_dir / f'{slug}-server.conf'}")
    if not args.push:
        if cleanup_root is not None:
            print(checkout)
        return
    subprocess.run(["git", "add", "catalog.json", ".gitignore"], cwd=checkout, check=True)
    commit = subprocess.run(
        ["git", "commit", "-m", f"Add custom plugin {slug} pointing at its server."],
        cwd=checkout,
        check=False,
    )
    if commit.returncode != 0:
        raise SystemExit("Nothing to commit, or git commit failed.")
    push = subprocess.run(["git", "push"], cwd=checkout, check=False)
    if push.returncode != 0:
        raise SystemExit("Push failed.")


if __name__ == "__main__":
    main()
