import os
import psycopg2

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')

class Switch(object):
    """The INVOKER class"""
    def execute(self, command):
        return command.execute()

class Query(object):
    """The RECEIVER class"""
    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        self.cur = self.conn.cursor()
    def _run_query(self, query):
        results = []
        try:
            self.cur.execute(query)
            if self.cur.rowcount == 0:
                return results
            row = self.cur.fetchone()
            while row is not None:
                results.append(row) 
                row = self.cur.fetchone()
        except Exception as e:
            raise e
        finally:
            self.conn.close()
        return results

    def run_query(self, query):
        raise NotImplementedError


class NoParamQuery(Query):
    def __init__(self):
        Query.__init__(self)

    def run_query(self, query):
        return self._run_query(query)


class SimpleQuery(Query):
    def __init__(self, param=None):
        Query.__init__(self)
        self.param = param

    def run_query(self, query):
        query = query.format(self.param)
        return self._run_query(query)


class CustomerQuery(Query):
    def __init__(self, email=None):
        Query.__init__(self)
        row = None
        try:
            sql_stmt = "select c.id from customers c where lower(email)='{}'".format(email)
            self.cur.execute(sql_stmt)
            row = self.cur.fetchone()
        except e:
            raise ValueError('Something wrong to get customer id')
        if not row:
            raise ValueError('Cannot find the email: {}'.format(email))
        self.customer_id = row[0]

    def run_query(self, query):
        query = query.format(self.customer_id)
        return self._run_query(query)
