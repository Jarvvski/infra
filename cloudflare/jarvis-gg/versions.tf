terraform {
  required_version = ">= 1.6.3"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.28.1"
    }
  }

  # Partial configuration for Cloudflare R2 (S3-compatible).
  # The endpoint is intentionally absent: it contains the Cloudflare account id.
  # Supply it at init time with -backend-config=backend.hcl (see backend.hcl.example).
  # Credentials are AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (the R2 API token).
  # skip_s3_checksum requires Terraform >= 1.6.3.
  backend "s3" {
    bucket = "jarvvski-tfstate"
    key    = "cloudflare/jarvis-gg/terraform.tfstate"
    region = "auto"

    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}

provider "cloudflare" {
  # Reads CLOUDFLARE_API_TOKEN from the environment. Do not hard-code a token.
}
