import boto3
import json
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime

s3 = boto3.client('s3')

def read_bucket_name():
    """
    This function reads the bucket name from a specified AWS S3 object.
    The object is expected to contain a JSON file with a 'outputs' section,
    and within that section, a 'gdpr_bucket' key with the bucket name as its value.

    Returns:
    str: The name of the GDPR bucket as read from the S3 object.
    """
    bucket_name = "tf-state-gdpr-obfuscator"
    object_key = "tf-state"

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        input_bucket_name = data["outputs"]["gdpr_bucket"]["value"]
        return input_bucket_name
    except s3.exceptions.NoSuchKey:
        print(f"The object {object_key} does not exist in the bucket {bucket_name}")
    except json.JSONDecodeError:
        print("Error decoding JSON from S3 object")
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def generate_s3_file_path(local_file_path):
    """
    Generates a timestamped file name for the S3 object.

    Parameters:
    local_file_path (str): The path to the local file for which a timestamped name is to be generated.

    Returns:
    str: A string representing the timestamped file name in the format 'YYYY_DD_MM_HH:MM:SS_filename'.
    """
    timestamp = datetime.now().strftime('%Y_%d_%m_%H:%M:%S')
    file_name = os.path.basename(local_file_path)
    s3_file_path = f"{timestamp}_{file_name}"
    return s3_file_path

def upload_file_to_s3(local_file_path, bucket_name):
    """
    Uploads a file to S3 with a timestamped filename.

    Parameters:
    local_file_path (str): The path to the local file that needs to be uploaded.
    bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    str: The timestamped filename of the uploaded file in the format 'YYYY_DD_MM_HH:MM:SS_filename'.
         If the file upload fails, returns None.
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

def export_to_json(bucket_name, s3_file_path, export_dir):
    """
    Exports the bucket name and s3_file_path to a JSON file.
    """
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    export_file = os.path.join(export_dir, 's3_file_info.json')
    data = {
        "bucket_name": bucket_name,
        "s3_file_path": s3_file_path
    }

    with open(export_file, 'w') as json_file:
        json.dump(data, json_file)


if __name__ == '__main__':
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    bucket_name = read_bucket_name()

    if bucket_name:
        s3_file_path = upload_file_to_s3(local_file_path, bucket_name)
        if s3_file_path:
            export_dir = 'output/s3_files'
            export_to_json(bucket_name, s3_file_path, export_dir)
            print(f"File successfully uploaded as {s3_file_path} and details exported to JSON.")
        else:
            print("Failed to upload file.")
    else:
        print("Bucket name could not be retrieved, try running terraform apply 1st to create bucket.")
