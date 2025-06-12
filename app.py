
import streamlit as st
import os
import sqlite3
import tempfile
import pandas as pd
import io
import google.generativeai as genai
from dotenv import load_dotenv

if "schema_info" not in st.session_state:
    st.session_state["schema_info"] = None

# Try to get API key from Streamlit Secrets (Streamlit Cloud)
api_key = st.secrets.get("API_KEY", None)

# Configure Gemini
genai.configure(api_key=api_key)

# Function to extract comprehensive schema information from a SQLite database
def extract_schema_info(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = {}

    for table in tables:
        table_name = table[0]
        # Skip SQLite internal tables
        if table_name.startswith('sqlite_'):
            continue

        # Get column information for this table
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()

        # Format: (cid, name, type, notnull, dflt_value, pk)
        col_info = []
        for col in columns:
            col_info.append({
                'name': col[1],
                'type': col[2] if col[2] else 'TEXT',
                'nullable': not col[3],
                'default': col[4],
                'primary_key': bool(col[5])
            })

        # Get foreign key information
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
        foreign_keys = cursor.fetchall()

        fk_info = []
        for fk in foreign_keys:
            fk_info.append({
                'from': fk[3],
                'to_table': fk[2],
                'to_column': fk[4]
            })

        schema_info[table_name] = {
            'columns': col_info,
            'foreign_keys': fk_info
        }

    conn.close()
    return schema_info

# Function to generate a comprehensive prompt based on schema information
def generate_prompt(schema_info):
    prompt = "You are an expert in converting English questions to SQL queries!\n\n"

    # Add database schema information
    prompt += "Database Schema:\n"

    for table_name, info in schema_info.items():
        columns = info['columns']
        foreign_keys = info['foreign_keys']

        prompt += f"\nTable: {table_name}\n"
        prompt += "Columns:\n"

        for col in columns:
            col_type = col['type'].upper()
            pk = " (PRIMARY KEY)" if col['primary_key'] else ""
            nullable = " NOT NULL" if not col['nullable'] else ""
            default = f" DEFAULT {col['default']}" if col['default'] is not None else ""
            prompt += f"  - {col['name']} ({col_type}{pk}{nullable}{default})\n"

        if foreign_keys:
            prompt += "Foreign Keys:\n"
            for fk in foreign_keys:
                prompt += f"  - {fk['from']} REFERENCES {fk['to_table']}({fk['to_column']})\n"

    # Add examples based on the schema
    prompt += "\nSQL Examples:\n"

    tables = list(schema_info.keys())
    if tables:
        # Use the first table for examples
        table_name = tables[0]
        columns = schema_info[table_name]['columns']

        prompt += f"\nExample 1: How many records are in {table_name}?\n"
        prompt += f"SELECT COUNT(*) FROM {table_name};\n"

        # Add more examples if we have enough columns
        if len(columns) >= 2:
            col1 = columns[0]['name']
            col2 = columns[1]['name']
            col1_type = columns[0]['type'].lower()

            # Adjust examples based on column type
            if 'int' in col1_type or 'number' in col1_type or 'float' in col1_type:
                prompt += f"\nExample 2: List all records where {col1} is greater than 50.\n"
                prompt += f"SELECT * FROM {table_name} WHERE {col1} > 50;\n"
            elif 'char' in col1_type or 'text' in col1_type or 'varchar' in col1_type:
                prompt += f"\nExample 2: List all records where {col1} contains 'value'.\n"
                prompt += f"SELECT * FROM {table_name} WHERE {col1} LIKE '%value%';\n"
            else:
                prompt += f"\nExample 2: List all records sorted by {col1}.\n"
                prompt += f"SELECT * FROM {table_name} ORDER BY {col1};\n"

            if len(columns) >= 3:
                col3 = columns[2]['name']
                prompt += f"\nExample 3: Count records grouped by {col3}.\n"
                prompt += f"SELECT {col3}, COUNT(*) FROM {table_name} GROUP BY {col3};\n"

    # Add guidelines for generating SQL queries
    prompt += '''

Guidelines for SQL generation:
1. Use proper SQL syntax with correct keywords
2. Always use proper quotes for text values (single quotes)
3. Handle NULL values with IS NULL or IS NOT NULL
4. For text searches, use LIKE with % wildcards
5. Use appropriate JOIN types when querying multiple tables
6. Include GROUP BY when using aggregate functions
7. Always validate column and table names exist in the schema
8. Return only valid executable SQL queries
'''

    return prompt

# Gemini Function
def get_response(que, prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([prompt, que])
    return response.text

# SQL Runner
def read_query(sql, db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to get column names for a query result
def get_column_names(sql, db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(sql)
    names = [description[0] for description in cursor.description]
    conn.close()
    return names

# Function to display query results with enhanced features
def display_query_results(result, col_names, max_rows=1000):
    if not result:
        st.warning("⚠️ No results found for this query.")
        return

    # Convert to dictionary for display
    result_dicts = []
    for row in result[:max_rows]:  # Limit to max_rows
        row_dict = {}
        for i, col in enumerate(col_names):
            row_dict[col] = row[i]
        result_dicts.append(row_dict)

    # Display the results
    st.markdown("<div class='response'>", unsafe_allow_html=True)
    st.subheader("📥 Query Result:")

    # Show how many rows were returned
    total_rows = len(result)
    if total_rows > max_rows:
        st.info(f"Showing {max_rows} of {total_rows} rows. The results have been truncated.")
    else:
        st.info(f"Found {total_rows} rows.")

    # Display the data
    df = pd.DataFrame(result_dicts)
    st.dataframe(df, use_container_width=True)

    # Add export option
    if result_dicts:
        # Create a download button for CSV export
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download results as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv"
        )

    st.markdown("</div>", unsafe_allow_html=True)

# Page Config
st.set_page_config(page_title="IntelliSQL", page_icon="🧠", layout="wide")

# --- CSS Styling ---
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&family=Roboto+Mono&display=swap');

html, body, .stApp {
    background: linear-gradient(135deg, #0d0d0d, #1a0000);
    color: white;
    font-family: 'Orbitron', sans-serif;
    scroll-behavior: smooth;
    transition: all 0.4s ease;
}

.main-title {
    font-size: 3rem;
    text-align: center;
    color: #ff1a1a;
    animation: flicker 1.5s infinite alternate;
    text-shadow: 0 0 10px red, 0 0 20px crimson, 0 0 30px darkred;
}
@keyframes flicker {
    0% { opacity: 1; }
    50% { opacity: 0.75; }
    100% { opacity: 1; }
}

.subtitle {
    text-align: center;
    font-size: 1.4rem;
    color: #ff9999;
    margin-bottom: 2rem;
    font-family: 'Roboto Mono', monospace;
    animation: slide-up 1.5s ease;
}
@keyframes slide-up {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

.description-box {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.5rem;
    backdrop-filter: blur(6px);
    box-shadow: 0 0 10px rgba(255, 0, 0, 0.4);
    margin-bottom: 2rem;
}

.upload-box {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px dashed #ff4d4d;
}

.schema {
    font-family: 'Roboto Mono', monospace;
    background-color: rgba(255, 255, 255, 0.07);
    padding: 1rem;
    border-radius: 12px;
    margin-top: 1rem;
    color: #66ffff;
    font-size: 0.9rem;
    border-left: 4px solid #ff1a1a;
}

.stTextInput > label {
    font-size: 1.4rem !important;
    font-weight: 600;
    color: #00ffff;
    font-family: 'Orbitron', sans-serif;
}

.stTextInput > div > input {
    background-color: rgba(0,0,0,0.5);
    color: #00ffff;
    border: 1px solid #00ffff;
    border-radius: 10px;
    padding: 0.6rem;
    transition: 0.3s;
}

.stButton button {
    background: linear-gradient(135deg, #ff0000, #990000);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    padding: 0.6rem 1.5rem;
    transition: transform 0.3s;
}

.response {
    animation: glowFade 1s ease;
    background: rgba(255, 255, 255, 0.05);
    padding: 1rem;
    border-radius: 15px;
    box-shadow: 0 0 10px #ff4d4d;
    margin-top: 1rem;
}

.footer {
    text-align: center;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: #999;
}
</style>
''', unsafe_allow_html=True)

# --- Title & Subtitle ---
st.markdown("<h1 class='main-title'>IntelliSQL - Ask Your Database</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Query your database like a pro – just by asking in English!</h3>", unsafe_allow_html=True)

# --- Description ---
st.markdown('''
<div class='description-box'>
<h4>🚀 Features:</h4>
<ul>
<li>🤖 Translates English to SQL instantly</li>
<li>📊 Upload your own SQLite database file</li>
<li>🔍 Dynamic schema detection and understanding</li>
<li>⚡ Powered by Gemini 2.0 Pro</li>
<li>📁 Export query results as CSV</li>
<li>🧠 Designed for students, analysts & developers</li>
</ul>
</div>
''', unsafe_allow_html=True)

st.markdown('''
<div style="background-color: rgba(255, 50, 50, 0.15); border-left: 5px solid #ff4d4d; padding: 1rem; margin-top: 1.2rem; font-family: 'Roboto Mono', monospace; color: #66ccff; border-radius: 12px; box-shadow: 0 0 8px rgba(255, 0, 0, 0.3);">
🔒 <b>Data Privacy Notice:</b><br><br>
When you upload a database file, <b>the admin does not store, access, or retain your uploaded database in any way</b>.<br>
Uploaded files are handled as <b>temporary files</b> and remain only on your system for the duration of your session.<br>
No database content is ever stored or backed up by the admin or on any external server.<br><br>
<b>Your data privacy and security are fully maintained.</b>
</div>
''', unsafe_allow_html=True)


# Initialize session state
if 'db_path' not in st.session_state:
    st.session_state['db_path'] = None
if 'schema_info' not in st.session_state:
    st.session_state['schema_info'] = None
if 'prompt' not in st.session_state:
    st.session_state['prompt'] = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state['uploaded_file_name'] = None

# --- Database Upload Section ---
st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
st.subheader("📥 Upload Your Database")
st.write("Upload your SQLite database file (.db, .sqlite, .sqlite3) to start querying it in natural language.")

uploaded_file = st.file_uploader("Choose a database file", type=['db', 'sqlite', 'sqlite3'])

if uploaded_file:
    # Create a temporary directory to store the uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    # Store the path and filename in session state
    st.session_state['db_path'] = tmp_path
    st.session_state['uploaded_file_name'] = uploaded_file.name

    # Extract schema information
    try:
        schema_info = extract_schema_info(tmp_path)
        st.session_state['schema_info'] = schema_info

        # Generate the prompt
        prompt = generate_prompt(schema_info)
        st.session_state['prompt'] = prompt

        # Display success message
        st.success(f"Database '{uploaded_file.name}' uploaded successfully! Found {len(schema_info)} tables.")

    except Exception as e:
        st.error(f"Error processing database: {e}")
        st.session_state['db_path'] = None
        st.session_state['schema_info'] = None
        st.session_state['prompt'] = None
        st.session_state['uploaded_file_name'] = None

st.markdown("</div>", unsafe_allow_html=True)

# --- Schema Display Section ---
if st.session_state['schema_info']:
    with st.expander("📋 View Database Schema", expanded=False):
        for table_name, info in st.session_state['schema_info'].items():
            st.markdown(f"**📊 Table: {table_name}**")

            columns = info['columns']
            foreign_keys = info['foreign_keys']

            # Create column information display
            col_info = ""
            for col in columns:
                col_type = col['type']
                pk = "🔑 " if col['primary_key'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" (default: {col['default']})" if col['default'] is not None else ""
                col_info += f"{pk}{col['name']} → {col_type}, {nullable}{default}\n"

            st.markdown(f"<div class='schema'><pre>{col_info}</pre></div>", unsafe_allow_html=True)

            # Display foreign keys if any
            if foreign_keys:
                fk_info = "Foreign Keys:\n"
                for fk in foreign_keys:
                    fk_info += f"  {fk['from']} → {fk['to_table']}.{fk['to_column']}\n"
                st.markdown(f"<div class='schema'><pre>{fk_info}</pre></div>", unsafe_allow_html=True)

# --- Query Section ---
if st.session_state['db_path'] and st.session_state['schema_info'] and st.session_state['prompt']:
    st.subheader("🔍 Query Your Database")

    if st.session_state['uploaded_file_name']:
        st.write(f"Currently working with: **{st.session_state['uploaded_file_name']}**")

    st.write("Ask questions about your data in plain English, and we'll convert it to SQL and run the query.")

    # Provide example questions based on the schema
    schema_tables = list(st.session_state['schema_info'].keys())
    if schema_tables:
        first_table = schema_tables[0]
        first_columns = st.session_state['schema_info'][first_table]['columns']

        example_questions = []
        example_questions.append(f"How many records are in {first_table}?")
        example_questions.append(f"Show me all data from {first_table}")

        if len(first_columns) >= 2:
            col1 = first_columns[0]['name']
            col2 = first_columns[1]['name']
            example_questions.append(f"List all {col1} from {first_table}")
            example_questions.append(f"Group {first_table} by {col2}")

        st.info(f"💡 Example questions you can ask:\n" + "\n".join([f"• {q}" for q in example_questions]))

    # Input for query
    que = st.text_input("📝 Enter your English question here:")
    submit = st.button("🚀 Generate SQL & Run")

    # Processing
    if submit and que:
        try:
            with st.spinner("Generating SQL query..."):
                response = get_response(que, st.session_state['prompt'])
                cleaned_sql = response.strip().replace("```sql", "").replace("```", "").strip()

            # Display the generated SQL
            st.markdown(f"<h4>🔍 Generated SQL:</h4>", unsafe_allow_html=True)
            st.code(cleaned_sql, language='sql')

            # Basic validation
            if not cleaned_sql.lower().strip().startswith(('select', 'with')):
                st.error("❌ Invalid SQL generated. Please try rephrasing your question or ensure you're asking for data retrieval.")
            else:
                with st.spinner("Executing query..."):
                    # Run the query
                    result = read_query(cleaned_sql, st.session_state['db_path'])
                    col_names = get_column_names(cleaned_sql, st.session_state['db_path'])

                    # Display results
                    display_query_results(result, col_names)

        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
            if "no such table" in str(e).lower():
                st.error("The table mentioned in the query doesn't exist in your database. Please check the table names in the schema above.")
            elif "no such column" in str(e).lower():
                st.error("One or more columns mentioned in the query don't exist. Please check the column names in the schema above.")
else:
    st.info("👆 Please upload a database file to start querying.")

# --- Default Database Option ---
if not st.session_state['db_path']:
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
    st.subheader("🚀 Quick Start with Sample Database")
    st.write("Don't have a database file? Use our sample student database to try out the app.")

    if st.button("Use Sample Database"):
        if os.path.exists("data.db"):
            st.session_state['db_path'] = "data.db"
            st.session_state['uploaded_file_name'] = "Sample Student Database"

            try:
                schema_info = extract_schema_info("data.db")
                st.session_state['schema_info'] = schema_info

                prompt = generate_prompt(schema_info)
                st.session_state['prompt'] = prompt

                st.success(f"Sample database loaded successfully! Found {len(schema_info)} tables.")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading sample database: {e}")
                st.session_state['db_path'] = None
                st.session_state['schema_info'] = None
                st.session_state['prompt'] = None
                st.session_state['uploaded_file_name'] = None
        else:
            st.error("Sample database (data.db) not found. Please upload your own database file.")

    st.markdown("</div>", unsafe_allow_html=True)

# Clear database button
if st.session_state['db_path']:
    if st.button("🗑️ Clear Current Database"):
        # Clean up temporary file if it exists
        if st.session_state['db_path'] != "data.db" and os.path.exists(st.session_state['db_path']):
            os.unlink(st.session_state['db_path'])

        st.session_state['db_path'] = None
        st.session_state['schema_info'] = None
        st.session_state['prompt'] = None
        st.session_state['uploaded_file_name'] = None
        st.rerun()

# --- Footer ---
st.markdown("""
<div class='footer' style="font-size: 16px;">
    Built with ❤️ by 
    <a href="https://www.instagram.com/rohith_kumar.6/" target="_blank" style="color:#1976d2; font-weight:bold; background:rgba(25,118,210,0.08); padding:2px 6px; border-radius:6px; text-decoration:none;">
        Rohith
    </a>
    using Streamlit, Gemini LLM, and SQLite
</div>
""", unsafe_allow_html=True)

