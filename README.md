##  CloudFlare-only nginx

This repository contains a complete configuration examples for CloudFlare-only nginx.

The goal is to close your web server to cloudflare-only traffic using firewall rules and [CloudFlare IP list](https://www.cloudflare.com/ips/).

You can accept traffic from both IPv4 and IPv6, however even having IPv6 only server doesn't mean that you cannot serve your website to IPv4 clients. You can use CloudFlare to achieve that. It's enough to set up only AAAA record in the CloudFlare DNS configuration. CloudFlare will communicate with your origin server via IPv6 and send responses to clients connecting from both IPv4 and IPv6 addresses.

### Log real client IP

With [realip module](https://nginx.org/en/docs/http/ngx_http_realip_module.html) you can log real client IP sent by CloudFlare in [CF-Connecting-IP header](https://developers.cloudflare.com/support/troubleshooting/restoring-visitor-ips/restoring-original-visitor-ips/).

### Helper script

```
python3 cloudflare_ips_reload.py
```

This script will recreate ip6tables CLOUDFLARE chain and allow traffic from only CloudFlare networks, then recreate realip configuration and reload nginx.

A chain must be present prior to running the script.
