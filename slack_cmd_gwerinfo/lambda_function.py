from __future__ import print_function
import os

from datetime import datetime
import urllib
from models import Switch, CustomerQuery, NoParamQuery, SimpleQuery
from commands import AssignedCommand, SubmittedCommand, AppliedCommand, AllPublicCommand, WorkerCommand
# from enum import Enum
import re

EXPECTED = os.environ['expected'].split(',')  # String expected to be on the page, stored in the expected environment variable, e.g. Amazon
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS').split(',')

class SlackCommand(object):
    ASSIGNED = 'assigned'
    APPLIED = 'applied'
    SUBMITTED = 'submitted'
    ALLPUBLIC = 'allpublic'
    WORKER = 'worker'

CUSTOMER_QUERY_COMMADS = set([SlackCommand.ASSIGNED, SlackCommand.APPLIED, SlackCommand.SUBMITTED])

def validate(event):
    auth = (event.get('token') in EXPECTED and event.get('team_domain') == 'gigwalk' and event.get('user_name') in AUTHORIZED_USERS)
    if not auth:
        raise Exception('Validation failed')

    param = None
    command = None
    try:
        print(event.get('command'), event.get('text'))
        # url decoding, not really needed with proper cleaning upfront in API gateway
        param = urllib.unquote(event.get('text')).lower() if event.get('text') else None
        command = urllib.unquote(event.get('command'))[1:]
        # params and command validation
        if command in CUSTOMER_QUERY_COMMADS:
            EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
            if not (param and re.match(EMAIL_REGEX, param)):
                raise ValueError("please provide correct email address")

        if command == SlackCommand.WORKER:
            if not (param and param.isdigit()):
                raise ValueError("please provide correct parameter for the command")
    except ValueError as e:
        raise e
    except Exception as e:
        print(e)
        raise ValueError('Something goes wrong unexpected, note down your command/parameter and contact Derek')
    return command, param


def lambda_handler(event, context):
    try:
        print(event)
        command, param = validate(event)
        light = None
        commandObj = None
        response = "Something wrong with your query.  How may I help you?"

        switch = Switch()

        if command == SlackCommand.ASSIGNED:
            light = CustomerQuery(param)
            commandObj = AssignedCommand(light)
        elif command == SlackCommand.APPLIED:
            light = CustomerQuery(param)
            commandObj = AppliedCommand(light)
        elif command == SlackCommand.SUBMITTED:
            light = CustomerQuery(param)
            commandObj = SubmittedCommand(light)
        elif command == SlackCommand.ALLPUBLIC:
            light = NoParamQuery()
            commandObj = AllPublicCommand(light)
        elif command == SlackCommand.WORKER:
            light = SimpleQuery(param)
            commandObj = WorkerCommand(light)
        if light and commandObj:
            response = switch.execute(commandObj)
        return response
    except Exception as e:
        print(e)
        return str(e)
        #{"text": "Something goes wrong"}
    finally:
        print('Check complete at {}'.format(str(datetime.now())))
