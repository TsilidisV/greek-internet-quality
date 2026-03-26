## Getting Started

### Prerequisites
- [Terraform](https://developer.hashicorp.com/terraform/install)
- [Make](https://www.gnu.org/software/make/)
- [uv](https://docs.astral.sh/uv/)
- [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk)
- A [GCP](https://console.cloud.google.com/) account with a project.
- Forking and/or downloading this repo.
- A Github account with a Github repo and a fine-grained personal access token with a Secrets permission (read and write) for your specific repo. Then, run:
    ```bash
    cd infrastructure 
    cp secrets.auto.tfvars.example secrets.auto.tfvars
    # copies secrets.auto.tfvars.example as secrets.auto.tfvars
    ```
    and add your github token to the `secrets.auto.tfvars` file.

All commands need to be executed in Bash. If you're on Windows, [git bash](https://git-scm.com/install/) is recommended.

### Infrastructure
Edit `infrastructure/variables.tf` with your desired project ID (the project needs to already exist), bucket name, dataset name, Github repo etc.

```bash
make infra-up
```
Logs you in to Google Cloud CLI and builds the infrastructure.

You might get the error: "Error waiting for Creating Job: Error code 5, message: Image 'mirror.gcr.io/<your_docker_image>' not found.", but don't worry, we haven't pushed the image to dockerhub yet. Nevertheless, the job has been created.

### Ingest

#### Local
```bash
make create-ingestor-key
```
downloads service account key for data ingestion with writing to bucket permissions and creates a `.env` file with INGESTOR_GCP_KEY and GCS_BUCKET_NAME which are read in python.

```python
uv run --directory ingest python -m src.main monthly

uv run --directory ingest python -m src.main monthly 2023 11

uv run --directory ingest python -m src.main backfill '2015-07' '2020-02'
```
uploads files to the GCS bucket.

#### Online

Github Actions automatically connects to GCP and ingest the data of the previous month every 1st day of each month at 04:14 UTC.

### Transform
#### Local
```bash
make create-transformer-key
```
downloads service account key for load and transform with reading to bucket and writing to dataset permissions and creates a `.env` file with TRANSFORM_GCP_KEY, GCS_BUCKET_NAME and BQ_DATASET which are read in the `docker-compose.yml`.

```bash
make docker-run
```
Builds and locally runs the dockerfile. Docker Engine needs to be running on your system.


#### Online

```bash
make image-push
```
Builds and pushes image to docker hub. This also addresses the error of `Image 'mirror.gcr.io/<your_docker_image>' not found` we had earlier.

It might take awhile for google cloud run to find the image because >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 



### Dashboard
#### Local
```bash
make create-dashboard-key
```
downloads service account key for dashboard with reading and querying to BigQuery and creates a `secrets.toml` file in `dashboard/.streamlit/`.

Then, the dashboard opens, by running
```bash
uv run --directory dashboard streamlit run app.py
```

```bash
d2 --theme=200 --layout=elk ./docs/architecture.d2
```


![GCP Medallion Architecture](./docs/architecture.svg)