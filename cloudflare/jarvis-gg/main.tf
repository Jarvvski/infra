locals {
  # Public zone identifier returned by the Cloudflare API. Not a secret.
  zone_id   = "25a69e647ecf731fb8268a02b55e8afa"
  zone_name = "jarvis.gg"

  # ttl 1 is Cloudflare's "automatic" TTL.
  ttl_automatic = 1

  # GitHub Pages apex addresses, checked against
  # https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
  # on 2026-10-23. DNS only: proxied stays false.
  github_pages_ipv4 = toset([
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
  ])
  github_pages_ipv6 = toset([
    "2606:50c0:8000::153",
    "2606:50c0:8001::153",
    "2606:50c0:8002::153",
    "2606:50c0:8003::153",
  ])
}

resource "cloudflare_dns_record" "apex_a" {
  for_each = local.github_pages_ipv4

  zone_id = local.zone_id
  name    = local.zone_name
  type    = "A"
  content = each.value
  ttl     = local.ttl_automatic
  proxied = false
}

resource "cloudflare_dns_record" "apex_aaaa" {
  for_each = local.github_pages_ipv6

  zone_id = local.zone_id
  name    = local.zone_name
  type    = "AAAA"
  content = each.value
  ttl     = local.ttl_automatic
  proxied = false
}

resource "cloudflare_dns_record" "www" {
  zone_id = local.zone_id
  name    = "www.${local.zone_name}"
  type    = "CNAME"
  content = "jarvvski.github.io"
  ttl     = local.ttl_automatic
  proxied = false
}

# GitHub Pages domain verification for the Jarvvski account. The token is public.
resource "cloudflare_dns_record" "github_pages_challenge" {
  zone_id = local.zone_id
  name    = "_github-pages-challenge-jarvvski.${local.zone_name}"
  type    = "TXT"
  content = "8246776e59edf2bb27a58013c4317d"
  ttl     = local.ttl_automatic
  proxied = false
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
