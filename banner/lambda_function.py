import json
import psycopg2
import os

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PWD = os.environ.get('DB_PWD')
RADIUS = os.environ.get('RADIUS_IN_MILES')


def lambda_handler(event, context):
    # default msg, 43 characters.  Old screen coudl only accommodate up to 63
    default_msg = 'New app coming soon-- get a sneak peek now!'
    out = {}
    out['statusCode'] = 200
    out['body'] = default_msg

    d = event.get('queryStringParameters')
    print(d.get('lat'), d.get('long'))

    try:
        lat = float(d.get('lat'))
        longti = float(d.get('long'))
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        cur = conn.cursor()

        radius = float(RADIUS)/69.0
        sql_stmt = "select sum(price) from unassigned_gig_location where ST_DWithin(st_SetSRID(st_makepoint({},{}), 4326), geom_pin, {})".format(longti, lat, radius)
        print(sql_stmt)
        cur.execute(sql_stmt)
        print("this is debug =================this is debug =================") 
        if cur.rowcount == 0:
            return out
        row = cur.fetchone()
        out['body'] = "There are ${} worth of gigs near you in our new app. Download now!".format(row[0])
    except Exception, e:
        print(e)
    finally:
        conn.close()
        print("this is finally debug ================= =================")
        print(out)
        return out
