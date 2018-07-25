import os
FE_SITE = os.environ['site']  # URL of the site to check

class Command(object):
    """The COMMAND interface"""
    def __init__(self, obj):
        self._obj = obj
        self.results = None

    def execute(self):
        if not self.query:
            return "No query defined for the command"
        self.results = self._obj.run_query(self.query)

        if self.results:
            return self.render_response()
        return "Command executed but no results"

    def render_response(self):
        raise NotImplementedError


class WorkerCommand(Command):
    def __init__(self, obj):
        Command.__init__(self, obj)
        self.query = "SELECT c.last_name, c.first_name, c.email, c.id, cert.title FROM customers c JOIN tickets t ON t.assigned_customer_id = c.id LEFT OUTER JOIN customer_cert_associations cca ON cca.customer_id = c.id LEFT OUTER JOIN certifications cert ON cert.id = cca.certification_id WHERE t.id = {}"

    def render_response(self):
        """
          assigned worker full name, assigned worker email address, assigned_customer_id, certification titles
        """
        attachments = []
        last_name, first_name, email, customer_id, _ = self.results[0]
        certs = [cert for (_, _, _, _, cert) in self.results if cert is not None]
        attachments.append({
                "fallback": "fallback text",
                "fields": [
                    {
                      "title": "Assigned worker full name",
                      "value": last_name+', '+first_name,
                      "short": True
                    },
                    {
                      "title": "Assigned worker email address",
                      "value": email,
                      "short": True
                    },
                    {
                      "title": "Assigned customer_id",
                      "value": customer_id,
                      "short": True
                    },
                    {
                      "title": "Certification",
                      "value": ', '.join(certs) if certs else None,
                      "short": True
                    }]
            })
        response = {
          "text": "Ticket assigned to:",
          "attachments": attachments
        }
        return response


class AllPublicCommand(Command):
    def __init__(self, obj):
        Command.__init__(self, obj)
        self.query = "SELECT os.organization_id, os.title, c.email, os.id FROM organization_subscriptions os LEFT OUTER JOIN customers c ON c.id = os.created_customer_id WHERE os.needs_public_workforce = True AND os.start_date < now() AND os.end_date > now()"

    def render_response(self):
        """
          title, project creator email, link
        """
        attachments = []
        for org_id, title, creator, project_id in self.results:
            attachments.append({
                  "fallback": "Active public wf projects",
                  "title": title,
                  "title_link": "{}/projects/{}/active/{}".format(FE_SITE, org_id, project_id),
                  "text": "Project Creator: {}".format(creator)
              })
        response = {
          "text": "Active public workforce projects:",
          "attachments": attachments
        }
        return response


class AppliedCommand(Command):
    """
        Given a worker email address, 
        get list of all tickets the worker has applied to in the past 30 days
        suggested command: /applied [email]
    """
    def __init__(self, obj):
        Command.__init__(self, obj)
        self.query = "SELECT os.title, c.email, os.organization_id, t.id, dm.date_created, dm.status FROM tickets t JOIN organization_subscriptions os ON os.id = t.organization_subscription_id LEFT OUTER JOIN customers c ON c.id = os.created_customer_id LEFT OUTER JOIN doubleoptin_map dm ON dm.ticket_id = t.id WHERE dm.date_created > Now() - interval '30 days'AND t.assigned_customer_id = {}"

    def render_response(self):
        """
        title, project creator email ,link ,date applied ,application_status
        """
        attachments = []
        for title, creator, org_id, ticket_id, date_applied, application_status in self.results:
            attachments.append({
                "fallback": "all tickets the worker has applied to in the past 30 days",
                "title": title,
                "title_link": "{}/tickets/{}/detail/{}".format(FE_SITE, org_id, ticket_id),
                "fields": [
                    {
                      "title": "Project creator",
                      "value": creator,
                      "short": True
                    },
                    {
                      "title": "Date applied",
                      "value": date_applied.strftime('%m/%d/%Y %H:%M:%S') if date_applied else None,
                      "short": True
                    },
                    {
                      "title": "Application status",
                      "value": application_status,
                      "short": True
                    }]
            })
        response = {
          "text": "Applied tickets in the last 30 days:",
          "attachments": attachments
        }
        return response


class SubmittedCommand(Command):
    """
        Given a worker email address, 
        get list of all active (unsubmitted) tickets currently assigned to the worker
        suggested command: /submitted [email]
    """
    def __init__(self, obj):
        Command.__init__(self, obj)
        self.query = "SELECT os.title, c.email, os.organization_id, t.id, t.date_submitted, p.status, txn.receiver_email, p.amount, p.date_paid, txn.paypal_trx_id FROM tickets t JOIN organization_subscriptions os ON os.id = t.organization_subscription_id LEFT OUTER JOIN customers c ON c.id = os.created_customer_id LEFT OUTER JOIN payouts p ON p.ticket_id = t.id LEFT OUTER JOIN payout_transactions txn ON p.transaction_id = txn.id WHERE t.date_submitted > Now() - interval '6 months' AND t.status='SUBMITTED' AND t.assigned_customer_id = {}"

    def render_response(self):
        """
          title, project creator email ,link ,date submitted ,payment status ,paypal received email ,paypal amount ,paid date
        """
        attachments = []
        for title, creator, org_id, ticket_id, date_submitted, payout_status, payout_email, payout_amount, date_paid, paypal_trx_id in self.results:
            attachments.append({
                  "fallback": "Last 6 months submitted tickets of the worker",
                  "title": title,
                  "title_link": "{}/tickets/{}/detail/{}".format(FE_SITE, org_id, ticket_id),
                  "fields": [
                    {
                      "title": "Project creator",
                      "value": creator,
                      "short": True
                    },
                    {
                      "title": "Date submitted",
                      "value": date_submitted.strftime('%m/%d/%Y %H:%M:%S') if date_submitted else None,
                      "short": True
                    },
                    {
                      "title": "Payment status",
                      "value": payout_status,
                      "short": True
                    },
                    {
                      "title": "Paypal received email",
                      "value": payout_email,
                      "short": True
                    },
                    {
                      "title": "Paypal amount",
                      "value": "${}".format(payout_amount) if payout_amount else None,
                      "short": True
                    },
                    {
                      "title": "Paid date",
                      "value": date_paid.strftime('%m/%d/%Y %H:%M:%S') if date_paid else None,
                      "short": True
                    },
                    {
                      "title": "Paypal txn id",
                      "value": paypal_trx_id,
                      "short": True
                    },
                  ]
              })
        response = {
          "text":"Submitted tickets in the last 6 months:",
          "attachments": attachments
        }
        return response


class AssignedCommand(Command):
    """
        Given a worker email address, 
        get list of all active (unsubmitted) tickets currently assigned to the worker
        suggested command: /assigned [email]
    """
    def __init__(self, obj):
        Command.__init__(self, obj)
        self.query = "SELECT os.organization_id, os.title, c.email, t.id FROM tickets t, organization_subscriptions os, customers c WHERE c.id = os.created_customer_id AND os.id = t.organization_subscription_id AND t.status IN ('ASSIGNED', 'SCHEDULED', 'STARTED') AND t.assigned_customer_id={}"

    def render_response(self):
        """
          title, project creator email, link
        """
        attachments = []
        for org_id, title, creator, ticket_id in self.results:
            attachments.append({
                  "fallback": "Active (unsubmitted) tickets currently assigned to the worker",
                  "title": title,
                  "title_link": "{}/tickets/{}/detail/{}".format(FE_SITE, org_id, ticket_id),
                  "text": "Project Creator: {}".format(creator)
              })
        response = {
          "text": "Assigned Tickets:",
          "attachments": attachments
        }
        return response
