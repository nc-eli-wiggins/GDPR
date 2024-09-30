import json
import os
import boto3
from src.utils.processing2 import tf_state_bucket, tf_state_key

pii_fields = ["Name", "Email Address", "Sex", "DOB"]

s3 = boto3.client("s3")


def get_bucket_names_from_tf_state(bucket_name, object_key):
    """Retrieves bucket names from the Terraform state file."""
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


def create_json_file(bucket_name, s3_file_path, pii_fields):
    """Creates JSON structure and saves it locally."""
    json_data = {
        "bucket_name": bucket_name,
        "s3_file_path": s3_file_path,
        "pii_fields": pii_fields,
    }

    local_json_path = (
        f"src/data/{os.path.basename(s3_file_path).replace('.csv', '.json')}"
    )

    os.makedirs(os.path.dirname(local_json_path), exist_ok=True)

    try:
        with open(local_json_path, "w") as json_file:
            json.dump(json_data, json_file)
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        return None

    return local_json_path


def upload_json_to_s3(local_json_path, bucket_name):
    """Uploads JSON file to S3 bucket."""
    try:
        file_name = os.path.basename(local_json_path)
        s3.upload_file(local_json_path, bucket_name, file_name)
        print(f"Successfully uploaded {file_name} to {bucket_name}")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")


def get_s3_file_name(bucket_name, prefix=""):
    """Retrieves the first file name from the specified S3 bucket."""
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            return response["Contents"][0]["Key"]
        print("No files found in the specified bucket.")
        return None
    except Exception as e:
        print(f"Error retrieving file name: {e}")
        return None


def main():
    input_bucket_name, processed_bucket_name, invocation_bucket_name = (
        get_bucket_names_from_tf_state(tf_state_bucket, tf_state_key)
    )

    if invocation_bucket_name:
        s3_file_path = get_s3_file_name(input_bucket_name)

        if s3_file_path:
            local_json_path = create_json_file(
                input_bucket_name, s3_file_path, pii_fields
            )
            if local_json_path:
                upload_json_to_s3(local_json_path, invocation_bucket_name)
            else:
                print("Failed to create JSON file.")
        else:
            print(
                "Failed to retrieve S3 file name. Make sure you've uploaded the file first."
            )
    else:
        print(
            "Failed to retrieve invocation bucket name. Make sure the buckets have been created."
        )


if __name__ == "__main__":
    main()
