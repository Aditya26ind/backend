import boto3
from fastapi import UploadFile
import os

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1')

BUCKET_NAME = os.getenv('BUCKET_NAME')

async def upload_to_s3(file, filename):
    try:
        print(f"Uploading {filename} to S3...")
        s3.upload_fileobj(file, BUCKET_NAME, filename)
        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        print(f"File uploaded successfully: {file_url}")
        return file_url
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        raise