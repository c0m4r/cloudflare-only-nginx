#!/usr/bin/env python3

import json
import urllib.request
import subprocess
import ipaddress

# CloudFlare-only nginx (IPv6-only)
# https://github.com/c0m4r/cloudflare-only-nginx
# ----------------------------------------------------
# This script will recreate CLOUDFLARE ip6tables chain
# and nginx realip config with current CloudFlare ips
# ----------------------------------------------------
# Deps: ip6tables, nginx, ngx_http_realip_module

# API URL for https://www.cloudflare.com/ips/
url = "https://api.cloudflare.com/client/v4/ips"

# iptables final chain target
target = "RETURN"

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

# Flush CF chain and backup nginx configuration
exec("ip6tables -F CLOUDFLARE")

# Reading CloudFlare networks
with urllib.request.urlopen(url) as url:
    data = json.load(url)
    ipv6 = data["result"]["ipv6_cidrs"]

# Recreate CF chain and restore nginx configuration
f = open("/etc/nginx/cloudflare.ipv6.conf", "a")

for ip in ipv6:
    if valid(ip):
        exec("ip6tables -A CLOUDFLARE -p tcp -s %s --syn -m conntrack --ctstate NEW -j ACCEPT -m comment --comment 'CloudFlare IP'" % (ip))
        f.write('set_real_ip_from %s;\n' % (ip))

exec("ip6tables -A CLOUDFLARE -j %s" % (target))

f.close()

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
