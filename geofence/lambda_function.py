'''
    Slack Command Format: /update_geofence <PROJECT_ID> <GEOFENCE_IN_MILES> <PROJECT_CREATOR_EMAIL>
'''


import os
import urllib
import psycopg2
import requests

GW_API_HOST = os.environ.get('GW_API_HOST')  # URL of the site to check
GW_AUTH_TOKEN = os.environ.get('GW_AUTH_TOKEN')
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS').split(',')
EXPECTED = os.environ['expected']  # String expected to be on the page (token from Slack)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')


def lambda_handler(event, context):
    '''
    Set the geofence (near_ticket_distance) of the project with validation
    event['text'] should be of the form "<pid>+<geofence>+<creator_email>
    Sample Curl:
        curl https://vgzl7kh5e3.execute-api.us-east-1.amazonaws.com/slackbot/updategeofence \
             -H 'Content-Type: application/x-www-form-urlencoded' \
             --data-binary "user_id=U09TV2DT2&channel_id=D19NDPDQR&text=4153393+1.0+krystle+gwteam@gigwalk.com&team_id=T0298UZFT&token=S66dc1AlO506mDqP1mQTroT4&team_domain=gigwalk&user_name=rv"
    '''
    try:
        # AWS parses AUTHORIZED_USERS setting of 'a, b' as two user names 'a' and ' b'
        # Note the blank in the second user name.
        user_name = event.get('user_name')
        user_name = user_name.strip() if user_name else user_name
        auth = (EXPECTED == event.get('token') and
                event.get('team_domain') == 'gigwalk' and
                user_name in AUTHORIZED_USERS)
        if not auth:
            return "Validation of token, team_domain, user_name failed"
        if not event or not event.get('text'):
            return 'No parameters provided'
        try:
            pid, geofence, email = event.get('text').split('+', 2)
            pid = int(pid)
            geofence = float(geofence)
            email = urllib.unquote(email).lower()
            if geofence <= 0:
                return 'Geofence value cannot be 0 or less'
        except Exception as e:
            return 'Incorrect input, the format should be: `/update_geofence PROJECT_ID GEOFENCE_IN_MILES PROJECT_CREATOR_EMAIL`'

        try:
            conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
            cur = conn.cursor()
        except Exception as e:
            return "DB Glitch? {}".format(e)

        sql_stmt = "SELECT c.email, os.organization_id from customers c, organization_subscriptions os where c.id = os.created_customer_id and os.id = {}".format(pid)
        cur.execute(sql_stmt)
        if cur.rowcount == 0:
            return "Invalid project id?"
        row = cur.fetchone()
        if row[0].lower() != email:
            return "project creator validation failed"

        org_id = row[1]
        url = "https://{}/v1/organizations/{}/subscriptions/{}".format(GW_API_HOST, org_id, pid)
        headers = {'user-agent': 'aws_lambda', 'Authorization': 'Token {}'.format(GW_AUTH_TOKEN), 'Content-Type': 'application/json;charset=UTF-8'}
        payload = {"near_ticket_distance": geofence}
        resp = requests.put(url, headers=headers, json=payload)

        if resp.status_code == 200:
            return "Project {} now has a geofence(near_ticket_distance) of {}".format(pid, geofence)
        return "Could not set geofence for project {}".format(pid)
    except Exception as e:
        return e
    finally:
        cur.close()
        conn.close()
