import mysql.connector
import numpy as np  
# Database connection function
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',       # your MySQL host
            database='publications_db',  # your database name
            user='root',            # your MySQL username
            password='Addala@2004'     # your MySQL password
        )

        if conn.is_connected():
            print('Connected to the database')
            return conn
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

def filter_publications(search_type, search_query, start_year=None, end_year=None, pub_type=None, sort_order="ascending"):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)  # Fetch results as dictionaries

    column_map = {
        "name": "faculty_name",
        "orcid": "orcid_id",
        "scholar_id": "scholar_id",
        "scopus_id": "scopus_id"
    }
    column_name = column_map.get(search_type, "faculty_name")

    # ✅ Step 1: Fetch faculty_id first
    cursor.execute(f"SELECT faculty_id FROM faculty WHERE {column_name} = %s", (search_query,))
    faculty_row = cursor.fetchone()

    if not faculty_row:
        cursor.close()
        conn.close()
        return []  # ✅ Return empty list if faculty not found

    faculty_id = faculty_row["faculty_id"]

    # ✅ Step 2: Fetch publications using faculty_id
    query = """
        SELECT p.publication_id, p.title, p.year, p.type, p.citation_count, f.faculty_name 
        FROM publications p 
        JOIN faculty f ON p.faculty_id = f.faculty_id
        WHERE p.faculty_id = %s
    """
    filters = [faculty_id]

    if start_year:
        query += " AND p.year >= %s"
        filters.append(int(start_year))
    
    if end_year:
        query += " AND p.year <= %s"
        filters.append(int(end_year))
    
    if pub_type and pub_type != "Both":
        query += " AND p.type = %s"
        filters.append(pub_type)
    
    if sort_order.lower() == "ascending":
        query += " ORDER BY p.year ASC"
    else:
        query += " ORDER BY p.year DESC"

    cursor.execute(query, tuple(filters))
    publications = cursor.fetchall()

    cursor.close()
    conn.close()
    return publications


import numpy as np  # Add this at the top

import numpy as np

def generate_summary(publications):
    total_publications = len(publications)
    total_journals = sum(1 for pub in publications if pub.get('type') == "Journal")
    total_conferences = sum(1 for pub in publications if pub.get('type') == "Conference")
    total_citation_count = sum(pub.get('citation_count', 0) for pub in publications if pub.get('citation_count') is not None)

    year_count = {}
    for pub in publications:
        year = pub.get('year')  # Get the publication year

        if isinstance(year, (int, float)) and year is not None:  # ✅ Ensure valid year
            if not np.isnan(year):  # ✅ Ensure it's not NaN
                year = int(year)  # ✅ Convert to integer
                year_count[year] = year_count.get(year, 0) + 1

    most_active_year = max(year_count, key=year_count.get) if year_count else None

    # ✅ Safely filter out None values for sorting
    valid_years = [pub.get('year') for pub in publications if pub.get('year') is not None]
    publication_trend = {year: year_count[year] for year in sorted(valid_years)}

    # Top 5 most cited papers
    top_cited = sorted(publications, key=lambda x: x.get('citation_count', 0), reverse=True)[:5]
    recent_publications = sorted(publications, key=lambda x: x.get('year', 0) if x.get('year') is not None else 0, reverse=True)[:5]
    
    # Get the most cited paper, ensuring the correct title and citation count
    highest_cited_paper = max(publications, key=lambda x: x.get('citation_count', 0), default={"title": "No Data", "citation_count": 0})
    
    # Calculate average citations and round it to the nearest integer
    avg_citations = round(total_citation_count / total_publications) if total_publications > 0 else 0

    return {
        "total_publications": total_publications,
        "total_journals": total_journals,
        "total_conferences": total_conferences,
        "total_citation_count": total_citation_count,
        "most_active_year": most_active_year,
        "highest_cited_paper": {"title": highest_cited_paper["title"], "citation_count": highest_cited_paper["citation_count"]},
        "avg_citations": avg_citations,
        "top_cited": [{"title": pub.get('title', 'Unknown'), "year": pub.get('year', 'Unknown'), "citation_count": pub.get('citation_count', 0)} for pub in top_cited],
        "publication_trend": publication_trend,
        "recent_publications": [{"title": pub.get('title', 'Unknown'), "year": pub.get('year', 'Unknown')} for pub in recent_publications],
    }

def get_faculty_names():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT faculty_name FROM faculty")
    faculty_names = [faculty[0] for faculty in cursor.fetchall()]
    cursor.close()
    conn.close()
    return faculty_names