import requests

ACCESS_TOKEN = '4a9f19f5-fcce-4fef-8724-dea4d46df390'  # Replace with your actual access token

def get_publications(orcid):
    works_url = f'https://pub.orcid.org/v3.0/{orcid}/works'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Accept': 'application/json'
    }

    seen_publications = set()
    publications = []
    url = works_url

    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()

            for work in data.get('group', []):
                for work_summary in work.get('work-summary', []):
                    put_code = work_summary.get('put-code')
                    title = work_summary.get('title', {}).get('title', {}).get('value', 'No Title')
                    publication_year = 'No Year'
                    publication_date = work_summary.get('publication-date', {})

                    if publication_date and 'year' in publication_date:
                        publication_year = publication_date['year'].get('value', 'No Year')

                    publication_identifier = f"{title} - {publication_year}"

                    # Skip duplicates
                    if publication_identifier in seen_publications:
                        continue
                    
                    seen_publications.add(publication_identifier)

                    publication_type = work_summary.get('type', 'No Type')
                    if 'journal' in publication_type.lower():
                        publication_type = 'Journal'
                    elif 'conference' in publication_type.lower():
                        publication_type = 'Conference'
                    else:
                        publication_type = 'Other'  # Including 'Other' to capture other publication types

                    publication_data = {
                        'title': title,
                        'year': publication_year,
                        'type': publication_type
                    }

                    publications.append(publication_data)

            url = data.get('links', {}).get('next', None)
        else:
            print(f"Error retrieving publications. Status code: {response.status_code}")
            break

    return publications if publications else None
