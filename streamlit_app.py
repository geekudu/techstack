import json
from bs4 import BeautifulSoup
import re
import streamlit as st
from typing import Dict, List
from scrapfly import ScrapeConfig, ScrapflyClient
import os

TECHNOLOGIES = [
    "React",
    "HTML",
    "CSS",
    "JavaScript",
    "Python",
    "Django",
    "Java",
    "Spring",
    "Laravel",
    "PHP",
    "Angular",
    "Vue.js",
    "Node.js",
    "Express.js",
    "Ruby on Rails",
    "C#",
    "ASP.NET",
    "C++",
    "Go",
    "Kotlin",
    "Swift",
    "Objective-C",
    "TypeScript",
    "SQL",
    "MongoDB",
    "PostgreSQL",
    "MySQL",
    "SQLite",
    "Redis",
    "GraphQL",
    "Apache",
    "Nginx",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Puppet",
    "Chef",
    "Flask",
    "FastAPI",
    "Bootstrap",
    "Tailwind CSS",
    "Sass",
    "LESS",
    "Webpack",
    "Babel",
    "Gulp",
    "Jenkins",
    "Git",
    "GitHub",
    "GitLab",
    "Bitbucket",
    "JIRA",
    "Confluence",
    "Jupyter Notebook",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Pandas",
    "NumPy",
    "Matplotlib",
    "Seaborn",
    "Hadoop",
    "Spark",
    "AWS",
    "Azure",
    "Google Cloud Platform",
    "Firebase"
]

# Initialize Scrapfly client
SCRAPFLY_KEY =  os.getenv('SCRAPFLY')
scrapfly = ScrapflyClient(key=SCRAPFLY_KEY)

# Base configuration for scraping
BASE_CONFIG = {
    "asp": True,  # Bypass scraping protection
    "headers": {
        "Accept-Language": "en-US,en;q=0.5"
    }
}

def strip_text(text):
    """Remove extra spaces while handling None values"""
    return text.strip() if text is not None else text

def parse_jobs(response) -> List[Dict]:
    """Parse job listings from LinkedIn"""
    selector = response.selector
    jobs = []
    for element in selector.xpath("//ul[contains(@class, 'jobs-search__results-list')]/li"):
        try:
            link = element.xpath(".//a[contains(@class, 'base-card__full-link')]")
            post_url = link.attrib.get('href', None)
            job_info = {}
            job_title = element.xpath(".//h3/text()").get()
            company_name = element.xpath(".//h4[contains(@class, 'base-search-card__subtitle')]/a/text()").get().strip()
            location = element.xpath(".//span[@class='job-search-card__location']/text()").get()

            job_info["job_title"] = job_title.strip() if job_title else None
            job_info["company_name"] = company_name.strip() if company_name else None
            job_info["location"] = location.strip() if location else None
            job_info["link"] = post_url
            jobs.append(job_info)
        except Exception as e:
            pass
    return jobs

def scrape_job_postings(company_page: str) -> List[Dict]:
    """Scrape LinkedIn job postings for a specific company"""
    url = f"https://in.linkedin.com/jobs/{company_page}-jobs"
    to_scrape = ScrapeConfig(url, **BASE_CONFIG)
    response = scrapfly.scrape(to_scrape)
    jobs_data = parse_jobs(response)
    return jobs_data

def scrape_posts(jobs_data: List[Dict]) -> List[str]:
    """Scrape job details from the job post URLs"""
    mentioned_techs = set()
    for item in jobs_data:
        to_scrape = ScrapeConfig(item["link"], **BASE_CONFIG)
        response = scrapfly.scrape(to_scrape)
        html_content = response.content

        soup = BeautifulSoup(html_content, "html.parser")
        script_tag = soup.find("script", type="application/ld+json")
        json_ld_content = script_tag.string if script_tag else None

        if json_ld_content:
            job_posting = json.loads(json_ld_content)
            description_html = job_posting.get("description", "")
            description = BeautifulSoup(description_html, "html.parser").get_text()

            extracted_technologies = extract_technologies(description)
            mentioned_techs.update(extracted_technologies)
    
    return list(mentioned_techs)

def extract_technologies(text):
    """Extract mentioned technologies from job descriptions"""
    mentioned_techs = []
    for tech in TECHNOLOGIES:
        if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE):
            mentioned_techs.append(tech)
    return mentioned_techs

# Streamlit app code
def main():
    st.title("LinkedIn Job Scraper for Technologies")

    # User input: Company name
    company_page = st.text_input("Enter the company name (e.g., 'myntra'):")

    if company_page:
        # Scrape job postings
        with st.spinner('Scraping job postings...'):
            job_data = scrape_job_postings(company_page)

        # Scrape technologies from job descriptions
        if job_data:
            with st.spinner('Scraping job descriptions and extracting technologies...'):
                techs = scrape_posts(job_data)

            st.subheader("Technologies mentioned in job postings")
            if techs:
                st.write(", ".join(techs))
            else:
                st.write("No technologies mentioned in the job postings.")

if __name__ == "__main__":
    main()
