import json
import boto3
import pandas as pd
import io

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')




def get_bucket_names_from_tf_state(bucket_name, object_key):
    """ Retrieves bucket names from the Terraform state file. """
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        input_bucket_name = data["outputs"]["gdpr_input_bucket"]["value"]
        processed_bucket_name = data["outputs"]["gdpr_processed_bucket"]["value"]
        
        return input_bucket_name, processed_bucket_name
    except Exception as e:
        print(f"Failed to retrieve bucket names: {e}")
        return None, None
    
    
    

def obfuscate_pii(bucket_name, s3_file_path, pii_fields):
    """ Obfuscates specified PII fields in a CSV file. """
    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_file_path)
        csv_data = response['Body'].read()
        df = pd.read_csv(io.BytesIO(csv_data))
        
        for pii_field in pii_fields:
            if pii_field in df.columns:
                df[pii_field] = '***'  

        obfuscated_csv = df.to_csv(index=False)
        return obfuscated_csv.encode('utf-8')
    except Exception as e:
        print(f"Failed to process file: {e}")
        return None

def handler(event, context):
    """ Main Lambda handler to obfuscate PII fields. """
    tf_state_bucket = 'tf-state-gdpr-obfuscator'
    tf_state_key = 'tf-state'

    input_bucket_name, processed_bucket_name = get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)

    if not input_bucket_name or not processed_bucket_name:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to retrieve bucket names from Terraform state.'})
        }

    bucket_name = event.get('bucket_name')
    s3_file_path = event.get('s3_file_path')
    pii_fields = event.get('pii_fields', [])

    if not bucket_name or not s3_file_path or not pii_fields:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing required parameters.'})
        }

    obfuscated_file_stream = obfuscate_pii(bucket_name, s3_file_path, pii_fields)

    if obfuscated_file_stream:
        processed_file_path = f"gdpr-processed-{s3_file_path.split('/')[-1]}"
        
        s3.put_object(Bucket=processed_bucket_name, Key=processed_file_path, Body=obfuscated_file_stream)

        empty_bucket(bucket_name)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'PII fields obfuscated and file uploaded successfully.'})
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to obfuscate PII fields.'})
        }



def empty_bucket(bucket_name):
    """Deletes all objects in the specified S3 bucket."""
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            print(f"All objects deleted from bucket: {bucket_name}")
        else:
            print(f"No objects found in bucket: {bucket_name}")
    
    except Exception as e:
        print(f"Failed to delete objects from bucket: {e}")
