import json
from io import BytesIO
from unittest import mock
from src.utils.processing import get_file_info_from_json, obfuscate_pii   

def test_get_file_info_from_json_valid():
    """
    This function tests the get_file_info_from_json function with a valid JSON file.

    Parameters:
    None

    Returns:
    None

    - Mocks the open function to simulate a valid JSON file.
    - Calls the get_file_info_from_json function with a dummy file path.
    """

    mock_json_content = {
        "bucket_name": "test-bucket",
        "s3_file_path": "test/path/to/file.csv"
    }

    with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(mock_json_content))):
        file_info = get_file_info_from_json("dummy_path.json")
        assert file_info == mock_json_content

def test_get_file_info_from_json_missing_keys():
    """
    This function tests the get_file_info_from_json function when the JSON file is missing required keys.

    Parameters:
    None

    Returns:
    None

    - Mocks the open function to simulate a JSON file with missing keys.
    - Calls the get_file_info_from_json function with a dummy file path.
    """
    mock_json_content = {
        "some_other_key": "value"
    }

    with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(mock_json_content))):
        file_info = get_file_info_from_json("dummy_path.json")
        assert file_info is None

def test_get_file_info_from_json_invalid_json():
    """
    This function tests the get_file_info_from_json function when the JSON file is invalid.

    Parameters:
    None

    Returns:
    None

    - Mocks the open function to simulate an invalid JSON file.
    - Calls the get_file_info_from_json function with a dummy file path.

    """
    with mock.patch("builtins.open", mock.mock_open(read_data="invalid json")):
        file_info = get_file_info_from_json("dummy_path.json")
        assert file_info is None

def test_get_file_info_from_json_file_not_found():
    """
    This function tests the get_file_info_from_json function when the specified JSON file is not found.

    Parameters:
    None

    Returns:
    None

    - Mocks the open function to simulate a FileNotFoundError.
    - Calls the get_file_info_from_json function with a dummy file path.
    """
    with mock.patch("builtins.open", side_effect=FileNotFoundError):
        file_info = get_file_info_from_json("dummy_path.json")
        assert file_info is None, "Should return None if file is not found"

def test_get_file_info_from_json_io_error():
    """
    This function tests the get_file_info_from_json function when an IOError occurs.

    Parameters:
    None

    Returns:
    None

    This function mocks the open function to simulate an IOError. It then calls the
    get_file_info_from_json function with a dummy file path. The function asserts that
    """
    with mock.patch("builtins.open", side_effect=IOError):
        file_info = get_file_info_from_json("dummy_path.json")
        assert file_info is None

def test_obfuscate_pii_valid_file():
    """
    This function tests the obfuscate_pii function with a valid file containing PII data.

    Parameters:
    file_info (dict): A dictionary containing the following keys:
        - "bucket_name" (str): The name of the S3 bucket where the file is located.
        - "s3_file_path" (str): The path to the file in the S3 bucket.
        - "pii_fields" (list of str): A list of column names containing PII data to be removed.

    Returns:
    None

    This function creates a mock file information dictionary, a sample CSV content as bytes,
    and a mock S3 client. It then patches the boto3.client function to return the mock S3 client.
    The function calls the obfuscate_pii function with the mock file information, and checks
    the content of the obfuscated CSV against an expected output.
    """
    file_info = {
        "bucket_name": "test-bucket",
        "s3_file_path": "test/path/to/file.csv",
        "pii_fields": ["name", "email"]
    }

    csv_content = "name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,25"

    mock_s3_client = mock.Mock()
    mock_s3_client.get_object.return_value = {"Body": BytesIO(csv_content.encode())}

    with mock.patch("boto3.client", return_value=mock_s3_client):
        obfuscated_file_stream = obfuscate_pii(file_info)
        obfuscated_csv = obfuscated_file_stream.decode('utf-8')

    expected_output = "name,email,age\n***,***,30\n***,***,25\n"
    assert obfuscated_csv == expected_output

def test_obfuscate_pii_missing_fields():
    """
    This function tests the obfuscate_pii function when the required fields are missing in the file_info dictionary.

    Parameters:
    file_info (dict): A dictionary containing the following keys:
        - "bucket_name" (str): The name of the S3 bucket where the file is located.
        - "s3_file_path" (str): The path to the file in the S3 bucket.
        - "pii_fields" (list of str): A list of column names containing PII data to be removed.

    Returns:
    None
        If the required fields are missing in the file_info dictionary, the function returns None.
    """
    file_info = {
        "bucket_name": "test-bucket",
        "s3_file_path": "test/path/to/file.csv"
    }

    result = obfuscate_pii(file_info)
    assert result is None

def test_obfuscate_pii_file_not_found():
    """
    This function tests the obfuscate_pii function when the specified file is not found in the S3 bucket.

    Parameters:
    file_info (dict): A dictionary containing the following keys:
        - "bucket_name" (str): The name of the S3 bucket where the file is located.
        - "s3_file_path" (str): The path to the file in the S3 bucket.
        - "pii_fields" (list of str): A list of column names containing PII data to be removed.

    Returns:
    None: If the specified file is not found in the S3 bucket, the function returns None.

    This function creates a mock file information dictionary, configures a mock S3 client to raise an exception
    when the file is not found, and then calls the obfuscate_pii function with the mock file information.
    """
    file_info = {
        "bucket_name": "test-bucket",
        "s3_file_path": "test/path/to/file.csv",
        "pii_fields": ["name", "email"]
    }

    mock_s3_client = mock.Mock()
    mock_s3_client.get_object.side_effect = Exception("File not found")

    with mock.patch("boto3.client", return_value=mock_s3_client):
        result = obfuscate_pii(file_info)

    assert result is None, "Should return None when the file is not found"



