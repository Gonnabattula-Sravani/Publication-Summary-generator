import requests
from scholarly import scholarly
import re

def classify_citation(citation):
    """Classify the publication type based on its citation."""
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

def fetch_from_scholar(scholar_id):
    """Fetch publications from Google Scholar using the scholar_id."""
    try:
        author = scholarly.search_author_id(scholar_id)
        author_filled = scholarly.fill(author)

        structured_publications = []

        for pub in author_filled.get('publications', []):
            title = pub.get("bib", {}).get("title", "No Title")
            year = pub.get("bib", {}).get("pub_year", "No Year")
            citation = pub.get("bib", {}).get("citation", "No Citation")
            pub_type = classify_citation(citation)

            # Extract citation count (default to 0 if not found)
            citation_count = pub.get("num_citations", 0)

            structured_publications.append({
                "title": title,
                "year": year,
                "type": pub_type,
                "citation_count": citation_count
            })

        return structured_publications

    except Exception as e:
        print(f"Error fetching data from Google Scholar: {e}")
        return []

# Example usage:
scholar_id = input("Enter Google Scholar ID: ")
publications = fetch_from_scholar(scholar_id)

for pub in publications:
    print(f"Title: {pub['title']}")
    print(f"Year: {pub['year']}")
    print(f"Type: {pub['type']}")
    print(f"Citation Count: {pub['citation_count']}")
    print("-" * 50)
