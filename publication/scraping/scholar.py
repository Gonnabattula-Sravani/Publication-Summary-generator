import requests
from bs4 import BeautifulSoup
import re
import itertools
from fuzzywuzzy import fuzz

def generate_all_name_permutations(name):
    """Generate all permutations of name components"""
    parts = name.split()
    permutations = itertools.permutations(parts)
    
    name_variations = set()  # Use set to avoid duplicates
    
    for perm in permutations:
        # Join parts back into a name
        permuted_name = " ".join(perm)
        name_variations.add(permuted_name)
        # Add common formats like Initials and Last Name, First Name
        name_variations.add(f"{perm[0][0]}.{perm[1][0]}. {perm[-1]}")  # Initials + Last Name
        name_variations.add(f"{perm[0]} {perm[1][0]}. {perm[-1]}")  # First + Initials + Last
        name_variations.add(f"{perm[-1]}, {perm[0]} {perm[1][0]}.")  # Last Name, First Initial
        name_variations.add(f"{perm[0][0]}.{perm[1][0]}.{perm[-1]}")  # First Initial + Last Initial + Last
    
    return name_variations

def search_google_scholar(name, affiliation):
    """Search Google Scholar using Google search and variations of name + affiliation"""
    name_variations = generate_all_name_permutations(name)
    search_results = []
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for name_variant in name_variations:
        search_url = f"https://www.google.com/search?q=site:scholar.google.com+{name_variant}+{affiliation}"
        
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all("a", href=True):
            if "scholar.google.com/citations" in link["href"]:
                match = re.search(r"https://scholar.google.com/citations\?user=([\w-]+)", link["href"])
                if match:
                    scholar_id = match.group(1)
                    publication_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
                    search_results.append({
                        "Google Scholar ID": scholar_id,
                        "Google Scholar URL": publication_url
                    })
    
    return search_results

def fetch_publications_from_scholar(scholar_id):
    """Fetch publication details from Google Scholar profile"""
    publications = []
    scholar_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(scholar_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for row in soup.find_all("tr", class_="gsc_a_tr"):
        title = row.find("a", class_="gsc_a_at").text.strip()
        link = "https://scholar.google.com" + row.find("a", class_="gsc_a_at")["href"]
        citation_count = row.find("a", class_="gsc_a_ac").text.strip()
        
        publications.append({
            "Title": title,
            "Link": link,
            "Citations": citation_count
        })
    
    return publications

def get_google_scholar_details(name, affiliation):
    """Fetch Google Scholar profile and publications"""
    scholar_profiles = search_google_scholar(name, affiliation)
    
    all_publications = []
    
    for profile in scholar_profiles:
        scholar_id = profile.get("Google Scholar ID")
        if scholar_id:
            publications = fetch_publications_from_scholar(scholar_id)
            all_publications.extend(publications)
    
    return all_publications

def fuzzy_name_match(name, scholar_name):
    """Match the input name with the name from Google Scholar using fuzzy matching"""
    return fuzz.partial_ratio(name.lower(), scholar_name.lower()) > 80  # 80% similarity threshold

# Input from user
name = input("Enter Name: ")  # Example: Mahaboob Hussain Shaik
affiliation = input("Enter Affiliation: ")  # Example: Stanford University

publications = get_google_scholar_details(name, affiliation)

# Display the publications
if publications:
    for pub in publications:
        print(f"Title: {pub['Title']}, Link: {pub['Link']}, Citations: {pub['Citations']}")
else:
    print("No publications found.")
