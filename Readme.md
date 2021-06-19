# Preparation

In this assignment you will run a small webserver with a web page that queries a local postgres database. To begin with, create the following table in your local database db-application (schema public):

```sql
create table users( 
    name varchar(20) not null
    , pwd varchar(20) not null 
    , permissions varchar(20) 
    , constraint pk_users primary key (name)
); 

insert into users values (’johndoe’, ’pa55word’, ’read’); 
insert into users values (’admin’, ’hArd2gu3ss’, ’read,write’); 
insert into users values (’janedoe’, ’top5ecret’, ’read’); 
```

Next create a new login role db-app with password foobar, and grant it access with the query: 

```sql
CREATE USER "db-app" WITH PASSWORD ’foobar’; 
GRANT USAGE ON SCHEMA public TO "db-app"; 
GRANT SELECT ON TABLE users TO "db-app";
```

The program generating the page is written in python, and requires some setup. 

1. Install the python module psycopg2 for connecting to postgres, by running one of 

```
> python3 -m pip install psycopg2-binary
```

A documentation of the module can be found at http://initd.org/psycopg/docs/.

Finally you need to setup a web server to serve your script. Python already includes an HTTP server module, which can be used for this task by running one of the following commands (in the directory where login.html is located), for python3 : 

```
> python3 -m http.server --cgi 8247
```

Python’s http server will try to execute any script it ﬁnds in cgi-bin and send its output to port 8247. Linux and OS/X users need to ensure login.py has execution permission. This can be done with the command

```
> chmod a+x login.py 
```


If you now point your browser at http://localhost:8247/login.html, you should see a login page.                                                                  When you enter a username and password, request will be handled by login.py which checks the course database for a matching user name and password, and grants or denies access accordingly. 

# Tasks

1. Consider the tables availability and appointments below, storing doctors’ availability and appointment details. 

```sql
CREATE TABLE availability(
    doctor varchar(20) NOT NULL
    , avl_date date NOT NULL
    , avl_start time NOT NULL
    , avl_end time NOT NULL
    , CONSTRAINT pk_availability PRIMARY KEY (doctor, avl_date)
);
```

```sql
CREATE TABLE appointments(
    patient varchar(20) NOT NULL
    , doctor varchar(20) NOT NULL
    , apt_date date NOT NULL
    , apt_start time NOT NULL
    , apt_end time NOT NULL
    , CONSTRAINT pk_appointments PRIMARY KEY (patient, apt_date)
);
```

2. Opening hours are from 8am to 5pm each day. Add a constraint to ensure that appointment times are sensible.

    ```sql
    alter table appointments
        add constraint time_constraints check ( apt_start >= '08:00 AM' and apt_end <= '05:00 PM' and apt_start < apt_end);
    ```

3. Create a database function apt count which takes as input a date and time and returns the number of appointments active at the given date and time. Include appointments starting at the given time.

    ```sql
    create function apt_count(_date date, _time time) returns int as
    $$
    begin
        return (select count(1)
                from appointments
                where apt_date = _date
                  and apt_start <= _time
                  and apt_end > _time);
    end;
    $$ language plpgsql;
    ```

4. The facility can allow at most 3 patients at any point in time. Create a view fully booked which lists all maximal time periods (apt date, apt start, apt end) during which no further appointments are possible (consider doctors' availability as well).
    Hint: Identify for each start time where maximal permitted appointments are reached the minimal end time at which they drop below that number again. Then eliminate non-maximal intervals. 
    该设施可在任何时间最多允许3名患者。创建一个视图fully_booked，列出所有最长的时间段(apt_date，apt_start，apt_end)，在此期间不可能有进一步的预约(考虑到医生的可用性)。提示:确定达到最大允许约会的每个开始时间，以及再次低于该数字的最小结束时间。然后消除非极大区间

    ```sql
    drop view if exists all_apt_start;
    create view all_apt_start as
    (
    select distinct apt_date, apt_start, apt_date + apt_start as apt_datetime_start, apt_count(apt_date, apt_start) as reach
    from appointments
        );
    
    drop view if exists all_apt_end;
    create view all_apt_end as
    (
    select distinct apt_date, apt_end, apt_date + apt_end as apt_datetime_end, apt_count(apt_date, apt_end) as below
    from appointments
        );
    
    drop view if exists all_periods;
    create view all_periods as
    (
    select apt_date, apt_start, apt_datetime_start, min(apt_datetime_end) apt_datetime_end
    from (select aas.apt_date, apt_start, apt_datetime_start, apt_datetime_end
          from all_apt_start aas,
               all_apt_end aae
          where aas.apt_date = aae.apt_date
            and reach = 3
            and below < 3
            and apt_end > apt_start) tmp
    where apt_datetime_end > apt_datetime_start
    group by apt_date, apt_start, apt_datetime_start
        );
    
    drop view if exists fully_booked;
    create view fully_booked as
    (
    select distinct x.apt_date,
                    x.apt_start,
                    x.apt_datetime_end::time apt_end
    from (
             select apt_date, apt_start, apt_datetime_start, apt_datetime_end
             from all_periods) x
             left join (
        select apt_date, apt_start, apt_datetime_start, apt_datetime_end
        from all_periods) y
                       on x.apt_date = y.apt_date
    where x.apt_datetime_start < y.apt_datetime_start
       or x.apt_datetime_start > y.apt_datetime_end
        );
    
    GRANT SELECT ON fully_booked TO "db-app";
    GRANT SELECT ON TABLE appointments TO "db-app";
    ```

5. Create a website which lets a user enter a day range for making an appointment, then displays a list of all time periods where the maximal number of permitted appointments has already been reached. The user should then be able to enter the details to make an appointment. When storing this appointment in the database, you must ensure that the limit of 3 concurrent appointments is not exceeded and a doctor is available as well for that time period.
    创建一个网站，允许用户输入进行预约的一天范围，然后显示所有时间段的列表，其中允许的预约的最大数量已经达到。用户应该能够输入详细信息进行预约。在数据库中存储此约会时，必须确保不超过3个并发约会的限制，并且在此期间有一位医生可用。
    Feel free to use login.html and login.py as starting points, but rename them to appointment.html and appointment.py to avoid confusion when marking. For processing appointment requests, create a new ﬁle appointment insert.py. 
    Tip: Use <input type="date" ...> in appointment.html for entering start and end dates. To format the query result for display, you can use an [html table](https://developer.mozilla.org/en/docs/Web/HTML/Element/table#Examples).

    ```sql
    drop function if exists check_available(varchar, date, time, time);
    create function check_available(doc varchar, a_date date, a_start time, a_end time) returns bool
        language plpgsql
    as
    $$
    begin
        return (
            select exists(
                           select 1
                           from availability
                           where doctor = doc
                             and avl_date = a_date
                             and not (avl_start <= a_start
                               and avl_end >= a_end)
                       ) or not exists(
                    select 1
                    from availability
                    where doctor = doc
                )
        );
    end;
    $$;
    
    drop function if exists check_conflict(varchar, date, time, time);
    create function check_conflict(doc varchar, a_date date, a_start time, a_end time) returns bool
        language plpgsql
    as
    $$
    begin
        return (
            select exists(
                           select 1
                           from appointments
                           where doctor = doc
                             and apt_date = a_date
                             and not (apt_start >= a_end
                               or apt_end <= a_start)
                       )
        );
    end;
    $$;
    
    drop function if exists check_fully_booked(varchar, date, time, time);
    create function check_fully_booked(a_date date, a_start time, a_end time) returns bool
        language plpgsql
    as
    $$
    begin
        return (
            select exists(
                           select 1
                           from fully_booked
                           where apt_date = a_date
                             and not (apt_start >= a_end
                               or apt_end <= a_start)
                       )
        );
    end;
    $$;
    
    
    drop function if exists insert_appointment();
    create function insert_appointment() returns trigger
        language plpgsql
    as
    $$
    begin
        if (select check_available(new.doctor, new.apt_date, new.apt_start, new.apt_end))
        then
            RAISE exception 'The % is not available between % and % in %',new.doctor,new.apt_start,new.apt_end,new.apt_date;
        elseif (select check_conflict(new.doctor, new.apt_date, new.apt_start, new.apt_end))
        then
            RAISE exception 'Conflict in the New Appointment : % % % %',new.doctor,new.apt_date,new.apt_start,new.apt_end USING ERRCODE = 'unique_violation';
        elseif (select check_fully_booked(new.apt_date, new.apt_start, new.apt_end))
        then
            RAISE exception 'Already fully booked between % and % in %',new.apt_date,new.apt_start,new.apt_end;
        end if;
        return new;
    end;
    $$;
    
    drop trigger if exists before_insert_appointment on appointments;
    create trigger before_insert_appointment
        before insert
        on appointments
        for each row
    execute function insert_appointment();
    
    GRANT INSERT ON TABLE appointments TO "db-app";
    GRANT SELECT ON TABLE availability TO "db-app";
    ```