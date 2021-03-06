#!/usr/bin/env python3

"""
1) change to directory containing
login.html
cgi-bin/login.py

2) run server with one of
python -m CGIHTTPServer 8247
python -m http.server --cgi 8247
python3 -m http.server --cgi 8247

3) point browser at
http://localhost:8247/login.html
"""
import cgi
import psycopg2

print("Content-type: text/html\n")
print("<title>Login Result</title>")
print("<body><center>")

try:
    # get post data
    form = cgi.FieldStorage()
    name = form['name'].value if 'name' in form else ''
    pwd = form['pwd'].value if 'pwd' in form else ''

    # debug
    # select permissions from users where name='admin' and pwd=' 'union select pwd from users where name='admin  '
    # select permissions from users where name='admin' and pwd=' ' or '1' = '1  '
    # print(pwd)

    permissions = []
    # query to check password and get permissions
    query = "select permissions from users where name='{}' and pwd='{}';".format(name, pwd)

    # debug
    # print(query)

    SQL = "select permissions from users where name=(%s) and pwd=(%s)"  # Note: no quotes
    data = ("{:s}".format(name), "{:s}".format(pwd))

    # connect to database
    conn = psycopg2.connect("dbname='158.247' user='158.247-app' host='127.0.0.1' password='foobar'")
    cursor = conn.cursor()

    cursor.execute(SQL, data)
    permissions = cursor.fetchall()

    # debug
    # print(permissions)

    if len(permissions) > 0:
        print("<H1>Access granted. You have the following permissions: {}.</H1>".format(permissions[0][0]))
    else:
        print("<H1>Access denied.</H1>")
except psycopg2.Error as e:
    # for ease of debugging
    print("Database Error: {}".format(e))
    print("<br>Query: {}".format(query))

print("""
<form action="../login.html" method="GET">
    <input type="submit" value="Back to Login">
</form>
""")

print('</center></body>')
