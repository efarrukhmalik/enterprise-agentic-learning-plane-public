# Google Cloud deployment guide

The local demo is the verified path. Terraform under `infra/gcp/terraform` is an unexecuted deployment design and never runs automatically.

## Intended mapping

| Local component | Google Cloud mapping |
|---|---|
| FastAPI gateway | Private Cloud Run service |
| SQLite event queue | Pub/Sub topic and authenticated push subscription |
| Local worker | Internal Cloud Run worker |
| SQLite analytical sink | BigQuery dataset and table |
| Local deterministic provider | Optional Vertex AI provider |
| Local environment variables | Secret Manager references and runtime identity |
| Container image | Artifact Registry |

## Validation without deployment

```powershell
terraform fmt -check -recursive infra/gcp/terraform
terraform -chdir=infra/gcp/terraform init -backend=false
terraform -chdir=infra/gcp/terraform validate
```

`terraform plan` requires a project, billing, enabled credentials, and immutable image URIs. Review IAM and costs before planning. Apply and destroy are deliberate operator actions and are outside the demo.

## Cost shutdown caution

Disable traffic and inspect BigQuery, Pub/Sub retention, Artifact Registry, and Cloud Run usage before removal. `terraform destroy` may delete infrastructure and can be blocked by deletion protection; never run it against an unknown project.

