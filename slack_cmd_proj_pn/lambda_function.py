from __future__ import print_function

import os
import time
from datetime import datetime
import urllib
from urllib2 import urlopen
import requests
import psycopg2

GW_API_HOST = os.environ['GW_API_HOST']  # URL of the site to check, stored in the site environment variable, e.g. https://aws.amazon.com
GW_AUTH_TOKEN = os.environ['GW_AUTH_TOKEN']
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
    if not event.get('text'):
        raise Exception('No parameters provided')

    try:
        pid, email, msg = event.get('text').split('+', 2)
        pid = int(pid)
        email = urllib.unquote(email).lower()
        msg = urllib.unquote(msg).lower().replace('+', ' ').encode('ascii', 'ignore')
    except Exception as e:
        print(e)
        raise ValueError('Something wrong with your input, the format should be: `/nudge PROJECT_ID PROJECT_CREATOR_EMAIL YOUR_MSG`')
    return  pid, email, msg
    
    
def lambda_handler(event, context):
    try:
        pid, email, msg = validate(event)
        print(pid, email, msg)
        payload = {"ticket_event_type":"COMMENT","ticket_event_data":{"comment": msg}}
        headers = {'user-agent': 'aws_lambda', 'Authorization': 'Token {}'.format(GW_AUTH_TOKEN), 'Content-Type': 'application/json;charset=UTF-8'}
        
        tids = _get_project_ticket_ids_with_validation(pid, email)
        print("this is debug =================this is debug =================1", tids)
        for tid in tids:
            url = "https://{}/v1/tickets/{}/events".format(GW_API_HOST, tid)
            myResponse = requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print(e) 
        return {"text": str(e)}
    finally:
        print('Check complete at {}'.format(str(datetime.now())))
    resp_text = "Comments have been added to these ticket ids: {}".format(tids)
    hook_url = event.get('response_url')
    headers = {'user-agent': 'aws_lambda', 'Content-Type': 'application/json;charset=UTF-8'}
    payload = {'text': resp_text}
    myResponse = requests.post(hook_url, headers=headers, json=payload)


def _get_project_ticket_ids_with_validation(pid, email):
    # validate provided email is the project creator email 
    # and return a list of assigned/scheduled/started ticekt ids
    # one line sql for testing
    # SELECT c.email, t.id from organization_subscriptions os, customers c, tickets t where os.id = t.organization_subscription_id and c.id = os.created_customer_id and t.status in ('STARTED', 'ASSIGNED', 'SCHEDULED') and os.id = 12061015
    tickets = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        cur = conn.cursor()
        sql_stmt = "SELECT c.email, t.id from organization_subscriptions os, customers c, tickets t where os.id = t.organization_subscription_id and c.id = os.created_customer_id and t.status in ('STARTED', 'ASSIGNED', 'SCHEDULED') and os.id = {}".format(pid) 
        print(sql_stmt)
        cur.execute(sql_stmt)
        
        print(cur.rowcount)
        if cur.rowcount == 0:
            return tickets
        
        row = cur.fetchone()
        if row[0] != email:
            raise ValueError("project creator validation failed")
        while row is not None:
            if row[1]:
                tickets.append(row[1])
            row = cur.fetchone()
    except Exception as e:
        raise e
    finally:
        conn.close()
    return tickets