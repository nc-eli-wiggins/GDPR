import json
import boto3

s3 = boto3.client('s3')


def get_bucket_names_from_tf_state(bucket_name, object_key):
    """ Retrieves bucket names from the Terraform state file. """
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        input_bucket_name = data["outputs"]["gdpr_input_bucket"]["value"]
        processed_bucket_name = data["outputs"]["gdpr_processed_bucket"]["value"]
        invocation_bucket_name = data["outputs"]["gdpr_invocation_bucket"]["value"]
        return input_bucket_name, processed_bucket_name, invocation_bucket_name
    except Exception as e:
        print(f"Failed to retrieve bucket names: {e}")
        return None, None, None
    
    
    
    