import boto3
import json
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock

from datetime import datetime

from src.utils.upload import generate_s3_file_path, upload_file_to_s3, get_bucket_names_from_tf_state


@pytest.fixture
def s3_upload_setup():
    """
    Sets up a mock AWS S3 environment for testing.
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
                    "gdpr_input_bucket": {"value": "input-bucket-name"},
                    "gdpr_processed_bucket": {"value": "processed-bucket-name"},
                    "gdpr_invocation_bucket": {"value": "invocation-bucket-name"}
                }
            })
        )
        yield bucket_name, object_key  


def test_get_bucket_names_from_tf_state(s3_upload_setup):
    bucket_name, object_key = s3_upload_setup  
    result = get_bucket_names_from_tf_state(bucket_name, object_key)

    assert result == ("input-bucket-name", "processed-bucket-name", "invocation-bucket-name")

def test_get_bucket_names_from_tf_state_no_such_key():
    bucket_name = "tf-state-gdpr-obfuscator"
    object_key = "non-existent-key"
    
    result = get_bucket_names_from_tf_state(bucket_name, object_key)
    assert result == (None, None, None)


def test_generate_s3_file_path():
    """
    Tests the generation of a unique timestamped S3 file path.
    """
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    with patch('src.utils.upload.datetime') as mock_datetime:
        fixed_timestamp = datetime(2024, 9, 12, 15, 30, 45)
        mock_datetime.now.return_value = fixed_timestamp

        expected_timestamp = fixed_timestamp.strftime('%Y_%d_%m_%H:%M:%S')
        expected_s3_file_path = f"{expected_timestamp}_dummy_data_20_entries.csv"
        result = generate_s3_file_path(local_file_path)
        assert result == expected_s3_file_path


def test_upload_file_to_s3_valid_input(s3_upload_setup):
    """
    Tests uploading a valid file to S3.
    """
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    bucket_name = "test-bucket"

    with patch('os.path.isfile', return_value=True), \
         patch('src.utils.upload.s3.upload_file') as mock_s3_upload:
        
        result = upload_file_to_s3(local_file_path, bucket_name)

        mock_s3_upload.assert_called_once()

        assert result.startswith(datetime.now().strftime('%Y_%d_%m_%H:%M:%S'))


def test_upload_file_to_s3_file_not_found():
    local_file_path = 'src/data/non_existent_file.csv'
    bucket_name = "test-bucket"
    expected_error_message = f"Error: The file {local_file_path} does not exist."
    
    with patch('builtins.print') as mock_print:
        result = upload_file_to_s3(local_file_path, bucket_name)
        mock_print.assert_called_once_with(expected_error_message)
        assert result is None


def test_upload_file_to_s3_generates_unique_timestamped_filename():
    """
    Tests if a unique timestamped filename is generated during S3 upload.
    """
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    bucket_name = "test-bucket"

    with patch('src.utils.upload.datetime') as mock_datetime, \
         patch('src.utils.upload.s3.upload_file') as mock_s3_upload:
        
        fixed_timestamp = datetime(2024, 9, 12, 15, 30, 45)
        mock_datetime.now.return_value = fixed_timestamp

        result = upload_file_to_s3(local_file_path, bucket_name)

        expected_timestamp = fixed_timestamp.strftime('%Y_%d_%m_%H:%M:%S')
        expected_s3_file_path = f"{expected_timestamp}_dummy_data_20_entries.csv"

        assert result == expected_s3_file_path


@pytest.mark.parametrize(
    "bucket_name, object_key, mock_response, expected, test_id",
    [
        (
            "test-bucket", 
            "test-key", 
            {
                "Body": MagicMock(read=MagicMock(return_value=json.dumps({
                    "outputs": {
                        "gdpr_input_bucket": {"value": "input-bucket"},
                        "gdpr_processed_bucket": {"value": "processed-bucket"},
                        "gdpr_invocation_bucket": {"value": "invocation-bucket"}
                    }
                }).encode('utf-8')))
            }, 
            ("input-bucket", "processed-bucket", "invocation-bucket"),
            "happy_path"
        ),
        (
            "test-bucket", 
            "test-key", 
            {
                "Body": MagicMock(read=MagicMock(return_value=json.dumps({
                    "outputs": {
                        "gdpr_input_bucket": {"value": ""},
                        "gdpr_processed_bucket": {"value": ""},
                        "gdpr_invocation_bucket": {"value": ""}
                    }
                }).encode('utf-8')))
            }, 
            ("", "", ""),
            "empty_bucket_names"
        ),
        (
            "test-bucket", 
            "test-key", 
            {
                "Body": MagicMock(read=MagicMock(return_value=json.dumps({
                    "outputs": {}
                }).encode('utf-8')))
            }, 
            (None, None, None),
            "missing_keys"
        ),
        (
            "test-bucket", 
            "test-key", 
            {
                "Body": MagicMock(read=MagicMock(return_value=b"invalid json"))
            }, 
            (None, None, None),
            "invalid_json"
        ),
        (
            "test-bucket", 
            "test-key", 
            Exception("S3 error"), 
            (None, None, None),
            "s3_exception"
        ),
    ],
    ids=[test_id for _, _, _, _, test_id in [
        ("test-bucket", "test-key", None, None, "happy_path"),
        ("test-bucket", "test-key", None, None, "empty_bucket_names"),
        ("test-bucket", "test-key", None, None, "missing_keys"),
        ("test-bucket", "test-key", None, None, "invalid_json"),
        ("test-bucket", "test-key", None, None, "s3_exception"),
    ]]
)
@patch('src.utils.upload.s3.get_object')
def test_get_bucket_names_from_tf_state(mock_get_object, bucket_name, object_key, mock_response, expected, test_id):
    if isinstance(mock_response, Exception):
        mock_get_object.side_effect = mock_response
    else:
        mock_get_object.return_value = mock_response

    result = get_bucket_names_from_tf_state(bucket_name, object_key)

    assert result == expected
    
