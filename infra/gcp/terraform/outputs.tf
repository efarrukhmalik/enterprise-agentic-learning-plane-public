output "api_uri" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Internal Cloud Run API URI."
}

output "events_topic" {
  value       = google_pubsub_topic.events.name
  description = "Event topic used by the governed evidence path."
}

