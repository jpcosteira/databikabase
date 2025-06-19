# Formulário web configurável para SQLite

Base de dados com formulario gradio
![ESQUEMA](images/esquema.jpg)

## Componentes principais:

- Formulário de consulta e actualização através de web browser
- Dados guardados em base de dados SQLight
- Base de Dados e formulário totalmente especificado a partir de ficheiro de configuração config.yaml 

### Para detalhes consultar pasta app
[app/config.yaml](app/config.yaml)
### Utilitários importantes

- Editor de SQL: https://dbeaver.com/docs/dbeaver/ https://sqlitebrowser.org/dl/
- Gradio https://www.gradio.app/
--- 
# YAML-Configured Gradio SQL App

## 🛠️ Setup Manual

### 1. 📁 Project Structure

Place these files in a directory:

```
your_project/
├── app.py             # Your main Python script
├── config.yaml        # Configuration file (UI + database schema)
├── requirements.txt   # Dependencies list
└── Dockerfile         # (Optional) For containerized setup
```

---

### 2. 📦 Install Required Packages

You need Python 3.8+ and the following packages:

#### a. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### b. Install dependencies:

Install manually:

```bash
pip install gradio pyyaml
```

Or use:

```bash
pip install -r requirements.txt
```

---

### 3. 📝 Configure `config.yaml`

Example `config.yaml`:

```yaml
database:
  name: data.db
  table: records

auth:
  password: "secret"

interface:
  tabs:
    - name: General Info
      layout:
        - row: false
          fields:
            - name: priority
              label: Priority Level
              type: dropdown
              options: ["High", "Middle", "Low"]
              default: "Middle"
```

---

### 4. 🚀 Launch the App

```bash
python app.py
```

Visit:

```
http://127.0.0.1:7860
```

---

## 🐳 Docker Support

### Dockerfile:

```Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir gradio pyyaml

EXPOSE 7860
CMD ["python", "app.py"]
```

### Build & Run:

```bash
docker build -t gradio-sql-app .
docker run -p 7860:7860 gradio-sql-app
```

---

## ✅ Features

- Web UI auto-generated from `config.yaml`
- SQLite database backend
- Password-protected load/save
- Supports text, number, checkbox, dropdown, radio, datetime
- Auto schema updates if config has new fields
