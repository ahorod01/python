#!/usr/bin/env python3
"""
List Active Directory computer objects with their OS name, version, and
service pack.

Requires: pip install ldap3

Usage examples:
    python list_ad_computer_os.py --server dc01.corp.example.com \
        --base-dn "DC=corp,DC=example,DC=com" --user "CORP\\svc_reader"

    python list_ad_computer_os.py --server dc01.corp.example.com \
        --base-dn "DC=corp,DC=example,DC=com" --user "CORP\\svc_reader" \
        --ssl --csv computers.csv

If --user is omitted, an anonymous/SASL(negotiate) bind is attempted using
the current OS credentials (Windows only, via ldap3's Kerberos support).
On non-Windows hosts, supply --user and you'll be prompted for a password
(or pass --password, or set the AD_PASSWORD environment variable).
"""

import argparse
import csv
import getpass
import os
import sys

from ldap3 import (
    ALL,
    NTLM,
    SASL,
    SUBTREE,
    Connection,
    Server,
)


def parse_args():
    p = argparse.ArgumentParser(description="List AD computer OS versions.")
    p.add_argument("--server", required=True, help="AD server hostname or IP")
    p.add_argument("--base-dn", required=True, help='e.g. "DC=corp,DC=example,DC=com"')
    p.add_argument("--user", help='e.g. "CORP\\\\svc_reader" or "svc_reader@corp.example.com"')
    p.add_argument("--password", help="Bind password (or set AD_PASSWORD env var)")
    p.add_argument("--ssl", action="store_true", help="Use LDAPS (port 636)")
    p.add_argument("--port", type=int, help="Override port")
    p.add_argument(
        "--search-filter",
        default="(objectCategory=computer)",
        help="LDAP filter for computer objects (default: all computers)",
    )
    p.add_argument("--csv", help="Optional path to write results as CSV")
    p.add_argument(
        "--disabled-only",
        action="store_true",
        help="Only include disabled computer accounts",
    )
    p.add_argument(
        "--enabled-only",
        action="store_true",
        help="Only include enabled computer accounts",
    )
    return p.parse_args()


# UserAccountControl bit flag for disabled accounts
UAC_ACCOUNTDISABLE = 2


def build_filter(base_filter, enabled_only, disabled_only):
    if enabled_only and disabled_only:
        raise SystemExit("Cannot use --enabled-only and --disabled-only together")
    if enabled_only:
        return f"(&{base_filter}(!(userAccountControl:1.2.840.113556.1.4.803:={UAC_ACCOUNTDISABLE})))"
    if disabled_only:
        return f"(&{base_filter}(userAccountControl:1.2.840.113556.1.4.803:={UAC_ACCOUNTDISABLE}))"
    return base_filter


def main():
    args = parse_args()

    port = args.port or (636 if args.ssl else 389)
    server = Server(args.server, port=port, use_ssl=args.ssl, get_info=ALL)

    password = args.password or os.environ.get("AD_PASSWORD")
    if args.user and not password:
        password = getpass.getpass(f"Password for {args.user}: ")

    if args.user:
        conn = Connection(
            server,
            user=args.user,
            password=password,
            authentication=NTLM if "\\" in args.user else None,
            auto_bind=True,
        )
    else:
        # Anonymous / current-credentials (Kerberos) bind
        conn = Connection(server, authentication=SASL, sasl_mechanism="GSSAPI", auto_bind=True)

    search_filter = build_filter(args.search_filter, args.enabled_only, args.disabled_only)

    attributes = [
        "name",
        "dNSHostName",
        "operatingSystem",
        "operatingSystemVersion",
        "operatingSystemServicePack",
        "distinguishedName",
        "userAccountControl",
        "whenChanged",
    ]

    conn.search(
        search_base=args.base_dn,
        search_filter=search_filter,
        search_scope=SUBTREE,
        attributes=attributes,
        paged_size=500,
    )

    rows = []
    for entry in conn.entries:
        uac = int(entry.userAccountControl.value) if entry.userAccountControl else 0
        rows.append(
            {
                "name": str(entry.name) if entry.name else "",
                "dns_hostname": str(entry.dNSHostName) if entry.dNSHostName else "",
                "os_name": str(entry.operatingSystem) if entry.operatingSystem else "(unknown)",
                "os_version": str(entry.operatingSystemVersion) if entry.operatingSystemVersion else "",
                "service_pack": str(entry.operatingSystemServicePack)
                if entry.operatingSystemServicePack
                else "",
                "enabled": "No" if (uac & UAC_ACCOUNTDISABLE) else "Yes",
                "last_changed": str(entry.whenChanged) if entry.whenChanged else "",
                "dn": str(entry.distinguishedName) if entry.distinguishedName else "",
            }
        )

    conn.unbind()

    if not rows:
        print("No computer objects found matching the filter.")
        return

    # Sort by OS name, then hostname
    rows.sort(key=lambda r: (r["os_name"], r["name"]))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {args.csv}")

    # Console summary: counts per OS
    counts = {}
    for r in rows:
        key = f"{r['os_name']} {r['os_version']}".strip()
        counts[key] = counts.get(key, 0) + 1

    print(f"\n{len(rows)} computer object(s) found.\n")
    print(f"{'Hostname':30} {'OS':35} {'Version':20} {'Enabled':7}")
    print("-" * 95)
    for r in rows:
        print(f"{r['name']:30} {r['os_name']:35} {r['os_version']:20} {r['enabled']:7}")

    print("\nSummary by OS:")
    for os_name, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:4}  {os_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
