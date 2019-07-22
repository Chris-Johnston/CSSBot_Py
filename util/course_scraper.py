"""
Course Scraper util

Scrapes MyPlan and gets a complete JSON for all of the courses.
Currently only will scrape for a single campus.
"""

import requests
import json
import time
import random

BASE_URL = 'https://myplan.uw.edu'

cookies = {
    "auth-provider": "washington.edu",
    # lol what is this cookie name
    "bbbbbbbbbbbbbbb": "xxx",
    "JSESSIONID": "xxx",
    "myplan.preferred_campus": "bothell" # dunno if this is used for the search, don't think so
}

request_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/javascript"
}

search_payload = {
    "days": [],
    "instructorSearch": False,
    "startTime": "0630",
    "endTime": "2230",
    "sectionSearch": True,
    "campus": "bothell", # defaults to "seattle"
}

def get_subject_areas():
    """
    GETs /course/api/subjectAreas for the list of course codes to search.
    """
    result = requests.get(BASE_URL + '/course/api/subjectAreas', cookies=cookies)
    result.raise_for_status()
    return result

def search_subject(subject_code: str):
    """
    POSTs /course/api/courses with request JSON for a given subject.
    """
    print('Scraping course:', subject_code)
    search_payload["queryString"] = subject_code
    # master hacker strats
    time.sleep(random.randint(2, 10))
    
    result = requests.post(BASE_URL + '/course/api/courses', cookies=cookies, json=search_payload, headers=request_headers)
    result.raise_for_status()

    return result

if __name__ == "__main__":
    subject_areas = get_subject_areas().json() 
    print(json.dumps(subject_areas, indent=2, sort_keys=True))

    codes = []
    for subject in subject_areas:
        codes.append(subject["codeNoSpaces"])
    print(codes)

    courses = []
    print("Scraping...")
    for code in codes:
        subject = search_subject(code).json()
        courses.extend(subject)

        print("Current # of courses:", len(courses))

        # pretty print
        # print(json.dumps(subject.json(), indent=2, sort_keys=True))
    
    print(f"Done. Got {len(courses)} courses.")

    with open("courses_out.json", "w") as f:
        json.dump(courses, f)

    print("Wrote file.")