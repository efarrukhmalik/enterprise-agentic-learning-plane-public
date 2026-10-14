locals {
  services = toset([
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "api" {
  account_id   = "learning-plane-api"
  display_name = "Learning Plane API"
}

resource "google_service_account" "worker" {
  account_id   = "learning-plane-worker"
  display_name = "Learning Plane Worker"
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "learning-plane"
  format        = "DOCKER"
  depends_on    = [google_project_service.required]
}

resource "google_pubsub_topic" "events" {
  name       = "learning-plane-events"
  depends_on = [google_project_service.required]
}

resource "google_pubsub_topic" "dead_letter" {
  name       = "learning-plane-events-dead-letter"
  depends_on = [google_project_service.required]
}

resource "google_bigquery_dataset" "evidence" {
  dataset_id                 = "learning_plane_evidence"
  location                   = var.region
  delete_contents_on_destroy = false
  default_table_expiration_ms = 7776000000
  depends_on                 = [google_project_service.required]
}

resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.evidence.dataset_id
  table_id            = "events"
  deletion_protection = true
  schema = jsonencode([
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "tenant_id_hash", type = "STRING", mode = "REQUIRED" },
    { name = "trace_id", type = "STRING", mode = "NULLABLE" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "occurred_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "payload_json", type = "JSON", mode = "NULLABLE" },
  ])
}

resource "google_cloud_run_v2_service" "api" {
  name                = "learning-plane-api"
  location            = var.region
  deletion_protection = true
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  template {
    service_account = google_service_account.api.email
    containers {
      image = var.api_image
      ports { container_port = 8000 }
      startup_probe {
        http_get { path = "/health" }
      }
      env {
        name  = "LEARNING_PLANE_REMOTE_MODEL_ENABLED"
        value = "false"
      }
    }
  }
  depends_on = [google_project_service.required]
}

resource "google_cloud_run_v2_service" "worker" {
  name                = "learning-plane-worker"
  location            = var.region
  deletion_protection = true
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    service_account = google_service_account.worker.email
    containers { image = var.worker_image }
  }
  depends_on = [google_project_service.required]
}

resource "google_pubsub_subscription" "worker" {
  name  = "learning-plane-worker"
  topic = google_pubsub_topic.events.id
  push_config {
    push_endpoint = google_cloud_run_v2_service.worker.uri
    oidc_token { service_account_email = google_service_account.worker.email }
  }
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_project_iam_member" "worker_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "api_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.api.email}"
}

