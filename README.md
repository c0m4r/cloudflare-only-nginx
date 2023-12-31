##  CloudFlare-only nginx

This repository contains a complete configuration examples for CloudFlare-only nginx.

The goal is to close your web server to cloudflare-only traffic using firewall rules and [CloudFlare IP list](https://www.cloudflare.com/ips/).

You can accept traffic from both IPv4 and IPv6, however even having IPv6 only server doesn't mean that you cannot serve your website to IPv4 clients. You can use CloudFlare to achieve that. It's enough to set up only AAAA record in the CloudFlare DNS configuration. CloudFlare will communicate with your origin server via IPv6 and send responses to clients connecting from both IPv4 and IPv6 addresses.

Use [Origin CA Certificates](https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/) for strict end-to-end encryption.

Keep in mind that CloudFlare will only use tcp/443 port (HTTPS). We don't need to expose 80/tcp.

### Log real client IP

With [realip module](https://nginx.org/en/docs/http/ngx_http_realip_module.html) you can log real client IP sent by CloudFlare in [CF-Connecting-IP header](https://developers.cloudflare.com/support/troubleshooting/restoring-visitor-ips/restoring-original-visitor-ips/).

Edit nginx.conf and add these settings inside `http` section:

### nginx configuration

```
# realip
include cloudflare.ipv4.conf;
include cloudflare.ipv6.conf;
real_ip_header CF-Connecting-IP;
```

### iptables

Before you use the script, make sure that incoming tcp/443 traffic is pointing to CLOUDFLARE chain.

If your INPUT default policy is DROP, just add:

```
-N CLOUDFLARE
-A INPUT -p tcp -m tcp --dport 443 -j CLOUDFLARE
```

If your INPUT default policy is ACCEPT, make sure to add a DROP rule afterwards:

```
-N CLOUDFLARE
-A INPUT -p tcp -m tcp --dport 443 -j CLOUDFLARE
-A INPUT -p tcp -m tcp --dport 443 -j DROP
```

or edit cloudflare_ips_reload.py and change `iptables_target = "RETURN"` to `iptables_target = "DROP"`

### Helper script

```
Usage: ./cloudflare_ips_reload.py [option]
Options:

 -4, --ipv4	# Only reload IPv4
 -6, --ipv6	# Only reload IPv6
```

This script will recreate iptables CLOUDFLARE chain and allow traffic from only CloudFlare networks, then recreate realip configuration and reload nginx.

With no options it will recreate rules for both IPv4 and IPv6.
