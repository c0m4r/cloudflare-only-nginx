#  CloudFlare-only nginx

[![Python](https://img.shields.io/badge/made%20with-python-blue?logo=python&logoColor=ffffff)](https://www.python.org/)
[![Python](https://img.shields.io/badge/pypi-neatplan-blue?logo=pypi&logoColor=ffffff)](https://pypi.org/project/cloudflare-only-nginx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test](https://github.com/c0m4r/cloudflare-only-nginx/workflows/lint_python/badge.svg)](https://github.com/c0m4r/cloudflare-only-nginx/actions)
[![CodeFactor](https://www.codefactor.io/repository/github/c0m4r/cloudflare-only-nginx/badge)](https://www.codefactor.io/repository/github/c0m4r/cloudflare-only-nginx)

This repository contains a complete configuration examples for CloudFlare-only nginx.

The goal is to close your web server to cloudflare-only traffic using firewall rules and [CloudFlare IP list](https://www.cloudflare.com/ips/).

You can accept traffic from both IPv4 and IPv6, however even having IPv6 only server doesn't mean that you cannot serve your website to IPv4 clients. You can use CloudFlare to achieve that. It's enough to set up only AAAA record in the CloudFlare DNS configuration. CloudFlare will communicate with your origin server via IPv6 and send responses to clients connecting from both IPv4 and IPv6 addresses.

Use [Origin CA Certificates](https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/) for strict end-to-end encryption.

Keep in mind that CloudFlare will only use tcp/443 port (HTTPS). We don't need to expose 80/tcp.

## Log real client IP

With [realip module](https://nginx.org/en/docs/http/ngx_http_realip_module.html) you can log real client IP sent by CloudFlare in [CF-Connecting-IP header](https://developers.cloudflare.com/support/troubleshooting/restoring-visitor-ips/restoring-original-visitor-ips/).

Edit nginx.conf and add these settings inside `http` section:

## nginx configuration

```
# realip
include cloudflare.ipv4.conf;
include cloudflare.ipv6.conf;
real_ip_header CF-Connecting-IP;
```

## iptables

Before you use the script, make sure that incoming tcp/443 traffic is pointing to CLOUDFLARE chain.

```
-N CLOUDFLARE
-A INPUT -p tcp -m tcp --dport 443 -j CLOUDFLARE
```

If your INPUT default policy is ACCEPT, make sure to run cloudflare_ips_reload.py with `--target DROP`

## Helper script

```
usage: cloudflare_ips_reload.py [-h] [-4] [-6] [-s] [--chain CHAIN] [--target TARGET]

CloudFlare-only nginx
https://github.com/c0m4r/cloudflare-only-nginx

options:
  -h, --help       show this help message and exit
  -4, --ipv4       only reload configuration for IPv4
  -6, --ipv6       only reload configuration for IPv6
  -s, --silent     silent mode - only prints errors
  --chain CHAIN    iptables chain name (default: CLOUDFLARE)
  --target TARGET  iptables chain target (default: RETURN)
```

This script will recreate iptables CLOUDFLARE chain and allow traffic from only CloudFlare networks, then recreate realip configuration and reload nginx.

By default, with no options passed, it will recreate rules for both IPv4 and IPv6.

### PyPI installation

```
pip install cloudflare-only-nginx
cloudflare-only-nginx --help
```

## License

> MIT License
> 
> Copyright (c) 2023 c0m4r
> 
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
> 
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
> 
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

## Funding

If you found this software helpful, please consider [making donation](https://en.wosp.org.pl/fundacja/jak-wspierac-wosp/wesprzyj-online) to a charity on my behalf. Thank you.
