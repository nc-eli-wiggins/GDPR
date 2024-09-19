import json
import boto3
import pandas as pd
import io
from datetime import datetime
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


s3 = boto3.client('s3')
def get_file_info_from_json(json_file_path):
    """
    Reads the local JSON file and retrieves the bucket name and S3 file path.

    Parameters:
    json_file_path (str): Path to the JSON file containing S3 file info.

    Returns:
    dict: A dictionary with bucket name and S3 file path.
    """
    try:
        with open(json_file_path, 'r') as file:
            file_info = json.load(file)
        if 'bucket_name' in file_info and 's3_file_path' in file_info:
            return file_info
        else:
            print("JSON file missing required keys")
            return None
    except Exception as e:
        print(f"Failed to read JSON file: {e}")
        return None

def obfuscate_pii(file_info):
    """
    Obfuscates specified PII fields in a CSV file.

    Parameters:
    file_info (dict): A dictionary containing:
        - "s3_file_path": S3 file path to the CSV file (relative to bucket)
        - "bucket_name": Name of the S3 bucket
        - "pii_fields": List of PII fields to obfuscate

    Returns:
    bytes: A bytestream of the obfuscated CSV content
    """
    if not file_info:
        print("No file info provided")
        return None
    
    s3_file_path = file_info.get("s3_file_path")
    bucket_name = file_info.get("bucket_name")
    pii_fields = file_info.get("pii_fields", [])

    if not s3_file_path or not bucket_name or not pii_fields:
        print("Missing required information in file_info")
        return None
    

    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_file_path)
        csv_data = response['Body'].read()
    except Exception as e:
        print(f"Failed to download file from S3: {e}")
        return None
    
    df = pd.read_csv(io.BytesIO(csv_data))
    
    for pii_field in pii_fields:
        if pii_field in df.columns:
            df[pii_field] = '***'
    
    obfuscated_csv = df.to_csv(index=False)
    return obfuscated_csv.encode('utf-8')

def upload_obfuscated_file_to_s3(obfuscated_file_stream, processed_bucket_name):
    """
    Uploads the obfuscated CSV file to the processed S3 bucket with a specific prefix.

    Parameters:
    obfuscated_file_stream (bytes): The obfuscated CSV content as bytes.
    processed_bucket_name (str): The name of the S3 bucket where the file will be uploaded.

    Returns:
    str: The S3 file path if the upload is successful.
        Returns None if the upload fails.
    """

    s3_file_path = f"gdpr-processed-{datetime.now().strftime('%Y_%d_%m_%H:%M:%S')}.csv"
    
    try:
        s3.put_object(Bucket=processed_bucket_name, Key=s3_file_path, Body=obfuscated_file_stream)
        print(f"Obfuscated file uploaded to {processed_bucket_name}/{s3_file_path}")
        return s3_file_path
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def read_processed_bucket_name():
    """
    Retrieves the name of the processed S3 bucket from the Terraform state file in S3.

    Returns:
    str: The name of the processed S3 bucket if the operation is successful.
        If the operation fails, returns None.
    """
    bucket_name = "tf-state-gdpr-obfuscator"
    object_key = "tf-state"

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        processed_bucket_name = data["outputs"]["gdpr_processed_bucket"]["value"]
        return processed_bucket_name
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

if __name__ == '__main__':
    json_file_path = 'output/s3_files/s3_file_info.json'
    file_info = get_file_info_from_json(json_file_path)
    obfuscated_file_stream = obfuscate_pii(file_info)

    if obfuscated_file_stream:
        processed_bucket_name = read_processed_bucket_name()
        if processed_bucket_name:
            upload_obfuscated_file_to_s3(obfuscated_file_stream, processed_bucket_name)
        else:
            print("Processed bucket name could not be retrieved.")
    else:
        print("Failed to obfuscate PII")
