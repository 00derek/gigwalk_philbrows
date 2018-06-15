"""
Shows basic usage of the Drive v3 API.

Creates a Drive v3 API service and prints the names and ids of the last 10 files
the user has access to.
"""
from __future__ import print_function
import os
import json
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

CREDENTIALS = os.environ['CREDENTIALS']
credentials_json = json.loads(CREDENTIALS)
CLIENT_SECRET_JSON = os.environ['CLIENT_SECRET_JSON']
client_secret_json = json.loads(CLIENT_SECRET_JSON)


# Setup the Drive v3 API
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets.readonly']
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
httpObj = creds.authorize(Http())
service = build('drive', 'v3', http=httpObj)

# spreadsheetId = '1t-WYZOfokamnizhxjY4iCoTcBezS1Ti_pfZaZ1gVnhQ'
# discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
# projects_sheet = build('sheets', 'v4', http=httpObj, discoveryServiceUrl=discoveryUrl)
# rangeName = 'Sheet1!A:A'
# result = projects_sheet.spreadsheets().values().get(
#     spreadsheetId=spreadsheetId, range=rangeName).execute()
#
# values = result.get('values', [])
# for row in values:
#     print(row)
#
# Call the Drive v3 API
results = service.files().list(
    pageSize=10, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])
if not items:
    print('No files found.')
else:
    print('Files:')
    for item in items:
        print('{0} ({1})'.format(item['name'], item['id']))
