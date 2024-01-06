#!/usr/bin/env python3

# ----------------------------------------------------
# Imports
# ----------------------------------------------------

import requests
import sys
from shutil import which
from subprocess import run, DEVNULL, PIPE
from ipaddress import ip_network as is_ip_network

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
url = "https://api.cloudflare.com/client/v4/ips"

# iptables chain name
iptables_chain = "CLOUDFLARE"

# iptables chain target
iptables_target = "RETURN"

# ----------------------------------------------------
# Options
# ----------------------------------------------------

try:
    option = sys.argv[1]
except Exception:
    option = None

if option not in (None, "-4", "-6", "--ipv4", "--ipv6"):
    print("Usage: %s [option]\nOptions:\n" % sys.argv[0])
    print(" -4, --ipv4\t# Only reload configuration for IPv4")
    print(" -6, --ipv6\t# Only reload configuration for IPv6")
    print("\nhttps://github.com/c0m4r/cloudflare-only-nginx")
    sys.exit(0)

# ----------------------------------------------------
# Functions
# ----------------------------------------------------


def valid(ip):
    try:
        is_ip_network(ip)
        if option not in ("-s", "--silent"):
            print(ip)
        return True
    except Exception:
        print("%s is not a valid IP" % (ip))
        return False


def cfrebuild(ips, iptcmd, confpath):
    try:
        f = open(confpath, "w+")
    except Exception:
        print("Can't open %s" % (confpath))
        sys.exit(1)
    if which(iptcmd) is None:
        print("%s not found" % (iptcmd))
        sys.exit(1)
    run([iptcmd, "-N", iptables_chain], stderr=DEVNULL)
    run([iptcmd, "-F", iptables_chain])
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
                    r"\'CloudFlare IP\'",
                ]
            )
            f.write("set_real_ip_from %s;\n" % (ip))
        else:
            print("ip: %s is invalid" % (ip))
    f.close()
    run([iptcmd, "-A", iptables_chain, "-j", iptables_target])


# ----------------------------------------------------
# Execute
# ----------------------------------------------------

resp = requests.get(url=url, timeout=30)
data = resp.json()
ipv4 = data["result"]["ipv4_cidrs"]
ipv6 = data["result"]["ipv6_cidrs"]

# Rebuild configuration
if option in (None, "-4", "--ipv4"):
    cfrebuild(ipv4, "iptables", "/etc/nginx/cloudflare.ipv4.conf")
if option in (None, "-6", "--ipv6"):
    cfrebuild(ipv6, "ip6tables", "/etc/nginx/cloudflare.ipv6.conf")

# Figure out which init system is in use
init = run(
    [which("ps"), "-p", "1", "-o", "comm", "--no-headers"],
    encoding="utf-8",
    stdout=PIPE,
)
init = init.stdout.strip()

# Reload nginx
nginx = which("nginx")

if nginx:
    nginx_test = run([nginx, "-t"], stdout=PIPE)
    if int(nginx_test.returncode) != 0:
        sys.exit(0)
else:
    print("nginx not found, reload it manually")

if init == "runit":
    run([which("sv"), "reload", "nginx"])
elif init == "init":
    run([which("service"), "nginx", "reload"])
elif init == "systemd":
    run([which("systemctl"), "reload", "nginx"])
else:
    print("unknown init, reload nginx manually")
