import boto3
import os
import json
from datetime import datetime

from src.utils.processing2 import tf_state_bucket, tf_state_key
from src.data.create_data import data_file_path

s3 = boto3.client("s3")


def get_bucket_names_from_tf_state(bucket_name, object_key):
    """
    Retrieves the names of the input, processed, and invocation buckets from a Terraform state file.

    Parameters:
    bucket_name (str): The name of the S3 bucket where the Terraform state file is located.
    object_key (str): The key of the Terraform state file within the specified bucket.

    Returns:
    tuple: A tuple containing the names of the input, processed, and invocation buckets.
           If an error occurs during retrieval, returns (None, None, None).
    """    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response["Body"].read().decode("utf-8"))
        input_bucket_name = data["outputs"]["gdpr_input_bucket"]["value"]
        processed_bucket_name = data["outputs"]["gdpr_processed_bucket"]["value"]
        invocation_bucket_name = data["outputs"]["gdpr_invocation_bucket"]["value"]
        return input_bucket_name, processed_bucket_name, invocation_bucket_name
    except Exception as e:
        print(f"Failed to retrieve bucket names: {e}")
        return None, None, None


def generate_s3_file_path(local_file_path):
    """
    Generates a timestamped filename for an S3 object based on the local file's name.

    Parameters:
    local_file_path (str): The path to the local file for which the timestamped filename is being generated.

    Returns:
    str: The timestamped filename in the format 'YYYY_DD_MM_HH:MM:SS_filename'.
    """
    timestamp = datetime.now().strftime("%Y_%d_%m_%H:%M:%S")
    file_name = os.path.basename(local_file_path)
    return f"{timestamp}_{file_name}"


def upload_file_to_s3(local_file_path, bucket_name):
    """
    Uploads a local file to an S3 bucket.

    Parameters:
    local_file_path (str): The path to the local file to be uploaded.
    bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    str: The S3 file path if the upload is successful.
        Returns None if the upload fails or if the local file does not exist.
    """
    if not os.path.isfile(local_file_path):
        print(f"Error: The file {local_file_path} does not exist.")
        return None

    s3_file_path = generate_s3_file_path(local_file_path)

    s3.upload_file(local_file_path, bucket_name, s3_file_path)
    print(f"Success: File {local_file_path} uploaded to {bucket_name}/{s3_file_path}")
    return s3_file_path


local_file_path = data_file_path
input_bucket_name, processed_bucket_name, invocation_bucket_name = (
    get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)
)

if input_bucket_name:
    s3_file_path = upload_file_to_s3(local_file_path, input_bucket_name)
