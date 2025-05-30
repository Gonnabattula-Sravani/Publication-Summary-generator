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
                citation_count = fetch_citation_count(doi) if doi else 0

                publication_data = {
                    'title': title,
                    'year': publication_year,
                    'type': publication_type,
                    'citations': citation_count
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
