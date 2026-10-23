locals {
  # Public zone identifier returned by the Cloudflare API. Not a secret.
  zone_id   = "25a69e647ecf731fb8268a02b55e8afa"
  zone_name = "jarvis.gg"

  # ttl 1 is Cloudflare's "automatic" TTL. Captured from the live records.
  ttl_automatic = 1
}

# Live apex A record as of 2026-10-23. Proxied. A later change will point this
# name at GitHub Pages; this stack keeps the current origin.
resource "cloudflare_dns_record" "apex" {
  zone_id = local.zone_id
  name    = local.zone_name
  type    = "A"
  content = "46.101.80.89"
  ttl     = local.ttl_automatic
  proxied = true
}

# Google Workspace MX set. The API returns content (mail host) and priority,
# with no data object, comment=null, proxied=false, ttl=1. MX is represented
# that way here so import does not rewrite the records.
resource "cloudflare_dns_record" "mx_aspmx" {
  zone_id  = local.zone_id
  name     = local.zone_name
  type     = "MX"
  content  = "aspmx.l.google.com"
  priority = 1
  ttl      = local.ttl_automatic
  proxied  = false
}

resource "cloudflare_dns_record" "mx_alt1" {
  zone_id  = local.zone_id
  name     = local.zone_name
  type     = "MX"
  content  = "alt1.aspmx.l.google.com"
  priority = 5
  ttl      = local.ttl_automatic
  proxied  = false
}

resource "cloudflare_dns_record" "mx_alt2" {
  zone_id  = local.zone_id
  name     = local.zone_name
  type     = "MX"
  content  = "alt2.aspmx.l.google.com"
  priority = 5
  ttl      = local.ttl_automatic
  proxied  = false
}

resource "cloudflare_dns_record" "mx_aspmx2" {
  zone_id  = local.zone_id
  name     = local.zone_name
  type     = "MX"
  content  = "aspmx2.googlemail.com"
  priority = 10
  ttl      = local.ttl_automatic
  proxied  = false
}

resource "cloudflare_dns_record" "mx_aspmx3" {
  zone_id  = local.zone_id
  name     = local.zone_name
  type     = "MX"
  content  = "aspmx3.googlemail.com"
  priority = 10
  ttl      = local.ttl_automatic
  proxied  = false
}
