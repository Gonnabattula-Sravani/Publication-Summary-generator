document.getElementById('search-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const facultyName = document.getElementById('faculty-name').value;
    const orcid = document.getElementById('orcid').value;
    const publicationType = document.getElementById('publication-type').value;
    const year = document.getElementById('year').value;

    const requestData = {
        faculty_name: facultyName,
        orcid: orcid,
        publication_type: publicationType,
        year: year
    };

    fetch('/search_publications', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
    })
    .then(response => response.json())
    .then(data => {
        const publicationList = document.getElementById('publication-list');
        publicationList.innerHTML = ''; // Clear previous results

        if (data.length > 0) {
            data.forEach(publication => {
                const li = document.createElement('li');
                li.innerHTML = `${publication.title} - ${publication.year} (Type: ${publication.type})`;
                publicationList.appendChild(li);
            });
        } else {
            publicationList.innerHTML = '<li>No publications found.</li>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching publications.');
    });
});
