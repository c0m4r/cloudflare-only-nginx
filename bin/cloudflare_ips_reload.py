#!/usr/bin/env python3

# ----------------------------------------------------
# CloudFlare-only nginx
# https://github.com/c0m4r/cloudflare-only-nginx
# ----------------------------------------------------
# This script will recreate CLOUDFLARE ip6tables chain
# and nginx realip config with current CloudFlare ips
# ----------------------------------------------------
# Deps: iptables, nginx, ngx_http_realip_module
# ----------------------------------------------------

# ----------------------------------------------------
# Variables
# ----------------------------------------------------

# API URL for https://www.cloudflare.com/ips/
url = "https://api.cloudflare.com/client/v4/ips"

# iptables final chain target
target = "RETURN"

# ----------------------------------------------------
# Imports
# ----------------------------------------------------

import sys
import json
import urllib.request
import subprocess
import ipaddress

# ----------------------------------------------------
# Options
# ----------------------------------------------------

try:
    option = sys.argv[1]
except:
    option = None

if option not in (None, "-4", "-6", "--ipv4", "--ipv6"):
    print("Usage: %s [option]\nOptions:\n" % sys.argv[0]);
    print(" -4, --ipv4\t# Only reload IPv4")
    print(" -6, --ipv6\t# Only reload IPv6")
    print("\nhttps://github.com/c0m4r/cloudflare-only-nginx")
    exit(1)

# ----------------------------------------------------
# Functions
# ----------------------------------------------------

def exec(cmd):
    subprocess.call(cmd, shell=True)

def valid(ip):
    try:
        ipaddress.ip_network(ip)
        print(ip)
        return True
    except:
        print('%s is not a valid IP' % (ip))
        return False

def cfrebuild(ips, iptcmd, confpath):
    # Flush CF chain
    exec("%s -N CLOUDFLARE 2>/dev/null" % (iptcmd))
    exec("%s -F CLOUDFLARE" % (iptcmd))
    # Recreate CF chain and restore nginx configuration
    f = open(confpath, "a")
    for ip in ips:
        if valid(ip):
            exec("%s -A CLOUDFLARE -p tcp -s %s --syn -m conntrack --ctstate NEW -j ACCEPT -m comment --comment 'CloudFlare IP'" % (iptcmd, ip))
            f.write('set_real_ip_from %s;\n' % (ip))
        else:
            print("ip: %s is invalid" % (ip))
    f.close()
    exec("%s -A CLOUDFLARE -j %s" % (iptcmd, target))

# ----------------------------------------------------
# Execute
# ----------------------------------------------------

# Reading CloudFlare networks
with urllib.request.urlopen(url) as url:
    data = json.load(url)
    ipv4 = data["result"]["ipv4_cidrs"]
    ipv6 = data["result"]["ipv6_cidrs"]

# Rebuild configuration
if option in (None, "-4", "--ipv4"):
    cfrebuild(ipv4, "iptables", "/etc/nginx/cloudflare.ipv4.conf")
if option in (None, "-6", "--ipv6"):
    cfrebuild(ipv6, "ip6tables", "/etc/nginx/cloudflare.ipv6.conf")

# Figure out which init system is in use
init = subprocess.check_output("ps -p 1 -o comm --no-headers", shell=True) .strip().decode('ascii')

# Reload nginx
if init == 'runit':
    exec("sv reload nginx")
elif init == 'init':
    exec("service nginx reload")
elif init == 'systemd':
    exec("systemctl reload nginx")
else:
    print('unknown init, reload nginx manually')
