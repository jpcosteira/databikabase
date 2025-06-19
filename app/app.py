import gradio as gr
import sqlite3
import yaml
import os
import csv
from datetime import datetime

# Load configuration from YAML
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Database and table info
db_name = config["database"]["name"]
table_name = config["database"]["table"]
admin_password = config["auth"]["password"]

# Determine SQL type based on field type
def sql_type(field_type):
    return {
        "text": "TEXT",
        "number": "INTEGER",
        "checkbox": "BOOLEAN",
        "dropdown": "TEXT",
        "radio": "TEXT",
        "datetime": "DATETIME",
    }.get(field_type, "TEXT")

# Check and update database schema to match config fields
def sync_db_schema():
    expected_fields = {}
    for tab in config["interface"]["tabs"]:
        for section in tab.get("layout", []):
            for field in section.get("fields", []):
                fname = field["name"]
                ftype = sql_type(field["type"])
                expected_fields[fname] = ftype

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id TEXT PRIMARY KEY)")
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
        for field, ftype in expected_fields.items():
            if field not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {field} {ftype}")
        conn.commit()

# Build the Gradio UI
def build_ui():
    field_components = {}

    with gr.Blocks() as demo:
        gr.Markdown("## 🔒 Password-Protected YAML-Powered Form")

        with gr.Row():
            id_input = gr.Textbox(label="Record ID", placeholder="Enter ID")
            password_input = gr.Textbox(label="Password", type="password", placeholder="Enter password")
            load_btn = gr.Button("🔍 Load")
            save_btn = gr.Button("💾 Save")

        tab_list = config["interface"]["tabs"] + [{"name": "All Data"}]

        for tab in tab_list:
            with gr.Tab(tab["name"]):
                if tab["name"] == "All Data":
                    with gr.Row():
                        view_pwd = gr.Textbox(label="Password", type="password", placeholder="Enter password")
                        filter_field = gr.Dropdown(label="Sort by Field", choices=["id"])
                        filter_text = gr.Textbox(label="Filter Contains")
                        refresh_btn = gr.Button("🔄 Refresh Table")
                        export_btn = gr.Button("📁 Download CSV")

                    data_table = gr.Dataframe(headers=["id"], label="All Records", interactive=False)
                    file_output = gr.File(label="CSV File")

                    def show_all_data(pwd, sort_field, filter_val):
                        if pwd != admin_password:
                            return [], None
                        with sqlite3.connect(db_name) as conn:
                            cursor = conn.cursor()
                            query = f"SELECT * FROM {table_name}"
                            params = []
                            if filter_val:
                                query += f" WHERE {sort_field} LIKE ?"
                                params.append(f"%{filter_val}%")
                            query += f" ORDER BY {sort_field}"
                            cursor.execute(query, params)
                            rows = cursor.fetchall()
                            headers = [desc[0] for desc in cursor.description]

                        data_table.headers = headers
                        return rows, None

                    def export_csv(pwd):
                        if pwd != admin_password:
                            return None
                        filepath = "export.csv"
                        with sqlite3.connect(db_name) as conn:
                            cursor = conn.cursor()
                            cursor.execute(f"SELECT * FROM {table_name}")
                            rows = cursor.fetchall()
                            headers = [desc[0] for desc in cursor.description]
                            with open(filepath, "w", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow(headers)
                                writer.writerows(rows)
                        return filepath

                    refresh_btn.click(fn=show_all_data, inputs=[view_pwd, filter_field, filter_text], outputs=[data_table, file_output])
                    export_btn.click(fn=export_csv, inputs=[view_pwd], outputs=file_output)
                    continue

                for section in tab.get("layout", []):
                    container = gr.Row() if section.get("row") else gr.Column()
                    with container:
                        for field in section.get("fields", []):
                            key = field["name"]
                            label = field.get("label", key)
                            default = field.get("default", None)
                            ftype = field["type"]

                            if ftype == "text":
                                comp = gr.Textbox(label=label, value=default)
                            elif ftype == "number":
                                comp = gr.Number(label=label, value=default)
                            elif ftype == "checkbox":
                                comp = gr.Checkbox(label=label, value=default)
                            elif ftype == "dropdown":
                                comp = gr.Dropdown(label=label, choices=field["options"], value=default)
                            elif ftype == "radio":
                                comp = gr.Radio(label=label, choices=field["options"], value=default)
                            elif ftype == "datetime":
                                comp = gr.Textbox(label=label + " (YYYY-MM-DDTHH:MM)", value=default, placeholder="2025-06-19T10:00")
                            else:
                                comp = gr.Textbox(label=label)

                            field_components[key] = comp

        status_box = gr.Textbox(label="Status", interactive=False)

        def load_data(record_id, pwd):
            if not record_id.strip():
                return ["" ] * len(field_components)+[ "❌ Please enter a Record ID."]
            if pwd != admin_password:
                return ["" ] * len(field_components)+ ["🔐 Incorrect password."]

            with sqlite3.connect(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
                row = cursor.fetchone()
                if row:
                    col_names = [desc[0] for desc in cursor.description]
                    values = []
                    for key in field_components:
                        field = next((f for t in config["interface"]["tabs"] for s in t["layout"] for f in s["fields"] if f["name"] == key), None)
                        val = row[col_names.index(key)] if key in col_names else None
                        if field and field.get("type") == "datetime" and val:
                            try:
                                val = datetime.fromisoformat(val).isoformat(timespec='minutes').replace(" ", "T")
                            except:
                                val = ""
                        values.append(val)
                    return values+ ["✅ Data loaded."]
                else:
                    return ["" ] * len(field_components)+[ "⚠️ No record found."]

        def save_data(record_id, pwd, *values):
            if not record_id.strip():
                return "❌ Please enter a Record ID."
            if pwd != admin_password:
                return "🔐 Incorrect password."

            sanitized_values = []
            for key, val in zip(field_components, values):
                field = next((f for t in config["interface"]["tabs"] for s in t["layout"] for f in s["fields"] if f["name"] == key), None)
                if field and field.get("type") == "datetime" and val:
                    try:
                        val = datetime.fromisoformat(val).isoformat(sep=" ")
                    except ValueError:
                        return f"❌ Invalid datetime format for '{key}'. Use YYYY-MM-DDTHH:MM"
                sanitized_values.append(val)

            with sqlite3.connect(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (record_id,))
                if cursor.fetchone():
                    clause = ", ".join(f"{k}=?" for k in field_components)
                    cursor.execute(f"UPDATE {table_name} SET {clause} WHERE id = ?", (*sanitized_values, record_id))
                else:
                    placeholders = ", ".join("?" for _ in field_components)
                    cursor.execute(f"INSERT INTO {table_name} (id, {', '.join(field_components.keys())}) VALUES (?, {placeholders})", (record_id, *sanitized_values))
                conn.commit()

            return "✅ Data saved successfully."

        load_btn.click(fn=load_data, inputs=[id_input, password_input], outputs=[*field_components.values(), status_box])
        save_btn.click(fn=save_data, inputs=[id_input, password_input] + list(field_components.values()), outputs=status_box)

    return demo
# Initialize database and launch app
sync_db_schema()
demo = build_ui()
demo.launch()