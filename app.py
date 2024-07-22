import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

st.title("Interactive Dashboard")

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Define the column variations dictionary
column_variations = {
    'campaign': ['campaign', 'campaign name'],
    'impression': ['impression', 'imp', 'impressions', 'impr.', 'impressi\nons'],
    'reach': ['reach'],
    'clicks': ['clicks', 'clk', 'link clicks', 'clicked'],
    'conversion': ['conversion', 'con', 'conv', 'results', 'purchase', 'purchases'],
    'spend': ['amount spent', 'cost'],
    'sent': ['sent'],
    'opened': ['opened'],
    'open_rate': ['open rate'],
    'click_rate': ['click rate'],
    'date': ['day', 'created time', 'date']
}

def standardize_columns(data, column_variations):
    standardized_data = data.copy()
    for standard_name, variations in column_variations.items():
        for variation in variations:
            if variation in standardized_data.columns:
                standardized_data.rename(columns={variation: standard_name}, inplace=True)
                break
    return standardized_data

def process_csv(data, column_variations):
    data = standardize_columns(data, column_variations)
    relevant_columns = ['campaign', 'impression', 'reach', 'clicks', 'conversion']
    processed_data = data[relevant_columns]
    return processed_data

def plot_data(data):
    fig, ax = plt.subplots()
    data.plot(kind='bar', x='campaign', y=['impression', 'reach', 'clicks', 'conversion'], ax=ax)
    st.pyplot(fig)

def filter_data_by_date(data, start_date, end_date):
    mask = (data['date'] >= start_date) & (data['date'] <= end_date)
    return data.loc[mask]

def get_api_data(url, headers):
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    
    try:
        logger.debug(f"Attempting to connect to {url}")
        response = http.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {url} failed: {e}")
        raise

def read_csv_skip_rows(uploaded_file):
    # Try to read the CSV file with different row offsets
    for skip_rows in range(5):  # Adjust the range as needed
        try:
            data = pd.read_csv(uploaded_file, skiprows=skip_rows)
            if not data.empty:
                return data
        except pd.errors.ParserError:
            continue
    st.error("Failed to read the CSV file.")
    raise ValueError("Failed to read the CSV file.")

try:
    api_url = "https://api.example.com/data"
    headers = {"Authorization": "Bearer YOUR_API_KEY"}
    
    api_data = get_api_data(api_url, headers)
    st.write(api_data)
    
except requests.exceptions.HTTPError as http_err:
    st.error(f"HTTP error occurred: {http_err}")
    logger.error(f"HTTP error occurred: {http_err}")
except requests.exceptions.ConnectionError as conn_err:
    st.error(f"Connection error occurred: {conn_err}")
    logger.error(f"Connection error occurred: {conn_err}")
except requests.exceptions.Timeout as timeout_err:
    st.error(f"Timeout error occurred: {timeout_err}")
    logger.error(f"Timeout error occurred: {timeout_err}")
except requests.exceptions.RequestException as req_err:
    st.error(f"An error occurred: {req_err}")
    logger.error(f"An error occurred: {req_err}")

try:
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        data = read_csv_skip_rows(uploaded_file)
        data['date'] = pd.to_datetime(data['date'])
        start_date = st.date_input('Start date', data['date'].min())
        end_date = st.date_input('End date', data['date'].max())
        filtered_data = filter_data_by_date(data, start_date, end_date)
        processed_data = process_csv(filtered_data, column_variations)
        st.write(processed_data)
        plot_data(processed_data)
except Exception as e:
    st.error(f"An error occurred: {e}")
    logger.error(f"An error occurred: {e}")
