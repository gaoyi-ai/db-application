#!/usr/bin/env python3

import cgi
from datetime import date

import psycopg2


def date2str(date: tuple) -> dict[str, str]:
    return {'apt_date': str(date[0]), 'apt_start': str(date[1]), 'apt_end': str(date[2])}


def display_table(res):
    print("""
<table border="1">
  <caption>Fully Booked Periods</caption>
  <tr>
    <th>Date</th>
    <th>Start</th>
    <th>End</th>
  </tr>
""")
    for a in res:
        date_str = date2str(a)
        print(f"""
  <tr>
    <td>{date_str.get('apt_date')}</td>
    <td>{date_str.get('apt_start')}</td>
    <td>{date_str.get('apt_end')}</td>
  </tr>
""")
    print("</table><hr>")


print("Content-type: text/html\n")
print("<title>Make a Appointment</title>")
print("<body><center>")

try:
    # get post data
    form = cgi.FieldStorage()
    apt_start = date.fromisoformat(form['apt_start'].value if 'apt_start' in form else '')
    apt_end = date.fromisoformat(form['apt_end'].value if 'apt_end' in form else '')

    fully_booked = []

    query = "select apt_date,apt_start,apt_end from fully_booked where apt_date between '{}' and '{}';".format(
        apt_start,
        apt_end)

    SQL = "select apt_date,apt_start,apt_end from fully_booked where apt_date between (%s) and (%s)"
    data = (apt_start, apt_end)

    # connect to database
    conn = psycopg2.connect("dbname='158.247' user='158.247-app' host='127.0.0.1' password='foobar'")
    cursor = conn.cursor()

    cursor.execute(SQL, data)

    fully_booked = cursor.fetchall()

    display_table(fully_booked)

except psycopg2.Error as e:
    # for ease of debugging
    print("Database Error: {}".format(e))
    print("<br>Query: {}".format(query))

print("""
<form action="appointment_insert.py" method="POST">
Your Full Name:<br><input type="text" name="patient" value="" size=40><br>
The doctor:<br><input type="text" name="doctor" value="" size=40><br>
Appointment Date:<br><input type="date" name="apt_date" value="" size=40><br>
Appointment Start Time:<br><input type="time" name="apt_start" value="" size=40><br>
Appointment End Time:<br><input type="time" name="apt_end" value="" size=40><br>
<br><input type="submit" value="Make a Appointment">
</form>
""")

print('</center></body>')
