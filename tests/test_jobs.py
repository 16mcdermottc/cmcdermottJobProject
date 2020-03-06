import sqlite3
import jobs

DATABASE = "Git_Jobs.sqlite"


def test_api_length():
    job_list = jobs.get_github_api("https://jobs.github.com/positions.json?page=")
    assert len(job_list) > 100


def test_stack_length():
    job_list = jobs.get_stack_feed("https://stackoverflow.com/jobs/feed")
    assert len(job_list) > 100


def test_job_listing():
    conn, cursor = jobs.open_db(DATABASE)
    cursor.execute("SELECT * FROM jobs WHERE company = 'Salesforce'")
    check_data = cursor.fetchone()
    jobs.close_db(conn)
    assert check_data is not None


def test_table_exists():
    conn, cursor = jobs.open_db(DATABASE)
    cursor.execute("SELECT * FROM jobs")
    check_data = cursor.fetchone()
    jobs.close_db(conn)
    assert check_data is not None


def test_good_git_data():
    job = [{
        "company": "test_company",
        "company_logo": "test_logo",
        "company_url": "test_url",
        "created_at": "test_creation",
        "description": "test_description",
        "how_to_apply": "test_apply",
        "id": "test_id",
        "location": "test_location",
        "title": "test_title",
        "type": "test_type",
        "url": "test_url"
    }]
    conn, cursor = jobs.open_db(DATABASE)
    jobs.insert_jobs(cursor, job)
    cursor.execute("SELECT * FROM jobs WHERE company = 'test_company'")
    check_data = cursor.fetchone()
    cursor.execute("DELETE FROM jobs WHERE company = 'test_company'")
    jobs.close_db(conn)
    assert check_data is not None


def test_good_stack_data():
    feed = '''<?xml version="1.0" encoding="utf-8"?>
    <rss xmlns:a10="http://www.w3.org/2005/Atom" version="2.0">
    <channel xmlns:os="http://a9.com/-/spec/opensearch/1.1/">
    <item>
        <guid isPermaLink="false">test_id</guid>
        <link>test_link</link>
        <a10:author><a10:name>test_company</a10:name></a10:author>
        <title>test_title</title>
        <description>test_description</description>
        <pubDate>test_date</pubDate><a10:updated>test_update</a10:updated>
        <location>test_location</location>
    </item></channel></rss>'''
    conn, cursor = jobs.open_db(DATABASE)
    jobs.insert_jobs(cursor, jobs.get_stack_feed(feed))
    cursor.execute("SELECT * FROM jobs WHERE company = 'test_company'")
    check_data = cursor.fetchone()
    cursor.execute("DELETE FROM jobs WHERE company = 'test_company'")
    jobs.close_db(conn)
    assert check_data is not None


def test_bad_git_data():
    bad_job = [{
        "company": "test_company",
        "company_logo": "test_logo",
        "company_url": "test_url",
        "created_at": None,
        "description": "test_description",
        "how_to_apply": "test_apply",
        "id": None,
        "location": "test_location",
        "title": "test_title",
        "type": "test_type",
        "url": "test_url"
    }]
    conn, cursor = jobs.open_db(DATABASE)
    try:
        jobs.insert_jobs(cursor, bad_job)
    except sqlite3.IntegrityError:
        jobs.close_db(conn)
        assert True
    else:
        assert False


def test_bad_stack_data():
    bad_feed = '''<?xml version="1.0" encoding="utf-8"?>
    <rss xmlns:a10="http://www.w3.org/2005/Atom" version="2.0">
    <channel xmlns:os="http://a9.com/-/spec/opensearch/1.1/">
    <item>
        <link>test_link</link>
        <a10:author><a10:name>test_company</a10:name></a10:author>
        <title>test_title</title>
        <description>test_description</description>
        <pubDate>tet_date</pubDate>
        <a10:updated>test_updated</a10:updated>
    </item></channel></rss>'''

    conn, cursor = jobs.open_db(DATABASE)
    try:
        jobs.insert_jobs(cursor, jobs.get_stack_feed(bad_feed))
    except sqlite3.IntegrityError:
        jobs.close_db(conn)
        assert True
    except AttributeError:
        jobs.close_db(conn)
        assert True
    else:
        assert False


def test_null_primary_keys():
    conn, cursor = jobs.open_db(DATABASE)
    cursor.execute("SELECT * FROM jobs WHERE id = NULL")
    check_data = cursor.fetchone()
    jobs.close_db(conn)
    assert check_data is None


def test_job_tech():
    conn, cursor = jobs.open_db(DATABASE)
    job_objects = jobs.join_jobs_and_cache(cursor, jobs.create_job_object(cursor))
    test_filter = "python"
    tech_filter = jobs.filter_job_tech(job_objects, test_filter)
    jobs.close_db(conn)
    if len(tech_filter) > 0:
        assert True
    else:
        assert False


def test_company():
    conn, cursor = jobs.open_db(DATABASE)
    job_objects = jobs.join_jobs_and_cache(cursor, jobs.create_job_object(cursor))
    test_filter = "Salesforce"
    company_filter = jobs.filter_company(job_objects, test_filter)
    jobs.close_db(conn)
    if len(company_filter) > 0:
        assert True
    else:
        assert False


def test_job_type():
    conn, cursor = jobs.open_db(DATABASE)
    job_objects = jobs.join_jobs_and_cache(cursor, jobs.create_job_object(cursor))
    test_filter = "full time"
    job_type_filter = jobs.filter_job_type(job_objects, test_filter)
    jobs.close_db(conn)
    if len(job_type_filter) > 0:
        assert True
    else:
        assert False


def test_date():
    conn, cursor = jobs.open_db(DATABASE)
    job_objects = jobs.join_jobs_and_cache(cursor, jobs.create_job_object(cursor))
    test_filter = "2020-01-01"
    job_date_filter = jobs.filter_date(job_objects, test_filter)
    jobs.close_db(conn)
    if len(job_date_filter) > 0:
        assert True
    else:
        assert False


def test_check_data():
    conn, cursor = jobs.open_db(DATABASE)
    job_objects = jobs.join_jobs_and_cache(cursor, jobs.create_job_object(cursor))
    data = {
        "points": [
            {
                "curveNumber": 0,
                "pointNumber": 3,
                "pointIndex": 3,
                "lon": "-71.0582912",
                "lat": "42.3602534",
                "text": "Salesforce: DevOps Engineers All Levels (Senior/Lead/Principal) (Multiple Locations) at Salesforce (Boston, MA)"
            }
        ]
    }
    jobs.close_db(conn)
    check = jobs.check_data(job_objects, data)
    assert check is not None
