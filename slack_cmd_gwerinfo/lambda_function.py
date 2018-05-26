from __future__ import print_function

import os
import time
from datetime import datetime
import urllib
from urllib2 import urlopen
import psycopg2

SITE = os.environ['site']  # URL of the site to check, stored in the site environment variable, e.g. https://aws.amazon.com
EXPECTED = os.environ['expected']  # String expected to be on the page, stored in the expected environment variable, e.g. Amazon
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')

def validate(token, team_domain):
    return EXPECTED ==token and team_domain == 'gigwalk'

def _get_certs(cur, email):
    certs = []
    sql_stmt = "select c.id, c.email, cs.id, cs.title from customers c left outer join customer_cert_associations ca on ca.customer_id = c.id join certifications cs on cs.id = ca.certification_id where lower(email)='{}' and c.organization_id = 5".format(email)
    cur.execute(sql_stmt)
    if cur.rowcount == 0:
        return []
    row = cur.fetchone()
    while row is not None:
        certs.append(row)
        row = cur.fetchone()
    return certs

def _get_tickets(cur, customer_id):
    tickets = []
    # one line sql for testing
    # select os.title, t.id, t.status, case when t.assigned_customer_id=1419753 then 'Yes' else 'No' end as ASSIGNED_TO_ME, t.approval_status, dm.status, os.organization_id, p.status, p.amount, p.date_paid, txn.paypal_trx_id, txn.receiver_email, txn.status from tickets t join organization_subscriptions os on os.id = t.organization_subscription_id join doubleoptin_map dm on t.id = dm.ticket_id left outer join payouts p on p.ticket_id = t.id and p.customer_id = dm.customer_id left outer join payout_transactions txn on p.transaction_id = txn.id where dm.customer_id = 1419753
    sql_stmt = "select os.title, t.id, t.status, " \
               "case when t.assigned_customer_id={} then 'Yes' else 'No' end as ASSIGNED_TO_ME, "\
               "t.approval_status, dm.status, os.organization_id, p.status, p.amount, p.date_paid,"\
               " txn.paypal_trx_id, txn.receiver_email, txn.status "\
               "from tickets t join organization_subscriptions os on os.id = t.organization_subscription_id "\
               "join doubleoptin_map dm on t.id = dm.ticket_id "\
               "left outer join payouts p on p.ticket_id = t.id and p.customer_id = dm.customer_id "\
               "left outer join payout_transactions txn on p.transaction_id = txn.id "\
               "where dm.customer_id = {}".format(customer_id, customer_id) 
    cur.execute(sql_stmt)
    if cur.rowcount == 0:
        return []
    row = cur.fetchone()
    while row is not None:
        tickets.append(row)
        row = cur.fetchone()
    return tickets

def lambda_handler(event, context):
    try:
        if not validate(event.get('token'), event.get('team_domain')):
            raise Exception('Validation failed')

        email = urllib.unquote(event.get('text')).lower() if event.get('text') else None
        certs = []
        tickets = []
        customer_id = None
        if not email:
            return {"text": "hey I need the Gigwalker's email"}
        try:
            conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
            cur = conn.cursor()
            # get certifications
            certs = _get_certs(cur, email)
            if not certs:
                return {"text": "YO! who is this guy, I cannot recognize him"}
            customer_id = certs[0][0]
            tickets = _get_tickets(cur, customer_id)

            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            return {"text": error}
        finally:
            if conn is not None:
                conn.close()
        cert_json = {
          "fallback": "Required plain-text summary of the attachment.",
          "color": "#36a64f",
          "pretext": "Assigned certifications",
          "fields": [{"title": cert[3], "value": cert[2], "short":True} for cert in certs],
          "footer": "Certifications",
          "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
        }
        attachments = [cert_json]
        
        # os.title, t.id, t.status, case when t.assigned_customer_id=1419753 then 'Yes' else 'No' end as ASSIGNED_TO_ME, t.approval_status, dm.status, os.organization_id, p.status, p.amount, p.date_paid, txn.paypal_trx_id, txn.receiver_email, txn.status
        for project_title, ticket_id, ticket_status, assigned_to_me, ticket_approval_status, application_status, org_id, payout_status, payout_amount, payout_paid_date, paypal_txn_id, paypal_receiver_email, txn_status in tickets:
            attachments.append({
              "fallback": "Required plain-text summary of the attachment.",
              "color": "#3B5998",
              "pretext": project_title,
              "title": "https://next.gigwalk.com/tickets/{}/detail/{}".format(org_id, ticket_id),
              "fields": [
                {
                  "title": "Ticket Status",
                  "value": ticket_status,
                  "short": True
                },
                {
                  "title": "ASSIGNED_TO_ME",
                  "value": assigned_to_me,
                  "short": True
                },
                {
                  "title": "Ticket Approval Status",
                  "value": ticket_approval_status,
                  "short": True
                },
                {
                  "title": "My Application Status",
                  "value": application_status,
                  "short": True
                },
                {
                  "title": "Payout Status",
                  "value": payout_status,
                  "short": True
                },
                {
                  "title": "Paypal receiver_email",
                  "value": paypal_receiver_email,
                  "short": True
                },
                {
                  "title": "Payout Amount",
                  "value": "${}".format(payout_amount),
                  "short": True
                },
                {
                  "title": "Paid Date",
                  "value": payout_paid_date.strftime('%m/%d/%Y %H:%M:%S'),
                  "short": True
                },
                {
                  "title": "Paypal TXN ID",
                  "value": paypal_txn_id,
                  "short": True
                },
                {
                  "title": "Paypal TXN Status",
                  "value": txn_status,
                  "short": True
                }
              ]
            })
        response = {
            "text": "ID: {}, Email:{}".format(customer_id, email),
            "attachments": attachments
        }
        return response
    except:
        return {"text": "Don't hack me, I am watching you!"}
    finally:
        print('Check complete at {}'.format(str(datetime.now())))
    