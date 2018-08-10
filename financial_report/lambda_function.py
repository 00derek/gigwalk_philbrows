import time
import requests
import os
import psycopg2
import boto3
import uuid


EXPECTED = os.environ['expected']  # String expected to be on the page, stored in the expected environment variable, e.g. Amazon
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS').split(',')

def validate(event):
    auth = (EXPECTED ==  event.get('token') and event.get('team_domain') == 'gigwalk' and event.get('user_name') in AUTHORIZED_USERS)
    if not auth:
        raise Exception('Validation failed')
        
def lambda_handler(event, context):
    try:
        validate(event)
        hook_url = event.get('response_url')
        headers = {'user-agent': 'aws_lambda', 'Content-Type': 'application/json;charset=UTF-8'}
        payload = {'text': "Generating report, a link is coming up...."}
        myResponse = requests.post(hook_url, headers=headers, json=payload)
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        cur = conn.cursor()
        outputquery = 'copy ({0}) to stdout with csv header'.format(os.environ.get('QUERY'))
        tmpfile = '/tmp/results.csv'
        with open(tmpfile, 'w') as f:
            cur.copy_expert(outputquery, f)
        print('end of the query')

        payload = {'text': "The two most powerful warriors are patience and time -- Leo Tolstoy"}
        myResponse = requests.post(hook_url, headers=headers, json=payload)
        s3 = boto3.resource('s3')
        data = open(tmpfile, 'rb')
        # note that the report lifecycle is 1 day and defined within the bucket
        s3bucket = os.environ.get('s3bucket')
        bucket = s3.Bucket(s3bucket)
        
        s3key = os.environ.get('s3_folder')+'/'+uuid.uuid4().hex+'.csv'
        print('uploading file {}'.format(s3key))
        bucket.put_object(Key=s3key, Body=data)
    except Exception, e:
        print(e)
        return {"text": str(e)}
    finally:
        conn.close()

    object_url = "https://s3-us-west-1.amazonaws.com/{0}/{1}".format(s3bucket, s3key)
    print(object_url)
    payload = {'text': object_url}
    myResponse = requests.post(hook_url, headers=headers, json=payload)
    
    return 'Hello from Derek, hope you have a good day!'
