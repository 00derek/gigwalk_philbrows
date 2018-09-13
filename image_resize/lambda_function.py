import json
from PIL import Image
import boto3
import os

s3 = boto3.resource('s3')
s3_bucket_lookup = {"multitenant": "gigwalk-multitenant-api-server", "beta": "gigwalk-beta-api-server", "stage": "gigwalk-stage-app-api-server", "jp_prod": "gigwalk-japan-api-server", "jp_stage": "gigwalk-jp-staging-api-server", "jp_partner": "gigwalk-partner-jp-api-server", "csmk_partner": "gigwalk-uu-partner", "csmk_partner_dev": "gigwalk-partner-dev-api-server", "csmk_prod": "gigwalk-uu"}
s3_bucket_inverse_lookup = {v: k for k, v in s3_bucket_lookup.items()}


def lambda_handler(event, context):
    s3bucket = None
    s3_file_key = None
    env_key = None

    print(event)
    # there are 2 types of events
    # s3 events, image created on s3
    if event.get('Records'):
        s3bucket_name = event['Records'][0]['s3']['bucket']['name']
        s3_file_key = event['Records'][0]['s3']['object']['key']
        env_key = s3_bucket_inverse_lookup.get(s3bucket_name)
    # API event, creating the thumbnails on the fly
    elif event.get('queryStringParameters') and event.get('queryStringParameters').get('key') :
        env_key, s3_file_key = event['queryStringParameters']['key'].split('/', 1)    
        s3bucket_name = s3_bucket_lookup.get(env_key)

    print(s3bucket_name, s3_file_key, env_key)

    # any of the required info is missing, failing with 400 response code
    if not all((s3bucket_name, s3_file_key, env_key)):
        return {"statusCode": 400}
    bucket = s3.Bucket(s3bucket_name)
    try:
        _resize_image(bucket, env_key, s3_file_key)
    except Exception as e:
        return {"statusCode": 400}

    return {
        "statusCode": 302,
        "headers": {"Location": 'http://gigwalk-thumbnails.s3-website-us-east-1.amazonaws.com/'+env_key+'/'+s3_file_key}
        # "headers": {"Location": 'https://google.com'}
    }


def _resize_image(orig_bucket, env_key, s3_file_key):
    print("resize image:", env_key, s3_file_key)
    tmp_file = '/tmp/tmp.jpg'
    try:
        orig_bucket.download_file(s3_file_key, tmp_file)
        img = Image.open(tmp_file)
        img.thumbnail([300, 300], Image.ANTIALIAS)
        img.save(tmp_file)
        data = open(tmp_file, 'rb')
        thumbnail_bucket = s3.Bucket('gigwalk-thumbnails')
        s3_key = env_key+'/'+s3_file_key
        thumbnail_bucket.put_object(Key=s3_key, Body=data, ACL='public-read')
    except Exception as e:
        print(e)
        raise e
