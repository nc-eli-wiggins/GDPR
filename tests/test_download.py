import pytest
import pandas as pd

import boto3
from moto import mock_aws
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
import json


from unittest.mock import patch, mock_open
from src.utils.download import load_s3_file_info, convert_df_to_bytestream, read_csv_from_s3
@pytest.fixture
def export_dir() -> str:
    """
    This function returns the directory path where S3 files will be downloaded and saved.

    Parameters:
    None

    Returns:
    str: The directory path where S3 files will be downloaded and saved.
    """
    return 'output/s3_files'
@pytest.fixture
def s3_download_csv_setup():
    """
    This fixture sets up a mock AWS environment and prepares a test CSV file in an S3 bucket for testing purposes.

    Returns:
    tuple: A tuple containing the boto3 S3 client, the name of the S3 bucket, and the path of the test CSV file.

    Note:
    - The mock AWS environment is created using the `moto` library.
    - The test CSV file is created in the specified S3 bucket with the given file path.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        download_bucket_name = "tf-state-gdpr-obfuscator"
        s3_file_path = "test-data.csv"

        s3.create_bucket(Bucket=download_bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        csv_data = "col1,col2\nval1,val2\nval3,val4\n"
        s3.put_object(Bucket=download_bucket_name, Key=s3_file_path, Body=csv_data)
        yield s3, download_bucket_name, s3_file_path
def test_load_s3_file_info_valid_json(export_dir):
    """
    This function tests the load_s3_file_info function with a valid JSON file containing S3 bucket name and file path.

    Parameters:
    export_dir (str): The directory path where the S3 file info JSON file is located.

    Returns:
    None

    - Uses the mock_open and patch functions from the unittest.mock module to mock the file open operation and os.path.exists function.
    - Asserts that the function correctly extracts the bucket name and S3 file path from the JSON file.
    """
    mock_json_content = json.dumps({
        "bucket_name": "test-bucket",
        "s3_file_path": "test-file-path"
    })

    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        with patch("os.path.exists", return_value=True):

            bucket_name, s3_file_path = load_s3_file_info(export_dir)

            assert bucket_name == "test-bucket"
            assert s3_file_path == "test-file-path"
def test_load_s3_file_info_file_not_exist(export_dir):
    """
    This function tests the load_s3_file_info function when the S3 file info JSON file does not exist.

    Parameters:
    export_dir (str): The directory path where the S3 file info JSON file is located.

    Returns:
    None

    This function uses the mock_open and patch functions from the unittest.mock module to mock the file open operation and os.path.exists function.
    It asserts that the function correctly handles the case when the file does not exist, printing an appropriate message and returning None for both bucket_name and s3_file_path.
    """
    with patch("os.path.exists", return_value=False):
        with patch("builtins.print") as mock_print:
            bucket_name, s3_file_path = load_s3_file_info(export_dir)

            assert bucket_name is None
            assert s3_file_path is None
            mock_print.assert_called_once_with(f"The file {os.path.join(export_dir, 's3_file_info.json')} does not exist")
def test_load_s3_file_info_invalid_json_structure(export_dir):
    """
    This function tests the load_s3_file_info function when the S3 file info JSON file contains an invalid structure.

    Parameters:
    export_dir (str): The directory path where the S3 file info JSON file is located.

    Returns:
    None

    This function uses the mock_open and patch functions from the unittest.mock module to mock the file open operation and os.path.exists function.
    It asserts that the function correctly handles the case when the JSON file contains an invalid structure, returning None for both bucket_name and s3_file_path.

    
    - The mock_json_content variable contains a JSON string with an invalid structure.
    - The with patch statements mock the open and os.path.exists functions to simulate the file existence and content.
    - The assert statements verify that the function returns None for both bucket_name and s3_file_path.
    """
    mock_json_content = json.dumps({
        "wrong_key": "value"
    })

    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        with patch("os.path.exists", return_value=True):
            bucket_name, s3_file_path = load_s3_file_info(export_dir)

            assert bucket_name is None
            assert s3_file_path is None
def test_convert_df_to_bytestream():
    """
    This function tests the convert_df_to_bytestream function, which converts a pandas DataFrame to a bytestream in CSV format.

    Parameters:
    None

    Returns:
    None

    This function creates a pandas DataFrame with two columns 'col1' and 'col2', containing the values ['val1', 'val2'] and ['val3', 'val4'] respectively.
    It then calls the convert_df_to_bytestream function with this DataFrame as input.
    The resulting bytestream is decoded to a string and compared with the expected CSV content.
    
    """
    df = pd.DataFrame({
        'col1': ['val1', 'val2'],
        'col2': ['val3', 'val4']
    })

    bytestream = convert_df_to_bytestream(df)

    expected_csv = "col1,col2\nval1,val3\nval2,val4\n"

    bytestream_content = bytestream.getvalue().decode('utf-8')

    assert bytestream_content == expected_csv
def test_read_csv_from_s3(s3_download_csv_setup):
    """
    This function tests the read_csv_from_s3 function, which reads a CSV file from an S3 bucket and returns it as a bytestream.

    Parameters:
    s3_download_csv_setup (tuple): A tuple containing the boto3 S3 client, the name of the S3 bucket, and the path of the test CSV file.
        - s3 (boto3.client): The boto3 S3 client.
        - bucket_name (str): The name of the S3 bucket.
        - s3_file_path (str): The path of the test CSV file in the S3 bucket.

    Returns:
    None

    This function reads the test CSV file from the specified S3 bucket using the read_csv_from_s3 function.
    """
    s3, bucket_name, s3_file_path = s3_download_csv_setup

    bytestream = read_csv_from_s3(bucket_name, s3_file_path)

    expected_csv = "col1,col2\nval1,val2\nval3,val4\n"

    bytestream_content = bytestream.getvalue().decode('utf-8')

    assert bytestream_content == expected_csv
def test_read_csv_from_s3_file_not_exist(s3_download_csv_setup):
    """
    Test the read_csv_from_s3 function when the specified CSV file does not exist in the S3 bucket.

    Parameters:
    s3_download_csv_setup (tuple): A tuple containing the boto3 S3 client, the name of the S3 bucket, and the path of the test CSV file.
        - s3 (boto3.client): The boto3 S3 client.
        - bucket_name (str): The name of the S3 bucket.
        - s3_file_path (str): The path of the test CSV file in the S3 bucket.

    Returns:
    None

    This function simulates a scenario where the specified CSV file does not exist in the S3 bucket.
    """
    s3, bucket_name, _ = s3_download_csv_setup
    s3_file_path = "non-existent-file.csv"

    bytestream = read_csv_from_s3(bucket_name, s3_file_path)

    assert bytestream is None
def test_read_csv_from_s3_invalid_credentials():
    """
    This function tests the read_csv_from_s3 function when the AWS credentials are invalid.

    Parameters:
    bucket_name (str): The name of the S3 bucket where the CSV file is located.
    s3_file_path (str): The path of the CSV file in the S3 bucket.

    Returns:
    None

    This function simulates a scenario where the AWS credentials are invalid.
    It patches the boto3 client to raise a NoCredentialsError when creating a client.
    The read_csv_from_s3 function is then called with the invalid credentials.
    """
    bucket_name = "test-bucket"
    s3_file_path = "test-file.csv"

    with patch("boto3.client") as mock_client:
        mock_client.side_effect = NoCredentialsError()

        bytestream = read_csv_from_s3(bucket_name, s3_file_path)

        assert bytestream is None
def test_read_csv_from_s3_partial_credentials():
    """
    This function tests the read_csv_from_s3 function when the AWS credentials are partially invalid.

    Parameters:
    bucket_name (str): The name of the S3 bucket where the CSV file is located.
    s3_file_path (str): The path of the CSV file in the S3 bucket.

    Returns:
    None

    This function simulates a scenario where the AWS credentials are partially invalid.
    It patches the boto3 client to raise a PartialCredentialsError when creating a client.
    The read_csv_from_s3 function is then called with the partially invalid credentials.
    """
    bucket_name = "test-bucket"
    s3_file_path = "test-file.csv"

    with patch("boto3.client") as mock_client:
        mock_client.side_effect = PartialCredentialsError(provider='aws', cred_var='aws_secret_access_key', message='Incomplete credentials provided')

        bytestream = read_csv_from_s3(bucket_name, s3_file_path)

        assert bytestream is None