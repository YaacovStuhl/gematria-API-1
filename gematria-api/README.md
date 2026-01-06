# Gematria API (Flask + Postgres)

## Local development

This app reads the database connection from the environment variable **`DATABASE_URL`**.

Example (local Postgres):

`postgresql://postgres:YOUR_PASSWORD@localhost:5432/gematria`

### PyCharm setup

- Set the interpreter to: `gematria-api/venv/Scripts/python.exe`
- Run `run.py`
- In the run configuration, add environment variable:
  - `DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/gematria`

Swagger UI: `/swagger-ui`  
OpenAPI JSON: `/openapi.json`

## Importing words from Sefaria (optional)

This uses Sefaria’s API to fetch Hebrew text, extracts unique Hebrew “words”, computes gematria for each, and upserts into your DB via:

- `PUT /entries/by-phrase`

Run (with the API server running):

```bash
.\venv\Scripts\python .\scripts\import_sefaria_words.py --ref "Genesis.1"
```

Note: the assignment DB table is `public.gematria_entries (id, phrase, value)` only.  
`source` is accepted by the API for convenience but is **not stored** unless you add a `source` column (or create a separate source table).

## Render deployment

### Web Service settings

When creating your Render **Web Service**, set:

- **Root Directory**: `gematria-api`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`

### Environment variables

- **`DATABASE_URL`**: paste your Render Postgres **Internal Database URL**

After deploy:

- Swagger UI: `/swagger-ui`
- OpenAPI JSON: `/openapi.json`

## Importing Strong's Hebrew “dictionary” lemmas (optional)

The repo at `https://github.com/openscriptures/strongs/tree/master/hebrew/` includes a ready-to-parse file:

- `strongs-hebrew-dictionary.js` (a JS-wrapped JSON object keyed by Strong IDs like `"H1"`)

If you clone that repo into `external/strongs` (like we did), you can import lemmas into `public.gematria_entries`:

```bash
.\venv\Scripts\python .\scripts\import_strongs_hebrew.py
```

This will normalize the Hebrew lemma (remove niqqud), compute gematria, and upsert via `PUT /entries/by-phrase`.


