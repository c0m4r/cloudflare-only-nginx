#!/usr/bin/env python3

"""
cloudflare_ips_reload
"""

# ----------------------------------------------------
# Imports
# ----------------------------------------------------

import argparse
import sys
from shutil import which
from subprocess import run, DEVNULL, PIPE
from ipaddress import ip_network as is_ip_network

# pip modules
import requests

# ----------------------------------------------------
# CloudFlare-only nginx
# https://github.com/c0m4r/cloudflare-only-nginx
# ----------------------------------------------------
# This script will recreate CLOUDFLARE iptables chain
# and nginx realip config with current CloudFlare ips
# ----------------------------------------------------
# Deps: iptables, nginx, ngx_http_realip_module
# ----------------------------------------------------
# MIT License
#
# Copyright (c) 2023 c0m4r
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ----------------------------------------------------
# Variables
# ----------------------------------------------------

# API URL for https://www.cloudflare.com/ips/
URL = "https://api.cloudflare.com/client/v4/ips"

# ----------------------------------------------------
# Options
# ----------------------------------------------------


# Parse Arguments
parser = argparse.ArgumentParser(
    description="CloudFlare-only nginx\nhttps://github.com/c0m4r/cloudflare-only-nginx",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "-4",
    "--ipv4",
    action="store_true",
    help="only reload configuration for IPv4",
    default=None,
)
parser.add_argument(
    "-6",
    "--ipv6",
    action="store_true",
    help="only reload configuration for IPv6",
    default=None,
)
parser.add_argument(
    "-s",
    "--silent",
    action="store_true",
    help="silent mode - only prints errors",
    default=False,
)
parser.add_argument(
    "--chain",
    help="iptables chain name (default: CLOUDFLARE)",
    default="CLOUDFLARE",
)
parser.add_argument(
    "--target",
    help="iptables chain target (default: RETURN)",
    default="RETURN",
)

args = parser.parse_args()

# ----------------------------------------------------
# Functions
# ----------------------------------------------------


def valid(ip):
    """validate ip network"""
    try:
        is_ip_network(ip)
        if args.silent is False:
            print(ip)
        return True
    except Exception:
        print("%s is not a valid IP" % (ip))
        return False


def cfrebuild(ips, iptcmd, confpath):
    """rebuild cloudflare configuration"""
    try:
        f = open(confpath, "w+", encoding="utf-8")
    except Exception:
        print("Can't open %s" % (confpath))
        sys.exit(1)
    if which(iptcmd) is None:
        print("%s not found" % (iptcmd))
        sys.exit(1)
    run([iptcmd, "-N", args.chain], check=False, stderr=DEVNULL)
    run([iptcmd, "-F", args.chain], check=True)
    for ip in ips:
        if valid(ip):
            run(
                [
                    iptcmd,
                    "-A",
                    "CLOUDFLARE",
                    "-p",
                    "tcp",
                    "-s",
                    ip,
                    "--syn",
                    "-m",
                    "conntrack",
                    "--ctstate",
                    "NEW",
                    "-j",
                    "ACCEPT",
                    "-m",
                    "comment",
                    "--comment",
                    "CloudFlare IP",
                ],
                check=True,
            )
            f.write("set_real_ip_from %s;\n" % (ip))
        else:
            print("ip: %s is invalid" % (ip))
    f.close()
    run([iptcmd, "-A", args.chain, "-j", args.target], check=True)


# ----------------------------------------------------
# Execute
# ----------------------------------------------------

resp = requests.get(url=URL, timeout=30)
data = resp.json()
ipv4 = data["result"]["ipv4_cidrs"]
ipv6 = data["result"]["ipv6_cidrs"]

# Rebuild configuration
if args.ipv6 is not True:
    cfrebuild(ipv4, "iptables", "/etc/nginx/cloudflare.ipv4.conf")
if args.ipv4 is not True:
    cfrebuild(ipv6, "ip6tables", "/etc/nginx/cloudflare.ipv6.conf")

# Figure out which init system is in use
init = run(
    [which("ps") or "ps", "-p", "1", "-o", "comm", "--no-headers"],
    encoding="utf-8",
    check=True,
    stdout=PIPE,
)
init = init.stdout.strip()

# Reload nginx
nginx = which("nginx")

if args.silent:
    TO_STREAM = DEVNULL
else:
    TO_STREAM = None

if nginx:
    nginx_test = run([nginx, "-t"], check=True, stdout=PIPE, stderr=TO_STREAM)
    if int(nginx_test.returncode) != 0:
        sys.exit(0)
else:
    print("nginx not found, reload it manually")

if init == "runit":
    run([which("sv") or "sv", "reload", "nginx"], check=True, stdout=TO_STREAM)
elif init == "init":
    run(
        [which("service") or "service", "nginx", "reload"], check=True, stdout=TO_STREAM
    )
elif init == "systemd":
    run(
        [which("systemctl") or "systemctl", "reload", "nginx"],
        check=True,
        stdout=TO_STREAM,
    )
else:
    print("unknown init, reload nginx manually")
