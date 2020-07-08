variable "org_name" {}
variable "api_token" {}
variable "base_url" {}
variable "demo_app_name" { default="travelagency" }
variable "udp_subdomain" { default="local-zartan"}
variable "app_uri" { default="localhost:8666" }

locals {
    app_url = var.app_uri
}

provider "okta" {
  org_name  = var.org_name
  api_token = var.api_token
  base_url  = var.base_url
  version   = "~> 3.0"
}
provider "template" {
  version = "~> 2.1"
}
provider "local" {
  version = "~> 1.2"
}
data "okta_group" "all" {
  name = "Everyone"
}
resource "okta_app_oauth" "travelagency" {
  label          = "${var.udp_subdomain} ${var.demo_app_name} Demo (Generated by UDP)"
  type           = "web"
  grant_types    = ["authorization_code"]
  redirect_uris  = [
    "https://${local.app_url}/authorization-code/callback",
    "http://${local.app_url}/authorization-code/callback"
  ]
  response_types = ["code"]
  issuer_mode    = "ORG_URL"
  consent_method = "TRUSTED"
  groups         = ["${data.okta_group.all.id}"]
}
resource "okta_trusted_origin" "travelagency-https" {
  name   = "${var.udp_subdomain} ${var.demo_app_name} HTTPS"
  origin = "https://${local.app_url}"
  scopes = ["REDIRECT", "CORS"]
}
resource "okta_trusted_origin" "travelagency-http" {
  name   = "${var.udp_subdomain} ${var.demo_app_name} HTTP"
  origin = "http://${local.app_url}"
  scopes = ["REDIRECT", "CORS"]
}
resource "okta_auth_server" "travelagency" {
  name        = "${var.udp_subdomain} ${var.demo_app_name}"
  description = "Generated by UDP"
  audiences   = ["api://${local.app_url}"]
}
resource "okta_auth_server_policy" "travelagency" {
  auth_server_id   = okta_auth_server.travelagency.id
  status           = "ACTIVE"
  name             = "standard"
  description      = "Generated by UDP"
  priority         = 1
  client_whitelist = ["${okta_app_oauth.travelagency.id}"]
}
resource "okta_auth_server_policy_rule" "travelagency" {
  auth_server_id       = okta_auth_server.travelagency.id
  policy_id            = okta_auth_server_policy.travelagency.id
  status               = "ACTIVE"
  name                 = "one_hour"
  priority             = 1
  group_whitelist      = ["${data.okta_group.all.id}"]
  grant_type_whitelist = ["authorization_code"]
  scope_whitelist      = ["*"]
}
data "template_file" "configuration" {
  template = "${file("${path.module}/travelagency.dotenv.template")}"
  vars = {
    client_id         = "${okta_app_oauth.travelagency.client_id}"
    client_secret     = "${okta_app_oauth.travelagency.client_secret}"
    domain            = "${var.org_name}.${var.base_url}"
    auth_server_id    = "${okta_auth_server.travelagency.id}"
    issuer            = "${okta_auth_server.travelagency.issuer}"
    okta_app_oauth_id = "${okta_app_oauth.travelagency.id}"
  }
}
resource "local_file" "dotenv" {
  content  = data.template_file.configuration.rendered
  filename = "${path.module}/travelagency.env"
}