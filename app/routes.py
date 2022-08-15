from flask import Blueprint, render_template, redirect, url_for
from app.forms import AppointmentForm
from datetime import datetime, timedelta
import os
import psycopg2


bp = Blueprint('main', __name__, url_prefix='/')

CONNECTION_PARAMETERS = {
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'dbname': os.environ.get('DB_NAME'),
    'host': os.environ.get('DB_HOST')
}

def get_appointments():
    with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, name, start_datetime, end_datetime, description FROM appointments ORDER BY start_datetime')
            rows = curs.fetchall()
            return rows

def get_todays_appointments(y,m,d):
    today = datetime(y,m,d)
    day = timedelta(days=1)
    next_day = today + day

    params = {
        "today": today,
        "next_day": next_day
    }

    with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
        with conn.cursor() as curs:
            curs.execute(
                         """
                         SELECT id, name, start_datetime, end_datetime, description FROM appointments
                         WHERE start_datetime BETWEEN %(today)s AND %(next_day)s ORDER BY start_datetime
                         """,
                         params
                        )
            rows = curs.fetchall()
            return rows

def insert_appointment(form):
    params = {
        'name': form.name.data,
        'start_datetime': datetime.combine(form.start_date.data, form.start_time.data),
        'end_datetime': datetime.combine(form.end_date.data, form.end_time.data),
        'description': form.description.data,
        'private': form.private.data
    }

    with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
        with conn.cursor() as curs:
            curs.execute("""
                         INSERT INTO appointments (name, start_datetime, end_datetime, description, private) VALUES
                         (%(name)s, %(start_datetime)s, %(end_datetime)s, %(description)s, %(private)s)
                         """,
                         params
                        )

    print('successfully inserted!')


@bp.route('/', methods=('GET', 'POST'))
def main():
    rows = get_appointments()
    form = AppointmentForm()

    today = datetime.now()
    today_url = url_for('.daily', year=today.year, month=today.month, day=today.day)

    if form.validate_on_submit():
        insert_appointment(form)
        return redirect('/')

    return render_template('main.html', rows=rows, form=form, today=today_url)


@bp.route('/<int:year>/<int:month>/<int:day>', methods=('GET', 'POST'))
def daily(year, month, day):
    rows = get_todays_appointments(year, month, day)
    form = AppointmentForm()

    if form.validate_on_submit():
        insert_appointment(form)
        return redirect(f'/{year}/{month}/{day}')

    return render_template('daily.html', rows=rows, form=form, date=f'{month}/{day}/{year}')
