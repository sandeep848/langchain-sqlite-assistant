"""Natural-language analytics for a local, read-only SQLite database."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from query_guard import UnsafeQuery, execute_read_only, schema_context

load_dotenv()
DB_PATH = Path(__file__).with_name("Student.db")

st.set_page_config(page_title="SQLite Analytics Assistant", layout="wide")
st.title("SQLite Analytics Assistant")
st.caption("Natural-language questions → guarded SELECT → auditable result table")

api_key = st.sidebar.text_input(
    "Groq API key", type="password", value=os.getenv("GROQ_API_KEY", "")
)
model = st.sidebar.selectbox(
    "Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
)
max_rows = st.sidebar.slider("Maximum returned rows", 10, 500, 200, 10)

schema = schema_context(DB_PATH)
with st.expander("Database schema"):
    st.code(schema, language="sql")

question = st.text_area(
    "Analytics question",
    placeholder="Which branch has the highest average marks?",
)

if st.button("Generate and run", type="primary", disabled=not question):
    if not api_key:
        st.error("Provide a Groq API key.")
        st.stop()

    prompt = f"""You translate analytics questions into SQLite.
Return exactly one SELECT or WITH query and no Markdown.
Never modify data. Use only the supplied schema.
Always aggregate when the question asks for a comparison.

Schema:
{schema}

Question: {question}
SQL:"""

    llm = ChatGroq(groq_api_key=api_key, model=model, temperature=0)
    generated = llm.invoke(prompt).content.strip().strip("`")
    if generated.lower().startswith("sql"):
        generated = generated[3:].strip()

    try:
        columns, rows, safe_sql = execute_read_only(
            DB_PATH, generated, max_rows=max_rows
        )
    except (UnsafeQuery, Exception) as exc:
        st.error(f"Query rejected: {exc}")
    else:
        st.subheader("Audited SQL")
        st.code(safe_sql, language="sql")
        st.subheader("Result")
        st.dataframe(pd.DataFrame(rows, columns=columns), use_container_width=True)
        st.caption(f"{len(rows)} row(s) returned from a read-only connection.")
