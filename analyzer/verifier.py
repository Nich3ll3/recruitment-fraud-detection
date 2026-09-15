import os

from dotenv import load_dotenv
from tavily import TavilyClient
from urllib.parse import urlparse

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def verify_company(company_name):

    response = client.search(
        company_name,
        max_results=5
    )

    sources = []

    company_words = set(
        company_name.lower().replace(",", "").split()
    )

    for result in response["results"]:

        text = (
            result["title"] + " " +
            result["content"]
        ).lower()

        matched_words = [
            word
            for word in company_words
            if len(word) > 2 and word in text
        ]

        if company_name.lower() in text:
            match_type = "name_match"

        elif len(matched_words) >= 2:
            match_type = "partial_match"

        else:
            match_type = "related"

        sources.append({
            "title": result["title"],
            "url": result["url"],
            "content": result["content"],
            "match_type": match_type
        })

    exact_matches = [
        source
        for source in sources
        if source["match_type"] == "name_match"
    ]

    return {
        "company": company_name,
        "exact_match_found": len(exact_matches) > 0,
        "sources": sources
    }

def verify_url(url):
    if not url:
        return {
            "status": "not_provided",
            "url": "",
            "domain": "",
            "evidence": []
        }

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Search for information about the domain
    response = client.search(
    f"official website {domain}",
    max_results=5
    )   

    evidence = []

    for result in response["results"]:
        title = result["title"]
        result_url = result["url"]
        content = result["content"]

        combined_text = (
            title + " " +
            result_url + " " +
            content
        ).lower()

        result_domain = urlparse(result_url).netloc.lower()

        if result_domain == domain or result_domain.endswith("." + domain):
            match_type = "source_domain_match"
        elif domain in combined_text:
            match_type = "domain_mentioned"
        else:
            match_type = "related"

        evidence.append({
            "title": title,
            "url": result_url,
            "content": content,
            "match_type": match_type
        })

    return {
        "status": "provided",
        "url": url,
        "domain": domain,
        "evidence": evidence
    }