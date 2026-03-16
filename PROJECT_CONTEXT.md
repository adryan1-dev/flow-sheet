
# FlowSheet — Project Context

## Project Overview
FlowSheet is a backend-focused web application built with Python and Django.
Its goal is to automate data-driven workflows using spreadsheet input.

The system allows a user to:

1. Upload an Excel spreadsheet
2. Parse and store the spreadsheet rows in the database
3. Use the stored records to run web automations using Playwright
4. Automatically fill forms on external systems

This acts as a simple RPA (Robotic Process Automation) system controlled by spreadsheet data.

---

# Tech Stack

Backend
- Python
- Django

Automation
- Playwright

Data Processing
- openpyxl

Database (development)
- SQLite

Templates
- Django Templates (simple HTML)

---

# Architecture

Template → View → Service → Model → Database

Templates
Responsible only for rendering HTML.

Views
Handle HTTP requests and responses.

Services
Contain the business logic of the system.

Models
Represent database tables using Django ORM.

Database
Stores application state and automation records.

---

# Main Apps

accounts
automations
logs
registros

Main apps currently in use:

registros  
automations

---

# Core Model

Model: Registro

Fields:

- nome
- empresa
- email
- telefone
- criado_em

These records represent rows from the spreadsheet and are used as inputs for automation.

---

# Feature 1 — Spreadsheet Import

Route:

/upload

Flow:

User uploads spreadsheet  
↓  
View upload_planilha receives file  
↓  
Service importar_planilha parses spreadsheet using openpyxl  
↓  
Rows converted into Registro objects  
↓  
Saved using bulk_create()

Important behavior:

Before importing a new spreadsheet:

Registro.objects.all().delete()

This ensures only the latest spreadsheet exists in the system.

---

# Feature 2 — List Records

Route:

/registros

View:

listar_registros

Behavior:

Fetch records from database  
↓  
Render template lista_registros.html  
↓  
Display records in table

Limit:

50 records per page.

---

# Feature 3 — Automation Test Page

Fake form used to simulate an external system.

Route:

/form-teste

Fields:

- nome
- empresa
- email
- telefone

When submitted the page displays the received data.

Used only for testing Playwright automation.

---

# Feature 4 — Automation Execution

On the records page there is a button:

"Iniciar automação"

This triggers:

POST /automations/executar

View:

executar_automacao_view

The view calls:

executar_automacoes()

from the automation service.

---

# Automation Service

File:

automations/services.py

Current flow:

Fetch records from database  
↓  
Start Playwright browser  
↓  
Open /form-teste  
↓  
Fill form fields using record data  
↓  
Submit form  
↓  
Repeat for each record

Playwright runs with:

headless=False  
slow_mo enabled

This allows visual debugging of the automation.

---

# Playwright Configuration

Browser launch:

browser = p.chromium.launch(headless=False, slow_mo=500)

Context:

context = browser.new_context(
    viewport={"width": 1280, "height": 900}
)

Page:

page = context.new_page()

---

# Current System Flow

Spreadsheet Upload  
↓  
Django parses Excel  
↓  
Records saved in database  
↓  
Automation service retrieves records  
↓  
Playwright browser opens  
↓  
Form is automatically filled and submitted

---

# Current Status

Working features:

✓ Spreadsheet upload  
✓ Database persistence  
✓ Record listing page  
✓ Automation trigger button  
✓ Playwright browser automation  
✓ Form auto-filling

---

# Planned Improvements

1. Automation logs

Registro → success / error

2. Record status

- pendente
- executado
- erro

3. Automation results page

4. Background workers

Future architecture:

HTTP request  
↓  
Create job  
↓  
Queue system  
↓  
Worker executes automation

---

# AI Guidelines

When generating code for this project:

- Keep business logic inside services
- Avoid heavy logic in views
- Automation logic must stay in automations app
- Spreadsheet logic stays in registros app
- Templates remain simple Django templates

---

# Project Goal

Build a data-driven automation system where spreadsheet records control automated web interactions.
