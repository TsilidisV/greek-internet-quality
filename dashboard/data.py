import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

project_id = st.secrets["gcp_resources"]["project_id"]
bq_dataset = st.secrets["gcp_resources"]["bq_dataset"]

@st.cache_resource
def get_connection():
    credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
    )
    print('ok')
    return bigquery.Client(credentials=credentials)

@st.cache_data(ttl=3600)
def get_regional_metrics():
    client = get_connection()

    query = f"""
        SELECT
            *
        FROM `{project_id}.{bq_dataset}.gold_regional_metrics`
    """

    ###### POLARS ########
    #query_job = client.query(query)  # API request
    #rows = query_job.result()  # Waits for query to finish
#
    #return pl.from_arrow(rows.to_arrow())

    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def get_sessionization():
    client = get_connection()

    query = f"""
        SELECT
            total_tests_in_session,
            time_since_last_session_seconds
        FROM `{project_id}.{bq_dataset}.gold_sessionization`
    """
    return client.query(query).to_dataframe()



@st.cache_data(ttl=3600)
def get_silver():
    client = get_connection()

    query = f"""
        SELECT
            measured_downstream_mbps,
            measured_jitter_msec,
            year
        FROM `{project_id}.{bq_dataset}.silver_measurements`
    """
    return client.query(query).to_dataframe()
