from __future__ import print_function
import csv
import os
from shutil import copyfile
# import pandas as pd
import datetime
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools

copyfile('credentials.json', '/tmp/credentials.json')
copyfile('client_secret.json', '/tmp/client_secret.json')

# Setup the Drive v3 API
CSV_FILE = '/tmp/qa_list.csv'
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets.readonly']
store = file.Storage('/tmp/credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('/tmp/client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
httpObj = creds.authorize(Http())


def get_project_ids(spreadsheetId):
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    projects_sheet = build('sheets', 'v4', http=httpObj, discoveryServiceUrl=discoveryUrl)
    rangeName = 'Sheet1!A:A'
    result = projects_sheet.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()

    values = result.get('values', [])
    data = []
    for row in values:
        try:
            project_id = int(row[0])
            data.append(project_id)
        except:
            pass
    return data


def upload_file():
    drive_service = build('drive', 'v3', http=httpObj)
    folder_id = '1pS-Ax6qOE3KRHK4PNQq0vGRkOmF6PaBZ'
    file_metadata = {
        'name': 'QA_list_' + datetime.datetime.now().strftime("%Y-%m-%d"),
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id]
    }
    media = MediaFileUpload(CSV_FILE,
                            mimetype='text/csv',
                            resumable=True)
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='webViewLink, id').execute()
    print('File ID: %s' % file.get('id'))
    print('File link: %s' % file.get('webViewLink'))


def generate_file(data):

    columns = [
        'Customer_Email',
        'Project_Title',
        'Project_Url',
        'QA_deadline_date',
        'Project_due_date',
        'Ticket_submitted_date',
        'Ticket_location',
        'Ticket_address',
        'Ticket_state',
        'TicketUrl',
        'Worker_id'
    ]
    with open(CSV_FILE, 'wb') as csv_file:
        wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        wr.writerow(columns)
        for row in data:
            wr.writerow(row)
    # df = pd.DataFrame(data, columns=columns)
    # df.to_csv(CSV_FILE, index=False)
    upload_file()
