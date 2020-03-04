import re
import sqlite3
from datetime import date
from datetime import datetime as dt
from typing import Tuple

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dateutil.parser
import feedparser
import plotly.graph_objects as go
import requests
from dash.dependencies import Input, Output
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


def open_db(filename: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_connection = sqlite3.connect(filename)
    cursor = db_connection.cursor()
    return db_connection, cursor


def close_db(connection: sqlite3.Connection):
    connection.commit()
    connection.close()


def create_table(cursor: sqlite3.Cursor):
    cursor.execute("DROP TABLE IF EXISTS jobs ")
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                   company TEXT NOT NULL,
                   company_logo TEXT,
                   company_url TEXT,
                   created_at TEXT NOT NULL,
                   description TEXT,
                   how_to_apply TEXT,
                   id TEXT PRIMARY KEY,
                   location TEXT,
                   title TEXT,
                   type TEXT,
                   url TEXT NOT NULL
                   );''')


def create_location_table(cursor: sqlite3.Cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS location_data (
                   location TEXT PRIMARY KEY NOT NULL,
                   latitude TEXT,
                   longitude TEXT
                   );''')


def insert_jobs(cursor: sqlite3.Cursor, job_responses):
    for job in job_responses:
        cursor.execute(f'''INSERT INTO jobs (company, company_logo, company_url,
                        created_at, description, how_to_apply, id, location, title, type, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (job["company"],
                        job["company_logo"],
                        job["company_url"],
                        job["created_at"],
                        job["description"],
                        job["how_to_apply"],
                        job["id"],
                        job["location"],
                        job["title"],
                        job["type"],
                        job["url"]))


def get_github_api(link):
    job_responses = []
    length = 50
    i = 1

    while length != 0:
        response = requests.get(link + str(i))
        if response.status_code == 200:
            i += 1
            for each in response.json():
                job_responses.append(each)
            length = len(response.json())
    return job_responses


def get_stack_feed(feed):
    job_responses = []
    feed = feedparser.parse(feed)

    for each in feed.entries:
        convert_json = {
            "company": each.author,
            "company_logo": None,
            "company_url": None,
            "created_at": each.published,
            "description": each.summary,
            "how_to_apply": None,
            "id": each.id,
            "location": each.location if 'location' in each else None,
            "title": each.title,
            "type": None,
            "url": each.link
        }
        job_responses.append(convert_json)

    return job_responses


def parse_city(location):
    location_array = re.split(', | or |&|/|-|;|\\|', location)
    final_loc = location_array[0]
    return final_loc


def parse_locations(cursor: sqlite3.Cursor):
    list_location = []
    locations = cursor.execute('''SELECT location FROM jobs WHERE location IS NOT NULL''')
    for location in locations:
        final_location = parse_city(location[0])
        if final_location.strip().lower().split()[0] != 'remote' and final_location not in list_location:
            list_location.append(final_location)
    return list_location


def insert_locations(cursor: sqlite3.Cursor, locations):
    geolocator = Nominatim(user_agent="https://nominatim.openstreetmap.org/search")
    for location in locations:
        cache = cursor.execute(f'''SELECT location FROM location_data WHERE location = ?''', [location])
        if len(cache.fetchall()) == 0:
            limiter = RateLimiter(geolocator.geocode, min_delay_seconds=1)
            parsed_location = limiter(location)
            if parsed_location is not None:
                print(parsed_location.latitude, parsed_location.longitude)
                cursor.execute(f'''INSERT INTO location_data (location, latitude, longitude) VALUES (?, ?, ?)''',
                               (location,
                                parsed_location.latitude,
                                parsed_location.longitude))


def create_job_object(cursor: sqlite3.Cursor):
    job_objects = []
    jobs = cursor.execute('''SELECT * FROM jobs''')
    for job in jobs:
        job_object = {
            "company": job[0],
            "company_logo": job[1],
            "company_url": job[2],
            "created_at": job[3],
            "description": job[4],
            "how_to_apply": job[5],
            "id": job[6],
            "location": job[7] if job[7] is not None else None,
            "title": job[8],
            "type": job[9],
            "url": job[10],
            "latitude": None,
            "longitude": None
        }
        job_objects.append(job_object)
    return job_objects


def join_jobs_and_cache(cursor: sqlite3.Cursor, job_objects):
    for job in job_objects:
        if job["location"] is not None:
            city = parse_city(job["location"])
            if city.lower().split()[0] != 'remote':
                cache_data = cursor.execute(f'''SELECT * FROM location_data WHERE location = ?''', [city])
                info = cache_data.fetchone()
                if info is not None:
                    job["latitude"] = info[1]
                    job["longitude"] = info[2]

    return job_objects


def filter_job_tech(job_objects, job_techs):
    jobs = []
    techs = job_techs.split(",")
    for job in job_objects:
        for tech in techs:
            if tech.strip().lower() in job["description"].lower() and job not in jobs:
                jobs.append(job)
    return jobs


def try_parsing_date(unparsed_date):
    for _ in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
        try:
            return dt.date(dateutil.parser.parse(unparsed_date))
        except ValueError:
            pass


def filter_date(job_objects, start_date):
    jobs = []
    for job in job_objects:
        if try_parsing_date(start_date) < try_parsing_date(job["created_at"]):
            jobs.append(job)
    return jobs


def filter_company(job_objects, company):
    jobs = []
    for job in job_objects:
        if company.lower() in job["company"].lower():
            jobs.append(job)
    return jobs


def filter_job_type(jobs_objects, job_type):
    jobs = []
    if job_type != 'any':
        for job in jobs_objects:
            if job["type"] is None and str(job_type) in job["description"].lower() or str(job_type) == str(
                    job["type"]).lower():
                jobs.append(job)
        return jobs
    else:
        return jobs_objects


def use_map(job_objects):
    mapbox_access_token = "pk.eyJ1IjoiZGFudGVkaWNsZW1lbnRlIiwiYSI6ImNrNzB6dHE1cjAxeGczZ25zcWo1YW9mZWoifQ.AJDlCC171CRF1xDT9rEd0A"

    comp = []
    lat = []
    lon = []

    for job in job_objects:
        if job["location"] is not None and job["latitude"] is not None:
            company_title = job["company"] + ": " + job["title"]
            comp.append(company_title)
            lat.append(job["latitude"])
            lon.append(job["longitude"])

    fig = go.Figure(go.Scattermapbox(
        lat=lat,
        lon=lon,
        text=comp,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10
        ),
    ))

    fig.update_layout(
        title='Jobs from Stack Overflow and GitHub',
        mapbox=dict(
            accesstoken=mapbox_access_token,
        )
    )

    return fig


def create_app_window(fig, job_objects):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div(children=[

        dcc.Graph(figure=fig, id='graph-component', style={
            'height': '90vh'
        }),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ),

        html.Div(children=[
            dcc.Input(
                id='keyword-search',
                placeholder='Enter job keywords, separated by commas',
                type='text',
                value='',
                style={
                    'width': '315px'
                }
            ),
            dcc.Input(
                id='company-search',
                placeholder='Enter company to search',
                type='text',
                value='',
                style={
                    'margin': '0 25',
                    'width': '200px'
                }
            ),
            dcc.DatePickerRange(
                id='date-search',
                min_date_allowed=dt(2019, 1, 1),
                max_date_allowed=date.today(),
                initial_visible_month=date.today(),
                start_date=dt(2020, 2, 1),
                end_date=date.today()
            ),
            dcc.Dropdown(
                id='dropdown-filter',
                options=[
                    {'label': 'Any', 'value': 'any'},
                    {'label': 'Full Time', 'value': 'full time'},
                    {'label': 'Part Time', 'value': 'part time'}
                ],
                value='any',
                searchable=False,
                style={
                    'width': '120px'
                }
            )
        ],
            style={
                'height': '8vh',
                'padding': '0 10vw',
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'space-between'
            }),
        html.Div([
            html.Pre(
                id='click-data',
                style={
                    'width': '100vw',
                    'max-width': '100vw',
                    'word-wrap': 'normal',
                    'color': 'black',
                    'border': '2px solid black'
                }
            ),
        ])
    ],
        style={
            'max-width': '100vw'
        })

    @app.callback(
        Output('graph-component', 'figure'),
        [Input('keyword-search', 'value'), Input('company-search', 'value'), Input('date-search', 'start_date'),
         Input('dropdown-filter', 'value')]
    )
    def update_output(technology, company, start_date, job_type):
        tech_filter = filter_job_tech(job_objects, technology)
        company_filter = filter_company(tech_filter, company)
        date_filter = filter_date(company_filter, start_date)
        job_type_filter = filter_job_type(date_filter, job_type)

        updated_fig = use_map(job_type_filter)

        return updated_fig

    @app.callback(
        Output('click-data', 'children'),
        [Input('graph-component', 'clickData')])
    def display_click_data(click_data):
        if click_data is not None:
            data = click_data["points"][0]
            for job in job_objects:
                if job["latitude"] is not None:
                    company_title = job["company"] + ": " + job["title"]
                    if data["lat"] == job["latitude"] and data["text"] == company_title:
                        full_desc = company_title + "\n" + job["url"] + "\nPOSTED: " + job["created_at"] + \
                                    ", LOCATION: " + job["location"] + "\nDESCRIPTION: " + job["description"]
                        return full_desc

    return app


def main():
    conn, cursor = open_db("Git_Jobs.sqlite")
    print(type(conn))
    create_table(cursor)
    insert_jobs(cursor, get_github_api("https://jobs.github.com/positions.json?page="))
    insert_jobs(cursor, get_stack_feed("https://stackoverflow.com/jobs/feed"))
    create_location_table(cursor)
    insert_locations(cursor, parse_locations(cursor))
    job_objects = join_jobs_and_cache(cursor, create_job_object(cursor))
    app = create_app_window(use_map(job_objects), job_objects)
    close_db(conn)
    app.run_server()


if __name__ == '__main__':
    main()
