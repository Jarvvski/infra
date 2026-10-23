output "zone_id" {
  description = "Cloudflare zone id for jarvis.gg."
  value       = local.zone_id
}

output "dns_record_ids" {
  description = "DNS record ids managed for jarvis.gg."
  value = {
    apex_a                 = { for ip, record in cloudflare_dns_record.apex_a : ip => record.id }
    apex_aaaa              = { for ip, record in cloudflare_dns_record.apex_aaaa : ip => record.id }
    www                    = cloudflare_dns_record.www.id
    github_pages_challenge = cloudflare_dns_record.github_pages_challenge.id
    mx_aspmx               = cloudflare_dns_record.mx_aspmx.id
    mx_alt1                = cloudflare_dns_record.mx_alt1.id
    mx_alt2                = cloudflare_dns_record.mx_alt2.id
    mx_aspmx2              = cloudflare_dns_record.mx_aspmx2.id
    mx_aspmx3              = cloudflare_dns_record.mx_aspmx3.id
  }
}
