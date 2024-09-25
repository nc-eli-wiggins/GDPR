import boto3
import json
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime
from src.utils.s3_paths import get_bucket_names_from_tf_state

s3 = boto3.client('s3')

tf_state_bucket = 'tf-state-gdpr-obfuscator'
tf_state_key = 'tf-state'

def generate_s3_file_path(local_file_path):
    """
    Generates a timestamped filename for an S3 object based on the local file's name.

    Parameters:
    local_file_path (str): The path to the local file for which the timestamped filename is being generated.

    Returns:
    str: The timestamped filename in the format 'YYYY_DD_MM_HH:MM:SS_filename'.
    """
    timestamp = datetime.now().strftime('%Y_%d_%m_%H:%M:%S')
    file_name = os.path.basename(local_file_path)
    s3_file_path = f"{timestamp}_{file_name}"
    return s3_file_path

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
        print(f"The file {local_file_path} does not exist")
        return None

    s3_file_path = generate_s3_file_path(local_file_path)

    try:
        s3.upload_file(local_file_path, bucket_name, s3_file_path)
        print(f"File {local_file_path} uploaded to {bucket_name}/{s3_file_path}")
        return s3_file_path
    except FileNotFoundError:
        print(f"The file {local_file_path} was not found")
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None



if __name__ == '__main__':
    local_file_path = 'src/data/dummy_data_large.csv'
    input_bucket_name, processed_bucket_name, invocation_bucket_name = get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)

    if input_bucket_name:
        s3_file_path = upload_file_to_s3(local_file_path, input_bucket_name)
        if s3_file_path:
            export_dir = 'output/s3_files'
            print(f"File successfully uploaded as {s3_file_path}")
        else:
            print("Failed to upload file.")
    else:
        print("Input bucket name could not be retrieved, try running terraform apply 1st to create bucket.")
