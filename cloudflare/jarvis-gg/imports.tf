# Record ids are public DNS identifiers, not secrets.
# Import id format for provider v5 is "<zone_id>/<dns_record_id>".
# The previous apex A record (46.101.80.89) is intentionally not imported.
# Once that record is in state from the import apply, removing its resource
# destroys it. MX imports stay so those records are not recreated.

import {
  to = cloudflare_dns_record.mx_aspmx
  id = "25a69e647ecf731fb8268a02b55e8afa/3a83636116fbdd503cd53b4dd308e0f0"
}

import {
  to = cloudflare_dns_record.mx_alt1
  id = "25a69e647ecf731fb8268a02b55e8afa/0a6b4a8ba79f45cb079af04ec0dd575c"
}

import {
  to = cloudflare_dns_record.mx_alt2
  id = "25a69e647ecf731fb8268a02b55e8afa/9c425b9a0f8cebfe221a259e3a78bc79"
}

import {
  to = cloudflare_dns_record.mx_aspmx2
  id = "25a69e647ecf731fb8268a02b55e8afa/9f71afd265c8831e0fbe51092c6f185d"
}

import {
  to = cloudflare_dns_record.mx_aspmx3
  id = "25a69e647ecf731fb8268a02b55e8afa/47b70150a5771195aa9f60d1f39410d5"
}
