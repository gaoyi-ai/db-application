#!/usr/bin/env python3

import cgi
from datetime import date, time

import psycopg2

print("Content-type: text/html\n")
print("<title>Appointment Result</title>")
print("<body><center>")

try:
    # get post data
    form = cgi.FieldStorage()
    patient = form['patient'].value if 'patient' in form else ''
    doctor = form['doctor'].value if 'doctor' in form else ''
    apt_date = date.fromisoformat(form['apt_date'].value if 'apt_date' in form else '')
    apt_start = time.fromisoformat(form['apt_start'].value if 'apt_start' in form else '')
    apt_end = time.fromisoformat(form['apt_end'].value if 'apt_end' in form else '')

    # connect to database
    conn = psycopg2.connect("dbname='158.247' user='158.247-app' host='127.0.0.1' password='foobar'")
    cursor = conn.cursor()

    query = "insert into appointments values ({},{},{},{},{});".format(patient, doctor, apt_date, apt_start, apt_end)

    SQL = "insert into appointments values (%s,%s,%s,%s,%s)"
    data = (patient, doctor, apt_date, apt_start, apt_end)

    cursor.execute(SQL, data)
    conn.commit()

    print('<strong style="color:green;">Success.</strong>')

except psycopg2.Error as e:
    print('<strong style="color:red;">Failed.</strong>')
    if 'fully booked' in e.pgerror:
        print(f"The limit of 3 concurrent appointments is exceeded for that time period between {str(apt_start)} \
            and {str(apt_end)} in {str(apt_date)}.")
    else:
        print(f"The doctor {doctor} is not available as well for that time period between {str(apt_start)} \
        and {str(apt_end)} in {str(apt_date)}.")
    # # for ease of debugging
    # print("<hr>Database Error: {}".format(e))
    print("<hr>Query: {}".format(query))

print("""
<hr>
<form action="../appointment.html" method="GET">
    <input type="submit" value="Back to Appointment">
</form>
""")

print('</center></body>')
