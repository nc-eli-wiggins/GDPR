import boto3
import pandas as pd
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import json
import os
import io


s3 = boto3.client('s3')

def load_s3_file_info(export_dir):
    """
    This function loads the S3 bucket name and file path from a JSON file.

    Parameters:
    export_dir (str): The directory where the JSON file is located.

    Returns:
    tuple: A tuple containing the S3 bucket name and file path. If the file does not exist, returns (None, None).
    """
    file_path = os.path.join(export_dir, 's3_file_info.json')
    if not os.path.exists(file_path):
        print(f"The file {file_path} does not exist")
        return None, None

    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        return data.get("bucket_name"), data.get("s3_file_path")
def convert_df_to_bytestream(df):
    """
    Converts a pandas DataFrame to a bytestream in CSV format.

    Parameters:
    df (pandas.DataFrame): The DataFrame to be converted.

    Returns:
    io.BytesIO: A bytestream containing the CSV representation of the DataFrame.
    """
    bytestream = io.BytesIO()
    df.to_csv(bytestream, index=False)
    bytestream.seek(0)  
    return bytestream
def read_csv_from_s3(bucket_name, s3_file_path):
    """
    This function reads a CSV file from an S3 bucket and converts it into a bytestream.

    Parameters:
    bucket_name (str): The name of the S3 bucket where the file is located.
    s3_file_path (str): The path to the file within the S3 bucket.

    Returns:
    io.BytesIO: A bytestream containing the CSV representation of the file. If an error occurs, returns None.
    """
    try:
        # Get the object from the S3 bucket
        response = s3.get_object(Bucket=bucket_name, Key=s3_file_path)

        # Read the CSV data from the S3 object
        df = pd.read_csv(response['Body'])

        # Convert the DataFrame to a bytestream
        bytestream = convert_df_to_bytestream(df)

        return bytestream
    except s3.exceptions.NoSuchKey:
        print(f"The file {s3_file_path} does not exist in the bucket {bucket_name}")
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except ClientError as e:
        print(f"An S3 client error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

if __name__ == '__main__':
    
    export_dir = 'output/s3_files'
    
    
    bucket_name, s3_file_path = load_s3_file_info(export_dir)

    if bucket_name and s3_file_path:
        
        bytestream = read_csv_from_s3(bucket_name, s3_file_path)

        
        if bytestream is not None:
            
            df = pd.read_csv(bytestream)
            print('***************data frame***************')
            print(df)
            print('***************bytestream***************') 
            print (bytestream.getvalue().decode('utf-8'))
        else:
            print("Failed to load bytestream, try uploading some data 1st.")
    else:
        print("Failed to retrieve bucket name or S3 file path. Try uploading data first using upload.py")



