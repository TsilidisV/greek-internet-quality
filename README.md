## Getting Started

### Prerequisites
- [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk)
- [Terraform](https://developer.hashicorp.com/terraform/install)
- [Make](https://www.gnu.org/software/make/)
- Create a github repo and make a fine-grained personal access token with a Secrets permission (read and write) for your specific repo. Then, run:
    ```bash
    cd infrastructure 
    cp secrets.auto.tfvars.example secrets.auto.tfvars
    # copies secrets.auto.tfvars.example as secrets.auto.tfvars
    ```
    and add your github token to the `secrets.auto.tfvars` file.

#### Local
- uv / python

### Infrastructure
Edit `infrastructure/variables.tf` with your desired project ID (theproject needs to already exist), bucket name, dataset name, etc.

```bash
make infra-up
```
Logs you in to gcloud cli and build infrastructure by creating a service account for uploading data to the lake, a service account for reading the lake and writing to BigQuery, a GCP bucket, a BigQuery dataset, and a Google Cloud Run Job.

You might get the error: "Error waiting for Creating Job: Error code 5, message: Image 'mirror.gcr.io/<your_docker_image>' not found.", but don't worry, since we haven't pushed the image to dockerhub yet. Nevertheless, the job has been created.

### Ingest

#### Local
```bash
make create-ingestor-key
```
downloads service account key for ingest with writing to bucket permissions and creates a `.env` file with INGESTOR_GCP_KEY and GCS_BUCKET_NAME which are read in python.

```python
uv run --directory ingest python -m src.main monthly

uv run --directory ingest python -m src.main monthly 2023 11

uv run --directory ingest python -m src.main backfill '2015-07' '2020-02'
```
uploads files to the GCS bucket.

#### Online

To have automated ingestion through github actions add an `INGESTOR_GCP_KEY` and a `GCS_BUCKET_NAME` secret to your forked github repository, with the contents of the `transform-gcp-key.json` and your chosen name of the GCS bucket, respectively.

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