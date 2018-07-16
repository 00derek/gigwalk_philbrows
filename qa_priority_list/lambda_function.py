import os
import gdocs

from models import Projects, Tickets
FILE_KEY = os.environ['FILE_KEY']


def priority_list(projects):
    tickets = Tickets().get_tickets_by_project_id([project[0] for project in projects])
    if tickets:
        gdocs.generate_file(tickets)


def lambda_handler(event, context):


    project_ids = gdocs.get_project_ids(FILE_KEY)
    if not project_ids:
        return "No projects found"
    print project_ids
    projects = Projects().get_projects_by_id_list([str(_id) for _id in project_ids])
    priority_list(projects)
    return 'Done'

if __name__ == '__main__':
    lambda_handler(1,2)