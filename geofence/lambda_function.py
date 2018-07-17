'''
    Slack Command Format: /update_geofence <PROJECT_ID> <GEOFENCE_IN_MILES> <PROJECT_CREATOR_EMAIL>
'''


import os
import urllib
import psycopg2

GW_API_HOST = os.environ['GW_API_HOST']  # URL of the site to check
GW_AUTH_TOKEN = os.environ['GW_AUTH_TOKEN']
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
        auth = (EXPECTED == event.get('token') and
                event.get('team_domain') == 'gigwalk' and
                event.get('user_name') in AUTHORIZED_USERS)
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

        sql_stmt = "SELECT c.email from customers c, organization_subscriptions os where c.id = os.created_customer_id and os.id = {}".format(pid)
        cur.execute(sql_stmt)
        if cur.rowcount == 0:
            return "Invalid project id?"
        row = cur.fetchone()
        if row[0].lower() != email:
            return "project creator validation failed"

        sql_stmt = "UPDATE organization_subscriptions SET near_ticket_distance = {} where id = {}".format(geofence, pid)
        cur.execute(sql_stmt)
        conn.commit()

        if cur.rowcount == 1:
            return "Project {} now has a geofence(near_ticket_distance) of {}".format(pid, geofence)
        else:
            "Could not set geofence for project {}".format(pid)
    except Exception as e:
        return e
