##  CloudFlare-only nginx + IPv6-only

Having IPv6 only server doesn't mean that you cannot serve your website to IPv4 clients. You can use CloudFlare to achieve that. It's enough to set up only AAAA record in the CloudFlare DNS configuration. CloudFlare will communicate with your origin server via IPv6 and send responses to clients connecting from both IPv4 and IPv6 addresses.

### Log real client IPs

With [realip module](https://nginx.org/en/docs/http/ngx_http_realip_module.html) you can log real client IP sent by CloudFlare in [CF-Connecting-IP header](https://developers.cloudflare.com/support/troubleshooting/restoring-visitor-ips/restoring-original-visitor-ips/).

### CloudFlare-only setup

You can also close your web server to cloudflare-only traffic using firewall rules with [CloudFlare IP list](https://www.cloudflare.com/ips/).

### Helper script

```
python3 cloudflare_ips_reload.py
```

This script will recreate ip6tables CLOUDFLARE chain and allow traffic from only CloudFlare IPs, then recreate /etc/nginx/cloudflare.conf with realip configuration and reload nginx.
