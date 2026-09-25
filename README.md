# GPS-style Photo Overlay Maker

## Streamlit deployment

Upload these files to your Streamlit app/repository:

- app.py
- requirements.txt
- gps.jpeg
- map.jpeg

Then run:

streamlit run app.py

The supplied `gps.jpeg` and `map.jpeg` are used as fixed template graphics.
Only date and time are editable.

The output contains a small `EDITED` marker because the timestamp is manually
entered rather than being a verified camera timestamp.
