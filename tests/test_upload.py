import boto3
import json
import pytest

from moto import mock_aws
from unittest.mock import patch, MagicMock
import os
from datetime import datetime
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from src.utils.upload import generate_s3_file_path, read_bucket_name, upload_file_to_s3

@pytest.fixture
def s3_upload_setup():
    """
    This fixture sets up a mock AWS S3 environment for testing purposes.
    It creates a bucket named "tf-state-gdpr-obfuscator" and uploads a JSON file named "tf-state" to it.
    The JSON file contains a single output named "gdpr_bucket" with a value of "test-bucket".

    Returns:
        None (as it is a fixture, it does not return a value directly)
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')  
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"

        # Create a new S3 bucket
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

        # Upload a JSON file to the bucket
        s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps({
                "outputs": {
                    "gdpr_bucket": {
                        "value": "test-bucket",
                        "type": "string"
                    }
                }
            })
        )
        yield

    """
    This function tests the read_bucket_name function when AWS credentials are not available.

    Parameters:
    None: This function does not take any parameters. It uses a mock AWS S3 environment and patches the s3.get_object method to simulate a NoCredentialsError exception.

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name is None when AWS credentials are not available.

    Note:
    This function uses the pytest fixture s3_upload_setup to set up a mock AWS S3 environment.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"
        
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps({
                "outputs": {
                    "gdpr_bucket": {
                        "value": "test-bucket",
                        "type": "string"
                    }
                }
            })
        )

        with patch('src.utils.upload.s3.get_object', side_effect=NoCredentialsError):
            result = read_bucket_name()
            assert result is None
def test_read_bucket_name(s3_upload_setup):
    """
    This function tests the read_bucket_name function by verifying that it correctly retrieves the name of the GDPR bucket from the Terraform state file.

    Parameters:
    s3_upload_setup (fixture): A pytest fixture that sets up a mock AWS S3 environment for testing purposes. It creates a bucket named "tf-state-gdpr-obfuscator" and uploads a JSON file named "tf-state" to it. The JSON file contains a single output named "gdpr_bucket" with a value of "test-bucket".

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name matches the expected value.
    """
    bucket_name = read_bucket_name()
    assert bucket_name == "test-bucket"
def test_read_bucket_name_no_such_key():
    """
    This function tests the read_bucket_name function when the specified key does not exist in the S3 bucket.

    Parameters:
    None: This function does not take any parameters. It uses a mock AWS S3 environment and patches the s3.get_object method to simulate a NoSuchKey exception.

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name is None when the specified key does not exist.

    This function uses the pytest fixture s3_upload_setup to set up a mock AWS S3 environment.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        bucket_name = "tf-state-gdpr-obfuscator"
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

        with patch('src.utils.upload.s3.get_object', side_effect=s3.exceptions.NoSuchKey):
            result = read_bucket_name()
            assert result is None
def test_read_bucket_name_json_decode_error():
    """
    This function tests the read_bucket_name function when the Terraform state file contains invalid JSON.

    Parameters:
    None: This function does not take any parameters. It uses a mock AWS S3 environment and uploads a non-JSON file to the S3 bucket.

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name is None when the Terraform state file contains invalid JSON.

    Note:
    This function uses the pytest fixture s3_upload_setup to set up a mock AWS S3 environment.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"

        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        s3.put_object(Bucket=bucket_name, Key=object_key, Body='not a json')

        result = read_bucket_name()
        assert result is None
def test_read_bucket_name_no_credentials():
    """
    This function tests the read_bucket_name function when AWS credentials are not available.

    Parameters:
    None: This function does not take any parameters. It uses a mock AWS S3 environment and patches the s3.get_object method to simulate a NoCredentialsError exception.

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name is None when AWS credentials are not available.

    Note:
    This function uses the pytest fixture s3_upload_setup to set up a mock AWS S3 environment.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"

        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps({
                "outputs": {
                    "gdpr_bucket": {
                        "value": "test-bucket",
                        "type": "string"
                    }
                }
            })
        )

        with patch('src.utils.upload.s3.get_object', side_effect=NoCredentialsError):
            result = read_bucket_name()
            assert result is None
def test_read_bucket_name_partial_credentials():
    """
    This function tests the read_bucket_name function when AWS credentials are partially available.

    Parameters:
    None: This function does not take any parameters. It uses a mock AWS S3 environment and patches the s3.get_object method to simulate a PartialCredentialsError exception.

    Returns:
    None: This function does not return a value directly. It asserts that the retrieved bucket name is None when AWS credentials are partially available.

    Note:
    This function uses the pytest fixture s3_upload_setup to set up a mock AWS S3 environment.
    """
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"

        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps({
                "outputs": {
                    "gdpr_bucket": {
                        "value": "test-bucket",
                        "type": "string"
                    }
                }
            })
        )

        with patch('src.utils.upload.s3.get_object', side_effect=PartialCredentialsError):
            result = read_bucket_name()
            assert result is None
def test_generate_s3_file_path():
    """
    This function tests the generate_s3_file_path function by verifying that it correctly generates a unique timestamped file path for an input local file path.

    Parameters:
    local_file_path (str): The local file path for which the timestamped file path needs to be generated. It should be a valid file path.

    Returns:
    str: The generated timestamped file path. The file path is in the format "{timestamp}_{filename}", where timestamp is in the format "YYYY_DD_MM_HH:MM:SS".
    """
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    with patch('src.utils.upload.datetime') as mock_datetime:
        fixed_timestamp = datetime(2024, 9, 12, 15, 30, 45)
        mock_datetime.now.return_value = fixed_timestamp
        expected_timestamp = fixed_timestamp.strftime('%Y_%d_%m_%H:%M:%S')
        expected_file_name = os.path.basename(local_file_path)
        expected_s3_file_path = f"{expected_timestamp}_{expected_file_name}"
        result = generate_s3_file_path(local_file_path)
        assert result == expected_s3_file_path
def test_upload_file_to_s3_valid_input():
    """
    This function tests the upload_file_to_s3 function with valid input.

    Parameters:
    local_file_path (str): The local file path of the file to be uploaded. It should be a valid file path.
    bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    str: The generated timestamped file path in the S3 bucket. The file path is in the format "{timestamp}_{filename}", where timestamp is in the format "YYYY_DD_MM_HH:MM:SS".
    """
    # Arrange
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    bucket_name = "test-bucket"
    expected_s3_file_path = generate_s3_file_path(local_file_path)

    # Mock the s3.upload_file method
    with patch('src.utils.upload.s3') as mock_aws:
        mock_aws.upload_file.return_value = None

        # Act
        result = upload_file_to_s3(local_file_path, bucket_name)

        # Assert
        mock_aws.upload_file.assert_called_once_with(
            local_file_path, bucket_name, expected_s3_file_path
        )
        assert result == expected_s3_file_path
def test_upload_file_to_s3_file_not_found():
    """
    This function tests the upload_file_to_s3 function when the specified local file does not exist.

    Parameters:
    local_file_path (str): The local file path of the file to be uploaded. It should be a valid file path.
    bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    None: If the specified local file does not exist, the function prints an error message and returns None.
    """
    # Arrange
    local_file_path = 'src/data/non_existent_file.csv'
    bucket_name = "test-bucket"
    expected_error_message = f"The file {local_file_path} does not exist"

    # Mock the print function to capture error messages
    with patch('builtins.print') as mock_print:
        # Act
        result = upload_file_to_s3(local_file_path, bucket_name)

        # Assert
        mock_print.assert_called_once_with(expected_error_message)
        assert result is None
def test_upload_file_to_s3_generates_unique_timestamped_filename():
    """
    This function tests the upload_file_to_s3 function to ensure it generates a unique timestamped filename.

    Parameters:
    local_file_path (str): The local file path of the file to be uploaded. It should be a valid file path.
    bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    None: This function does not return a value directly. It asserts that the generated timestamped file path matches the expected value.
    """
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    bucket_name = "test-bucket"


    with patch('src.utils.upload.datetime') as mock_datetime, \
        patch('src.utils.upload.s3') as mock_aws:

        fixed_timestamp = datetime(2024, 9, 12, 15, 30, 45)
        mock_datetime.now.return_value = fixed_timestamp


        mock_aws.upload_file.return_value = None


        result = upload_file_to_s3(local_file_path, bucket_name)


        expected_timestamp = fixed_timestamp.strftime('%Y_%d_%m_%H:%M:%S')
        expected_file_name = os.path.basename(local_file_path)
        expected_s3_file_path = f"{expected_timestamp}_{expected_file_name}"
        assert result == expected_s3_file_path

