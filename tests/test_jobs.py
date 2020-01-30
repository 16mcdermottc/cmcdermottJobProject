import jobs
import os.path


def test_api_length():
    joblist = jobs.get_api()
    assert len(joblist) > 100


def test_job_listing():
    flag = False
    file = open(os.path.dirname(__file__) + '/../jobList.txt', "r")
    for line in file:
        if 'SkillValue' in line:
            flag = True
    assert flag
    file.close()
