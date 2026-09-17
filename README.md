# SQLite Analytics Assistant

A read-only natural-language analytics application for small SQLite databases. Unlike the other LLM projects in this profile, this repository focuses on **safe structured-data access** rather than chat, summarization or retrieval.

## Distinct use case

A student, analyst or instructor can ask questions such as:

- Which branch has the highest average marks?
- How many students are in each section?
- Show the top five scores.

The model generates SQL, but deterministic application logic validates the statement before it reaches the database.

## Safety architecture

~~~mermaid
flowchart LR
    A["Natural-language question"] --> B["LLM SQL translation"]
    B --> C["Read-only policy guard"]
    C --> D["SQLite URI in read-only mode"]
    D --> E["Audited SQL and result table"]
~~~

The guard:

- accepts only `SELECT` and `WITH` statements
- rejects multiple statements and mutation keywords
- adds a maximum row limit
- opens SQLite with `mode=ro`
- displays the final SQL for review

## Run

~~~bash
git clone https://github.com/sandeep848/langchain-sqlite-assistant.git
cd langchain-sqlite-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
~~~

## Test

~~~bash
pytest
~~~

## Key files

- `app.py` — Streamlit analytics workflow
- `query_guard.py` — deterministic SQL policy and read-only execution
- `sqlite.py` — sample database generator
- `tests/test_query_guard.py` — policy regression tests
