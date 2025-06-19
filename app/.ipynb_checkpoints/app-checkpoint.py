import os
import sqlite3
import yaml
import gradio as gr

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

db_name = config['database']['name']
table_name = config['database']['table']

def map_field_to_sql(field):
    ftype = field['type']
    if ftype == "number":
        return "INTEGER"
    elif ftype == "checkbox":
        return "BOOLEAN"
    return "TEXT"

def create_table():
    fields = []
    for tab in config['interface']['tabs']:
        for field in tab['fields']:
            name = field['name']
            sql_type = map_field_to_sql(field)
            fields.append(f"{name} {sql_type}")
    with sqlite3.connect(db_name) as conn:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (id TEXT PRIMARY KEY, {', '.join(fields)})"
        )
        conn.commit()

create_table()

field_components = {}
tabs_ui = []

for tab in config['interface']['tabs']:
    components = []
    for field in tab['fields']:
        key = field['name']
        label = field.get("label", key)
        default = field.get("default", None)
        ftype = field['type']
        if ftype == "text":
            comp = gr.Textbox(label=label, value=default)
        elif ftype == "number":
            comp = gr.Number(label=label, value=default)
        elif ftype == "checkbox":
            comp = gr.Checkbox(label=label, value=default)
        elif ftype == "dropdown":
            comp = gr.Dropdown(label=label, choices=field.get("options", []), value=default)
        elif ftype == "radio":
            comp = gr.Radio(label=label, choices=field.get("options", []), value=default)
        else:
            comp = gr.Textbox(label=label)
        field_components[key] = comp
        components.append(comp)
    tabs_ui.append(gr.Tab(label=tab['name'], children=components))

id_input = gr.Textbox(label="Record ID")

def load_data(record_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.execute(f"SELECT * FROM {table_name} WHERE id=?", (record_id,))
        row = cursor.fetchone()
        if row:
            col_names = [desc[0] for desc in cursor.description]
            return [row[col_names.index(key)] if key in col_names else None for key in field_components.keys()]
        return [None] * len(field_components)

def save_data(record_id, *values):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.execute(f"SELECT 1 FROM {table_name} WHERE id=?", (record_id,))
        if cursor.fetchone():
            conn.execute(f"UPDATE {table_name} SET {', '.join(f'{k}=?' for k in field_components)} WHERE id=?", (*values, record_id))
        else:
            conn.execute(f"INSERT INTO {table_name} (id, {', '.join(field_components)}) VALUES (?, {', '.join(['?'] * len(values))})", (record_id, *values))
        conn.commit()
    return "Saved successfully."

with gr.Blocks() as demo:
    gr.Markdown("# Dynamic Form from YAML")
    with gr.Row():
        id_input_comp = id_input
        load_btn = gr.Button("Load")
        save_btn = gr.Button("Save")

    for tab in tabs_ui:
        demo.append(tab)

    status_output = gr.Textbox(label="Status")

    load_btn.click(fn=load_data, inputs=[id_input_comp], outputs=list(field_components.values()))
    save_btn.click(fn=save_data, inputs=[id_input_comp] + list(field_components.values()), outputs=status_output)

demo.launch()
