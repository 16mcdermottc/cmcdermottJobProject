import sqlite3
import jobs


def test_api_length():
    job_list = jobs.get_api()
    assert len(job_list) > 100


def test_job_listing():
    conn, cursor = jobs.open_db("Git_Jobs.sqlite")
    cursor.execute("SELECT * FROM jobs WHERE company = 'SkillValue'")
    assert cursor.fetchone() is not None
    jobs.close_db(conn)


def test_table_exists():
    conn, cursor = jobs.open_db("Git_Jobs.sqlite")
    cursor.execute("SELECT * FROM jobs")
    assert cursor.fetchone() is not None
    jobs.close_db(conn)


def test_good_data():
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
    conn, cursor = jobs.open_db("Git_Jobs.sqlite")
    jobs.insert_jobs(cursor, job)
    cursor.execute("SELECT * FROM jobs WHERE company = 'test_company'")
    assert cursor.fetchone() is not None
    cursor.execute("DELETE FROM jobs WHERE company = 'test_company'")
    jobs.close_db(conn)


def test_bad_data():
    job = [{
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
    conn, cursor = jobs.open_db("Git_Jobs.sqlite")
    try:
        jobs.insert_jobs(cursor, job)
    except sqlite3.IntegrityError:
        assert True
    else:
        assert False
    cursor.execute("DELETE FROM jobs WHERE company = 'test_company'")
    jobs.close_db(conn)


def test_null_primary_keys():
    conn, cursor = jobs.open_db("Git_Jobs.sqlite")
    cursor.execute("SELECT * FROM jobs WHERE id = NULL")
    assert cursor.fetchone() is None
    jobs.close_db(conn)
