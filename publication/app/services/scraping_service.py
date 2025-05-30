import requests
from bs4 import BeautifulSoup
from scholarly import scholarly
import re
import time

import requests
ACCESS_TOKEN = '4a9f19f5-fcce-4fef-8724-dea4d46df390' 

def fetch_from_orcid(orcid):
    """Fetch publications from ORCID using the orcid."""
    works_url = f'https://pub.orcid.org/v3.0/{orcid}/works'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Accept': 'application/json'
    }

    seen_publications = set()
    publications = []

    response = requests.get(works_url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        for work in data.get('group', []):
            for work_summary in work.get('work-summary', []):
                title = work_summary.get('title', {}).get('title', {}).get('value', 'No Title')
                publication_year = 'No Year'
                publication_date = work_summary.get('publication-date', {})

                if publication_date and 'year' in publication_date:
                    publication_year = publication_date['year'].get('value', 'No Year')

                publication_identifier = f"{title} - {publication_year}"

                if publication_identifier in seen_publications:
                    continue

                seen_publications.add(publication_identifier)

                publication_type = work_summary.get('type', 'No Type')
                if 'journal' in publication_type.lower():
                    publication_type = 'Journal'
                elif 'conference' in publication_type.lower():
                    publication_type = 'Conference'
                else:
                    publication_type = 'Other'

                # Extract DOI if available
                external_ids = work_summary.get('external-ids', {}).get('external-id', [])
                doi = None
                for ext_id in external_ids:
                    if ext_id.get('external-id-type') == 'doi':
                        doi = ext_id.get('external-id-value')
                        break

                # Fetch citation count (0 if DOI is missing)
                citation_Count = fetch_citation_count(doi) if doi else 0

                publication_data = {
                    'title': title,
                    'year': publication_year,
                    'type': publication_type,
                    'citation_count': citation_Count
                }

                publications.append(publication_data)
    else:
        print(f"Error retrieving publications. Status code: {response.status_code}")

    # Return an empty list if no publications found instead of None
    return publications

def fetch_citation_count(doi):
    """Fetch citation count from CrossRef API using DOI."""
    if not doi:
        return 0  # Return 0 if DOI is not available

    crossref_url = f"https://api.crossref.org/works/{doi}"

    try:
        response = requests.get(crossref_url)
        if response.status_code == 200:
            data = response.json()
            citation_count = data.get("message", {}).get("is-referenced-by-count", 0)
            return citation_count
    except requests.exceptions.RequestException:
        return 0  # Return 0 if there is an error in fetching citation count

    return 0  # Default to 0 if citation count is not found
 

def classify_citation(citation):
    if re.search(r'(Proceedings|International Conference|IEEE|ACM|Springer|Workshop|World Conference|Symposium)', citation, re.IGNORECASE):
        return "Conference"
    
    journal_patterns = [
        r'(Journal|Transactions|Review|Studies|Letters)',
        r'\d{1,3}\s?\(\d{1,2}\)',  
        r'\bvol\.?\s?\d{1,3}',  
        r'(Elsevier|Springer|Wiley|Taylor & Francis|Sage)',  
        r'\bDOI\b',  
        r'ISSN',  
    ]
    
    for pattern in journal_patterns:
        if re.search(pattern, citation, re.IGNORECASE):
            return "Journal"
    
    return "Other"

def fetch_from_scholar(scholarId):
    if not scholarId or not isinstance(scholarId, str):
        print(f"❌ Invalid scholarId: {scholarId}")
        return []

    try:
        # ✅ Step 2: Check if the scholarId exists in Google Scholar
        author = scholarly.search_author_id(scholarId)
        if not author:
            print(f"❌ No author found for Scholar ID: {scholarId}")
            return []

        # ✅ Step 3: Fetch author details
        author_filled = scholarly.fill(author)
    
    except Exception as e:
        print(f"❌ Error fetching data from Google Scholar: {e}")
        return []

    structured_publications = []
    for pub in author_filled.get('publications', []):
        title = pub.get("bib", {}).get("title", "No Title")
        year = pub.get("bib", {}).get("pub_year", "No Year")
        citation = pub.get("bib", {}).get("citation", "No Citation")
        pub_type = classify_citation(citation)
        
        citation_count = pub.get("num_citations", 0)

        structured_publications.append({
                "title": title,
                "year": year,
                "type": pub_type,
                "citation_count": citation_count
            })

    return structured_publications

def fetch_from_dblp(dblpId):
    url = f'https://dblp.org/pid/{dblpId}.xml'
    publications_list = []

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            publications = soup.find_all(['article', 'inproceedings'])

            for pub in publications:
                title = pub.find('title').text if pub.find('title') else 'No Title'
                year = pub.find('year').text if pub.find('year') else 'No Year'

                pub_category = 'Conference' if pub.find('booktitle') else 'Journal'
                publication_data = {
                    'title': title,
                    'year': int(year) if year.isdigit() else 'No Year',
                    'type': pub_category
                }
                publications_list.append(publication_data)
            
            publications_list.sort(key=lambda x: x['year'], reverse=True)
        else:
            print(f"Failed to fetch data. HTTP Status code: {response.status_code}")

    except requests.exceptions.Timeout:
        print('The request timed out.')
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return publications_list