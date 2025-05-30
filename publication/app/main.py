from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import pandas as pd
import mysql.connector
from services.scraping_service import fetch_from_orcid, fetch_from_scholar, fetch_from_dblp
from services.file_service import generate_docx, generate_xlsx
from services.summary_service import  get_faculty_names,filter_publications,generate_summary
from services.visualization_service import generate_publication_trend, generate_publication_type_dist

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection function
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',      
            database='publications_db', 
            user='root',           
            password='Addala@2004'     
        )

        if conn.is_connected():
            print('Connected to the database')
            return conn
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

def store_data_in_db(publications, faculty_details):
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            
            for faculty in faculty_details:
                faculty_name = faculty.get('faculty_name')
                orcid_id = faculty.get('orcid_id')
                scholar_id = faculty.get('scholar_id')
                dblp_id = faculty.get('dblp_id')
                scopus_id = faculty.get('scopus_id')  # Newly added Scopus ID

                # Check if faculty already exists
                cursor.execute("SELECT faculty_id FROM faculty WHERE faculty_name = %s", (faculty_name,))
                faculty_row = cursor.fetchone()

                if faculty_row:
                    faculty_id = faculty_row[0]
                    # Update missing details without overwriting existing valid data
                    cursor.execute("""
                        UPDATE faculty
                        SET orcid_id = COALESCE(%s, orcid_id),
                            scholar_id = COALESCE(%s, scholar_id),
                            dblp_id = COALESCE(%s, dblp_id),
                            scopus_id = COALESCE(%s, scopus_id)
                        WHERE faculty_id = %s;
                    """, (orcid_id, scholar_id, dblp_id, scopus_id, faculty_id))
                else:
                    # Insert new faculty record
                    cursor.execute("""
                        INSERT INTO faculty (faculty_name, orcid_id, scholar_id, dblp_id, scopus_id)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (faculty_name, orcid_id, scholar_id, dblp_id, scopus_id))
                    faculty_id = cursor.lastrowid

                # Insert publication data
                for pub in publications:
                    if pub['faculty_name'] == faculty_name:
                        title = pub['title']
                        year = pub['year']
                        pub_type = pub['type']
                        citation_count = pub['citation_count']

                        cursor.execute("""
                            SELECT COUNT(*) FROM publications WHERE faculty_id = %s AND title = %s AND year = %s
                        """, (faculty_id, title, year))
                        exists = cursor.fetchone()[0]

                        if exists == 0:
                            cursor.execute("""
                                INSERT INTO publications (faculty_id, title, year, type, citation_count)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (faculty_id, title, int(year) if str(year).isdigit() else None, pub_type, citation_count))

            conn.commit()
    except mysql.connector.Error as err:
        print(f"Error inserting data into DB: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Process the Excel file
    publications, faculty_details = process_faculty_file(file_path)

    if not publications:
        return jsonify({'error': 'No publications found'}), 400

    # Save publications to the database
    store_data_in_db(publications,faculty_details)

    # Generate the combined reports
    docx_filename = generate_docx(publications)  # Generate one docx file for all
    xlsx_filename = generate_xlsx(publications)  # Generate one xlsx file for all

    return jsonify({
        'docx': docx_filename,
        'xlsx': xlsx_filename
    })

@app.route('/output')
def output():
    docx_filename = request.args.get('docx')
    xlsx_filename = request.args.get('xlsx')

    if docx_filename and xlsx_filename:
        docx_url = url_for('download_file', filename=os.path.basename(docx_filename))
        xlsx_url = url_for('download_file', filename=os.path.basename(xlsx_filename))
        return render_template('output.html', docx_url=docx_url, xlsx_url=xlsx_url)
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    return send_file(file_path, as_attachment=True)
@app.route('/generate')
def generate():
    faculty_names = get_faculty_names()
    return render_template('generate.html', faculty_names=faculty_names)
@app.route('/visualize')
def visualize():
    faculty_names = get_faculty_names()  # Get the list of faculty names
    return render_template('visualize.html', faculty_names=faculty_names)

def search_faculty(search_type, query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    column_map = {
        "name": "faculty_name",
        "orcid": "orcid_id",
        "scholar_id": "scholar_id",
        "scopus_id": "scopus_id"
    }
    
    column_name = column_map.get(search_type, "faculty_name")  # Default to "faculty_name"

    query_sql = f"""
        SELECT faculty_id, faculty_name, orcid_id, scholar_id, scopus_id
        FROM faculty 
        WHERE {column_name} LIKE %s
    """
    
    cursor.execute(query_sql, (f"%{query}%",))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results

# ✅ API Route for Searching Faculty
@app.route('/search_faculty', methods=['GET'])
def search_faculty_api():
    search_type = request.args.get('search_type')
    query = request.args.get('query', '')

    if not search_type or not query:
        return jsonify([])

    faculty_results = search_faculty(search_type, query)
    return jsonify(faculty_results)

# ✅ API Route for Fetching Publications
@app.route('/fetch_publications', methods=['POST'])
def fetch_publications():
    search_type = request.form['search_type']
    search_query = request.form['search_query']
    start_year = request.form.get('start_year', None)
    end_year = request.form.get('end_year', None)
    publication_type = request.form.get('publication_type', "Both")
    sort_order = request.form.get('sort_order', "ascending")  # Get sorting order

    # Fetch publications from database
    publications = filter_publications(search_type, search_query, start_year, end_year, publication_type,sort_order)

    # ✅ Fetch faculty name from the database to avoid "Unknown Faculty" error
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    column_map = {
        "name": "faculty_name",
        "orcid": "orcid_id",
        "scholar_id": "scholar_id",
        "scopus_id": "scopus_id"
    }
    column_name = column_map.get(search_type, "faculty_name")

    cursor.execute(f"SELECT faculty_name FROM faculty WHERE {column_name} = %s", (search_query,))
    faculty_row = cursor.fetchone()
    cursor.close()
    conn.close()

    faculty_name = faculty_row["faculty_name"] if faculty_row else "Unknown Faculty"

    return jsonify({
        "faculty_name": faculty_name,  # ✅ Now returning the faculty name
        "publications": publications
    })

@app.route('/fetch_visualization_data', methods=['POST'])
def fetch_visualization_data():
    try:
        search_type = request.json.get('search_type')
        search_query = request.json.get('search_query')

        if not search_type or not search_query:
            return jsonify({"error": "Search type and query are required"}), 400

        # Fetch publications from the database
        publications = filter_publications(search_type, search_query)

        if not publications:
            return jsonify({"error": "No publications found"}), 404

        # Generate summary
        # Generate required summary information
        summary = generate_summary(publications)

        # Create visualizations (e.g., publication trends, type distribution, etc.)
        publication_trend = generate_publication_trend(publications)
        publication_type_dist = generate_publication_type_dist(publications)
        

        # Return the summary and visualization data
        return jsonify({
            "summary": summary,  # Now sending the summary!
            "publication_trend": publication_trend,
            "publication_type_dist": publication_type_dist,
            
        })

    except Exception as e:
        print(f"Error in fetching visualization data: {e}")
        return jsonify({"error": "Failed to fetch visualization data"}), 500

       
def process_faculty_file(file_path):
    df = pd.read_excel(file_path)
    all_publications = []
    faculty_details = []
    seen_publications = set()

    for _, row in df.iterrows():
        faculty_name = row.get("Faculty Name", "Unknown")
        orcid = row.get("ORCID", None)
        scholar_id = row.get("Google Scholar ID", None)
        dblp_id = row.get("DBLP ID", None)
        scopus_id = row.get("Scopus ID", None)  # Extracting Scopus ID

        faculty_details.append({
            'faculty_name': faculty_name if pd.notna(faculty_name) else None,
            'orcid_id': orcid if pd.notna(orcid) else None,
            'scholar_id': scholar_id if pd.notna(scholar_id) else None,
            'dblp_id': dblp_id if pd.notna(dblp_id) else None,
            'scopus_id': scopus_id if pd.notna(scopus_id) else None
        })

        publications = []
        if orcid:
            publications += fetch_from_orcid(orcid)
        if scholar_id:
            publications += fetch_from_scholar(scholar_id)
        if dblp_id:
            publications += fetch_from_dblp(dblp_id)

        for pub in publications:
            pub['faculty_name'] = faculty_name
            title = pub.get('title', 'Unknown Title')
            year = pub.get('year')
            if not isinstance(year, int) or pd.isna(year):
                year = None

            publication_key = (title, year)
            if publication_key not in seen_publications:
                seen_publications.add(publication_key)
                all_publications.append(pub)

    return all_publications, faculty_details

if __name__ == "__main__":
    app.run(debug=True, port=5000)