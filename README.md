# VillageFinder Web

A Flask web version of the uploaded `VillageFinder_trov.py` using the uploaded NCDD CSV dataset.

## Run on Windows

1. Install Python 3.10+.
2. Open Command Prompt in this folder.
3. Run:
   ```
   py -m pip install -r requirements.txt
   py app.py
   ```
4. Open `http://127.0.0.1:5000` in your browser.

The app keeps the core logic from the original Python script:
- Detects province from NCDD codes / province headers.
- Detects district type: ស្រុក / ក្រុង / ខណ្ឌ.
- Detects commune type: ឃុំ / សង្កាត់.
- Flattens village records into searchable records.
- Searches Khmer or English text and codes.
- Generates the Khmer administrative address.

## Main files

- `app.py` — Flask backend and NCDD processing logic
- `templates/index.html` — website page
- `static/style.css` — visual design
- `static/app.js` — search interaction
- `ncdd_admin_database.csv` — uploaded NCDD dataset
