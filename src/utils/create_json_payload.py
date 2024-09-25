import json
import os
import boto3
from src.utils.s3_paths import get_bucket_names_from_tf_state  

pii_fields = ['Name', 'Email Address', 'Sex']

def create_json_file(bucket_name, s3_file_path, pii_fields):
    """Create JSON structure and save it locally."""
    json_data = {
        "bucket_name": bucket_name,
        "s3_file_path": s3_file_path,
        "pii_fields": pii_fields
    }
    
    json_string = json.dumps(json_data)
    
    local_json_path = f"src/data/{os.path.basename(s3_file_path).replace('.csv', '.json')}"
    
    try:
        os.makedirs(os.path.dirname(local_json_path), exist_ok=True)  
        with open(local_json_path, 'w') as json_file:
            json_file.write(json_string)
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        return None
    
    return local_json_path  

def upload_json_to_s3(local_json_path, bucket_name):
    """Upload JSON file to S3 bucket."""
    s3 = boto3.client('s3')
    
    try:
        file_name = os.path.basename(local_json_path)
        
        s3.upload_file(local_json_path, bucket_name, file_name)
        print(f"Successfully uploaded {file_name} to {bucket_name}")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")

def get_invocation_bucket_from_tf_state(tf_state_bucket, tf_state_key):
    """Retrieve input bucket info from Terraform state."""
    input_bucket_name, processed_bucket_name, invocation_bucket_name = get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)
    return input_bucket_name, invocation_bucket_name

def get_s3_file_name(bucket_name, prefix=''):
    """Retrieve the first file name from the specified S3 bucket."""
    s3 = boto3.client('s3')
    
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            file_name = response['Contents'][0]['Key']
            return file_name
        else:
            print("No files found in the specified bucket.")
            return None
    except Exception as e:
        print(f"Error retrieving file name: {e}")
        return None

if __name__ == "__main__":
    tf_state_bucket = 'tf-state-gdpr-obfuscator'  
    tf_state_key = 'tf-state'                      

    input_bucket_name, processed_bucket_name, invocation_bucket_name = get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)
    
    if invocation_bucket_name:
        s3_file_path = get_s3_file_name(input_bucket_name)  
        
        if s3_file_path:
            local_json_path = create_json_file(input_bucket_name, s3_file_path, pii_fields)
            if local_json_path:
                upload_json_to_s3(local_json_path, invocation_bucket_name)  
            else:
                print("Failed to create JSON file.")
        else:
            print("Failed to retrieve S3 file name. Make sure you've uploaded the file first.")
    else:
        print("Failed to retrieve invocation bucket name. Make sure the buckets have been created.")
