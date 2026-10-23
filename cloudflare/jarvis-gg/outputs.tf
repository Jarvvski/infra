output "zone_id" {
  description = "Cloudflare zone id for jarvis.gg."
  value       = local.zone_id
}

output "dns_record_ids" {
  description = "DNS record ids managed for jarvis.gg, keyed by Terraform address suffix."
  value = {
    apex      = cloudflare_dns_record.apex.id
    mx_aspmx  = cloudflare_dns_record.mx_aspmx.id
    mx_alt1   = cloudflare_dns_record.mx_alt1.id
    mx_alt2   = cloudflare_dns_record.mx_alt2.id
    mx_aspmx2 = cloudflare_dns_record.mx_aspmx2.id
    mx_aspmx3 = cloudflare_dns_record.mx_aspmx3.id
  }
}
