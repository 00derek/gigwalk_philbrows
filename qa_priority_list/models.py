import os
import psycopg2

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')
LIMIT = os.environ.get('LIMIT', 2200)

__all__ = ['Projects', 'Tickets']

class Model:
    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)

    def _execute_query(self, query):
        data = []
        cur = self.conn.cursor()
        cur.execute(query)
        if cur.rowcount == 0:
            return []
        row = cur.fetchone()
        while row is not None:
            data.append(row)
            row = cur.fetchone()
        return data


class Projects(Model):

    def get_projects_by_id_list(self, ids):
        query = "SELECT * FROM organization_subscriptions where id in ({})".format(",".join(ids))
        return self._execute_query(query)


class Tickets(Model):

    def get_tickets_by_project_id(self, project_ids):
        query = """
        SELECT
        Customer.email,
        Project.title,
        CONCAT(
         'https://app.gigwalk.com/projects/',
         Project.organization_id,
         '/active/',
         Project.id
        ) as ProjectUrl,
        CASE
          WHEN Payout.status = 'payout' THEN Payout.date_created + INTERVAL '10 MINUTE'
          ELSE Ticket.date_submitted
        END as QA_deadline_date,
        CASE
          WHEN Project.end_date IS NOT NULL THEN Project.end_date
          ELSE Ticket.due_date
        END as Project_due_date,
        Ticket.date_submitted as Ticket_submitted_date,
        Location.title as Ticket_location,
        Location.address as Ticket_address,
        Location.administrative_area_level_1 as Ticket_state,
        CONCAT(
          'https://app.gigwalk.com/tickets/',
          Project.organization_id,
          '/detail/',
          Ticket.id
        ) as TicketUrl,
        Worker.id as Worker_id
        FROM
        tickets as Ticket
        LEFT JOIN locations as Location on Location.id = Ticket.location_id
        LEFT JOIN organization_subscriptions as Project on Project.id = Ticket.organization_subscription_id
        LEFT JOIN payouts as Payout on Payout.ticket_id = Ticket.id
        LEFT JOIN customers as Customer on Customer.id = Project.created_customer_id
        LEFT JOIN customers as Worker on Worker.id = Ticket.assigned_customer_id
        WHERE Ticket.status = 'SUBMITTED' and Ticket.approval_status != 'APPROVED' and Project.id in ({})
        ORDER BY QA_deadline_date, Ticket_submitted_date 
        LIMIT {};
        """
        project_ids_string = [str(_id) for _id in project_ids]
        query = query.format(",".join(project_ids_string), LIMIT)
        return self._execute_query(query)