import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

import matplotlib.pyplot as plt
import seaborn as sns

import io
import base64

# Generate Publication Trend (Bar Chart)
def generate_publication_trend(publications):
    year_count = {}
    for pub in publications:
        year = pub['year']
        if year in year_count:
            year_count[year] += 1
        else:
            year_count[year] = 1

    # Create a bar chart
    plt.figure(figsize=(8, 6))
    sns.barplot(x=list(year_count.keys()), y=list(year_count.values()))
    plt.title("Publication Trend by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Publications")
    
    # Save the plot as an image and return as base64 string
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_base64 = base64.b64encode(img_stream.getvalue()).decode()
    plt.close()
    return img_base64

# Generate Publication Type Distribution (Pie Chart)
def generate_publication_type_dist(publications):
    journal_count = sum(1 for pub in publications if pub['type'] == 'Journal')
    conference_count = sum(1 for pub in publications if pub['type'] == 'Conference')

    # Create a pie chart
    plt.figure(figsize=(6, 6))
    plt.pie([journal_count, conference_count], labels=["Journals", "Conferences"], autopct='%1.1f%%', startangle=90)
    plt.title("Publication Type Distribution")
    
    # Save the plot as an image and return as base64 string
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_base64 = base64.b64encode(img_stream.getvalue()).decode()
    plt.close()
    return img_base64

