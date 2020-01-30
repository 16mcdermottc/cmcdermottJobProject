import requests
import json


def get_api():
    job_responses = []
    length = 50
    i = 1

    while length != 0:
        response = requests.get("https://jobs.github.com/positions.json?page=" + str(i))
        i += 1

        for each in response.json():
            job_responses.append(json.dumps(each, sort_keys=True, indent=4))

        length = len(response.json())

    file = open("jobList.txt", "w+")

    for each in job_responses:
        file.write(each)
        print(each)

    return job_responses
