import pytest
import pandas as pd
import boto3
import json

from unittest import mock
from unittest.mock import patch
from io import BytesIO
from moto import mock_aws
from src.utils.processing2 import (
    get_bucket_names_from_tf_state,
    obfuscate_pii,
    get_keys_from_bucket,
    empty_bucket,
    handler,
)
from botocore.exceptions import ClientError
import logging


@pytest.fixture
def mock_aws_s3():
    with mock_aws():
        s3 = boto3.client("s3", region_name="eu-west-2")
        bucket_name = "tf-state-gdpr-obfuscator"
        object_key = "tf-state"

        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        mock_input_bucket_name = "mock-input-bucket-name"
        mock_processed_bucket_name = "mock-processed-bucket-name"
        mock_invocation_bucket_name = "mock-invocation-bucket-name"

        state_file_content = {
            "version": 4,
            "terraform_version": "1.6.6",
            "serial": 45,
            "lineage": "92ed6dfd-fecf-ec4d-15ab-f2f80bbe684f",
            "outputs": {
                "gdpr_input_bucket": {
                    "value": mock_input_bucket_name,
                    "type": "string",
                },
                "gdpr_processed_bucket": {
                    "value": mock_processed_bucket_name,
                    "type": "string",
                },
                "gdpr_invocation_bucket": {
                    "value": mock_invocation_bucket_name,
                    "type": "string",
                },
            },
        }

        s3.put_object(
            Bucket=bucket_name, Key=object_key, Body=json.dumps(state_file_content)
        )

        yield bucket_name, object_key, (
            mock_input_bucket_name,
            mock_processed_bucket_name,
            mock_invocation_bucket_name,
        )


def test_get_bucket_names_from_tf_state(mock_aws_s3):
    bucket_name, object_key, expected_buckets = mock_aws_s3

    input_bucket_name, processed_bucket_name, invocation_bucket_name = (
        get_bucket_names_from_tf_state(bucket_name, object_key)
    )

    assert input_bucket_name == expected_buckets[0]
    assert processed_bucket_name == expected_buckets[1]
    assert invocation_bucket_name == expected_buckets[2]


def test_get_bucket_names_from_tf_state_no_such_key():
    bucket_name = "tf-state-gdpr-obfuscator"
    object_key = "non-existent-key"

    result = get_bucket_names_from_tf_state(bucket_name, object_key)
    assert result == (None, None, None)


@pytest.mark.parametrize(
    "bucket_name, s3_file_path, pii_fields, csv_content, expected_output",
    [
        (
            "test-bucket",
            "test.csv",
            ["email"],
            "name,email\nJohn,john@example.com",
            "name,email\nJohn,***\n",
        ),
        (
            "test-bucket",
            "test.csv",
            ["email", "phone"],
            "name,email,phone\nJohn,john@example.com,1234567890",
            "name,email,phone\nJohn,***,***\n",
        ),
        (
            "test-bucket",
            "test.csv",
            [],
            "name,email\nJohn,john@example.com",
            "name,email\nJohn,john@example.com\n",
        ),
        (
            "test-bucket",
            "test.csv",
            ["nonexistent"],
            "name,email\nJohn,john@example.com",
            "name,email\nJohn,john@example.com\n",
        ),
    ],
    ids=[
        "single_pii_field",
        "multiple_pii_fields",
        "no_pii_fields",
        "pii_field_not_in_csv",
    ],
)
@patch("src.utils.processing2.s3")
@patch("src.utils.processing2.logger")
def test_obfuscate_pii_happy_and_edge_cases(
    mock_logger,
    mock_s3,
    bucket_name,
    s3_file_path,
    pii_fields,
    csv_content,
    expected_output,
):
    mock_s3.get_object.return_value = {"Body": BytesIO(csv_content.encode("utf-8"))}

    result = obfuscate_pii(bucket_name, s3_file_path, pii_fields)

    assert result.decode("utf-8") == expected_output


@pytest.mark.parametrize(
    "bucket_name, s3_file_path, pii_fields, exception, log_message",
    [
        (
            "test-bucket",
            "test.csv",
            ["email"],
            Exception("S3 error"),
            "Failed to process file: S3 error",
        ),
        (
            "test-bucket",
            "test.csv",
            ["email"],
            pd.errors.EmptyDataError("No columns to parse from file"),
            "Failed to process file: No columns to parse from file",
        ),
    ],
    ids=["s3_exception", "invalid_csv_format"],
)
@patch("src.utils.processing2.s3")
@patch("src.utils.processing2.logger")
def test_obfuscate_pii_error_cases(
    mock_logger, mock_s3, bucket_name, s3_file_path, pii_fields, exception, log_message
):
    mock_s3.get_object.side_effect = exception

    result = obfuscate_pii(bucket_name, s3_file_path, pii_fields)

    assert result is None
    mock_logger.error.assert_called_with(log_message)


@pytest.mark.parametrize(
    "bucket_name, mock_response, expected_key, test_id",
    [
        (
            "test-bucket",
            {"Contents": [{"Key": "data.json"}]},
            "data.json",
            "single_json_key",
        ),
        (
            "test-bucket",
            {
                "Contents": [
                    {"Key": "data.txt"},
                    {"Key": "data.json"},
                    {"Key": "image.png"},
                ]
            },
            "data.json",
            "multiple_keys_one_json",
        ),
        ("test-bucket", {}, None, "no_keys"),
        (
            "test-bucket",
            {"Contents": [{"Key": "first.json"}, {"Key": "second.json"}]},
            "first.json",
            "multiple_json_keys",
        ),
        (
            "test-bucket",
            {"Contents": [{"Key": "data.txt"}, {"Key": "image.png"}]},
            None,
            "no_json_key",
        ),
        ("test-bucket", {"Error": "No contents"}, None, "no_contents_key"),
    ],
    ids=[
        "single_json_key",
        "multiple_keys_one_json",
        "no_keys",
        "multiple_json_keys",
        "no_json_key",
        "no_contents_key",
    ],
)
@patch("src.utils.processing2.s3.list_objects_v2")
@patch("src.utils.processing2.logger")
def test_get_keys_from_bucket(
    mock_logger, mock_list_objects, bucket_name, mock_response, expected_key, test_id
):
    mock_list_objects.return_value = mock_response

    result = get_keys_from_bucket(bucket_name)

    assert result == expected_key
    if expected_key:
        mock_logger.info.assert_any_call(f"Found key: {expected_key}")
    mock_logger.info.assert_any_call(f"JSON key found: {expected_key}")


@pytest.mark.parametrize(
    "bucket_name, list_objects_response, expected_log",
    [
        (
            "test-bucket",
            {"Contents": [{"Key": "file1"}, {"Key": "file2"}]},
            "All objects deleted from bucket: test-bucket",
        ),
        ("empty-bucket", {}, "No objects found in bucket: empty-bucket"),
    ],
    ids=["bucket_with_objects", "empty_bucket"],
)
def test_empty_bucket_happy_path(
    bucket_name, list_objects_response, expected_log, caplog
):
    with patch("src.utils.processing2.s3") as mock_s3:
        mock_s3.list_objects_v2.return_value = list_objects_response

        with caplog.at_level(logging.INFO):
            empty_bucket(bucket_name)

        if "Contents" in list_objects_response:
            assert mock_s3.delete_object.call_count == len(
                list_objects_response["Contents"]
            )
        else:
            assert mock_s3.delete_object.call_count == 0
        assert expected_log in caplog.text


@pytest.mark.parametrize(
    "bucket_name, exception, expected_log",
    [
        (
            "nonexistent-bucket",
            ClientError({"Error": {"Code": "NoSuchBucket"}}, "ListObjectsV2"),
            "Failed to delete objects from bucket: An error occurred (NoSuchBucket)",
        ),
        (
            "access-denied-bucket",
            ClientError({"Error": {"Code": "AccessDenied"}}, "ListObjectsV2"),
            "Failed to delete objects from bucket: An error occurred (AccessDenied)",
        ),
    ],
    ids=["nonexistent_bucket", "access_denied"],
)
def test_empty_bucket_error_cases(bucket_name, exception, expected_log, caplog):
    with patch("src.utils.processing2.s3") as mock_s3:
        mock_s3.list_objects_v2.side_effect = exception

        with caplog.at_level(logging.ERROR):
            empty_bucket(bucket_name)

        assert expected_log in caplog.text


@mock.patch("src.utils.processing2.get_bucket_names_from_tf_state")
@mock.patch("src.utils.processing2.get_keys_from_bucket")
@mock.patch("src.utils.processing2.s3.get_object")
@mock.patch("src.utils.processing2.s3.put_object")
@mock.patch("src.utils.processing2.obfuscate_pii")
@mock.patch("src.utils.processing2.empty_bucket")
def test_handler_success(
    mock_empty_bucket,
    mock_obfuscate_pii,
    mock_put_object,
    mock_s3_get_object,
    mock_get_keys,
    mock_get_bucket_names,
):
    event = {}
    context = {}

    mock_get_bucket_names.return_value = (
        "input-bucket",
        "processed-bucket",
        "invocation-bucket",
    )

    mock_get_keys.return_value = "data.json"

    mock_s3_get_object.return_value = {
        "Body": mock.Mock(
            read=mock.Mock(
                return_value=json.dumps(
                    {
                        "bucket_name": "input-bucket",
                        "s3_file_path": "data.csv",
                        "pii_fields": ["name"],
                    }
                ).encode("utf-8")
            )
        )
    }

    mock_obfuscate_pii.return_value = b"obfuscated_data"

    response = handler(event, context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == "Processing completed successfully."
    mock_put_object.assert_called_once_with(
        Bucket="processed-bucket", Key="processed/data.csv", Body=b"obfuscated_data"
    )
    mock_empty_bucket.assert_any_call("input-bucket")
    mock_empty_bucket.assert_any_call("invocation-bucket")


@mock.patch("src.utils.processing2.get_bucket_names_from_tf_state")
@mock.patch("src.utils.processing2.get_keys_from_bucket")
@mock.patch("src.utils.processing2.s3.get_object")
def test_handler_500_no_json_file_found(
    mock_s3_get_object, mock_get_keys, mock_get_bucket_names
):
    event = {}
    context = {}

    mock_get_bucket_names.return_value = (
        "input-bucket",
        "processed-bucket",
        "invocation-bucket",
    )

    mock_get_keys.return_value = None

    response = handler(event, context)

    assert response["statusCode"] == 500
    assert (
        json.loads(response["body"])
        == "Error retrieving JSON file from invocation bucket."
    )


@mock.patch("src.utils.processing2.get_bucket_names_from_tf_state")
@mock.patch("src.utils.processing2.get_keys_from_bucket")
@mock.patch("src.utils.processing2.s3.get_object")
def test_handler_500_error_reading_json_file(
    mock_s3_get_object, mock_get_keys, mock_get_bucket_names
):
    event = {}
    context = {}

    mock_get_bucket_names.return_value = (
        "input-bucket",
        "processed-bucket",
        "invocation-bucket",
    )

    mock_get_keys.return_value = "data.json"

    mock_s3_get_object.side_effect = Exception("Some error occurred")

    response = handler(event, context)

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == "Error reading JSON file."


@mock.patch("src.utils.processing2.get_bucket_names_from_tf_state")
@mock.patch("src.utils.processing2.get_keys_from_bucket")
@mock.patch("src.utils.processing2.s3.get_object")
@mock.patch("src.utils.processing2.obfuscate_pii")
def test_handler_500_error_processing_json_content(
    mock_obfuscate_pii, mock_s3_get_object, mock_get_keys, mock_get_bucket_names
):
    event = {}
    context = {}

    mock_get_bucket_names.return_value = (
        "input-bucket",
        "processed-bucket",
        "invocation-bucket",
    )

    mock_get_keys.return_value = "data.json"

    mock_s3_get_object.return_value = {
        "Body": mock.Mock(
            read=mock.Mock(
                return_value=json.dumps(
                    {
                        "bucket_name": "input-bucket",
                        "s3_file_path": "data.csv",
                        "pii_fields": ["name"],
                    }
                ).encode("utf-8")
            )
        )
    }

    mock_obfuscate_pii.side_effect = Exception("Error in obfuscation")

    response = handler(event, context)

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == "Error processing JSON content."
