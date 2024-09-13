import pytest
from unittest.mock import patch
import os
from datetime import datetime
from src.utils.upload import generate_s3_file_path  

def test_generate_s3_file_path():
    '''This test will validate that generate_s3_file_path behaves 
    correctly by generating the expected S3 file path 
    based on a mocked timestamp.'''
    local_file_path = 'src/data/dummy_data.csv'
    
    
    with patch('src.utils.upload.datetime') as mock_datetime:
        fixed_timestamp = datetime(2024, 9, 12, 15, 30, 45)
        mock_datetime.now.return_value = fixed_timestamp
        
        expected_timestamp = fixed_timestamp.strftime('%Y_%d_%m_%H:%M:%S')
        expected_file_name = os.path.basename(local_file_path)
        expected_s3_file_path = f"{expected_timestamp}_{expected_file_name}"
        
        
        result = generate_s3_file_path(local_file_path)
        
        
        assert result == expected_s3_file_path