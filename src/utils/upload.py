import boto3
import json
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime

s3 = boto3.client('s3')

def read_input_bucket_name():
    """
    Retrieves the name of the input S3 bucket from the Terraform state file in S3.

    Returns:
    str: The name of the input S3 bucket if the operation is successful.
        If the operation fails, returns None.
    """
    bucket_name = "tf-state-gdpr-obfuscator"
    object_key = "tf-state"

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        input_bucket_name = data["outputs"]["gdpr_input_bucket"]["value"]
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
############################################################

            #for the test lambda function
def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }
############################################################

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

def export_to_json(bucket_name, s3_file_path, export_dir):
    """
    Exports the S3 bucket name and file path to a JSON file.

    This function creates a directory if it does not exist, then writes the S3 bucket name and file path
    to a JSON file named 's3_file_info.json' in the specified export directory.

    Parameters:
    bucket_name (str): The name of the S3 bucket where the file was uploaded.
    s3_file_path (str): The path of the file in the S3 bucket.
    export_dir (str): The directory where the JSON file will be created.

    Returns:
    None
    """
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    export_file = os.path.join(export_dir, 's3_file_info.json')
    pii_fields = ["Name", "Email Address"]
    data = {
        "bucket_name": bucket_name,
        "s3_file_path": s3_file_path,
        "pii_fields": pii_fields
    }

    with open(export_file, 'w') as json_file:
        json.dump(data, json_file)

if __name__ == '__main__':
    local_file_path = 'src/data/dummy_data_20_entries.csv'
    input_bucket_name = read_input_bucket_name()


    if input_bucket_name:
        s3_file_path = upload_file_to_s3(local_file_path, input_bucket_name)
        if s3_file_path:
            export_dir = 'output/s3_files'
            export_to_json(input_bucket_name, s3_file_path, export_dir)
            print(f"File successfully uploaded as {s3_file_path} and details exported to JSON.")
        else:
            print("Failed to upload file.")
    else:
        print("Input bucket name could not be retrieved, try running terraform apply 1st to create bucket.")
