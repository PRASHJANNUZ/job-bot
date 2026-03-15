import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import config

jobs = []

headers = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_naukri():

    url = "https://www.naukri.com/java-developer-jobs"

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")

    cards = soup.select("article.jobTuple")

    for job in cards:

        title = job.select_one("a.title").text.strip()
        company = job.select_one(".comp-name").text.strip()
        location = job.select_one(".locWdth").text.strip()
        exp = job.select_one(".expwdth").text.strip()
        link = job.select_one("a.title")["href"]

        if not any(loc in location.lower() for loc in config.LOCATIONS):
            continue

        if not any(k in title.lower() for k in config.KEYWORDS):
            continue

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "exp": exp,
            "link": link,
            "source": "Naukri"
        })


def scrape_indeed():

    url = "https://in.indeed.com/jobs?q=java+developer&l=pune"

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")

    cards = soup.select(".job_seen_beacon")

    for job in cards:

        title = job.select_one("h2").text.strip()
        company = job.select_one(".companyName").text.strip()
        location = job.select_one(".companyLocation").text.strip()

        link = "https://indeed.com" + job.select_one("a")["href"]

        if not any(loc in location.lower() for loc in config.LOCATIONS):
            continue

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "exp": "Check JD",
            "link": link,
            "source": "Indeed"
        })


def remove_duplicates():

    unique = {}

    for job in jobs:
        key = job["title"] + job["company"]

        if key not in unique:
            unique[key] = job

    return list(unique.values())


def generate_email(job_list):

    html = """
    <h2>Java Developer Jobs (Last 72 hrs)</h2>
    <table border="1" cellpadding="10">
    <tr>
    <th>Title</th>
    <th>Company</th>
    <th>Location</th>
    <th>Apply</th>
    </tr>
    """

    for j in job_list:

        html += f"""
        <tr>
        <td>{j['title']}</td>
        <td>{j['company']}</td>
        <td>{j['location']}</td>
        <td><a href="{j['link']}">Apply</a></td>
        </tr>
        """

    html += "</table>"

    return html


def send_email(html):

    msg = MIMEText(html, "html")

    msg["Subject"] = "Daily Java Jobs (1-4 yrs Pune/Hyderabad)"
    msg["From"] = config.EMAIL
    msg["To"] = config.TO_EMAIL

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

    server.login(config.EMAIL, config.PASSWORD)

    server.sendmail(config.EMAIL, config.TO_EMAIL, msg.as_string())

    server.quit()


def main():

    print("Fetching jobs...")

    scrape_naukri()
    scrape_indeed()

    final_jobs = remove_duplicates()

    print("Total jobs:", len(final_jobs))

    html = generate_email(final_jobs)

    send_email(html)


if __name__ == "__main__":
    main()
