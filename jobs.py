import requests
import sqlite3
from typing import Tuple
import feedparser


def open_db(filename: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_connection = sqlite3.connect(filename)
    cursor = db_connection.cursor()
    return db_connection, cursor


def close_db(connection: sqlite3.Connection):
    connection.commit()
    connection.close()


def create_table(cursor: sqlite3.Cursor):
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


def insert_jobs(cursor: sqlite3.Cursor, job_responses):
    for job in job_responses:
        cursor.execute(f'''INSERT OR REPLACE INTO jobs (company, company_logo, company_url,
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


def main():
    conn, cursor = open_db("Git_Jobs.sqlite")
    print(type(conn))
    cursor.execute("DROP TABLE jobs")
    create_table(cursor)
    insert_jobs(cursor, get_github_api("https://jobs.github.com/positions.json?page="))
    insert_jobs(cursor, get_stack_feed("https://stackoverflow.com/jobs/feed"))
    close_db(conn)


if __name__ == '__main__':
    main()
