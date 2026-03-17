# FlowSheet - Project Context

## Project Overview

FlowSheet is a backend-focused web application built with Python and Django.
Its goal is to automate data-driven workflows using spreadsheet input.

The current version of the system allows a user to:

1. Upload an Excel spreadsheet
2. Parse the spreadsheet and persist its rows in the database
3. Organize imported rows by import batch
4. Edit imported records inside the application before running the automation
5. Execute browser automations using Playwright based on the imported data
6. Track execution progress in real time, row by row
7. Review execution history and reprocess only failed records

This project acts as a simple spreadsheet-driven RPA platform, focused on backend architecture, automation orchestration, and data persistence.

---

## Tech Stack

### Backend
- Python
- Django

### Automation
- Playwright

### Data Processing
- openpyxl

### Database (development)
- SQLite

### Templates / UI
- Django Templates
- Vanilla JavaScript for polling execution status in real time

---

## High-Level Architecture

Template -> View -> Service -> Model -> Database

### Templates
Responsible for rendering HTML and visual status information.

### Views
Handle HTTP requests and responses.
Keep orchestration logic light and delegate business rules to services.

### Services
Contain business logic such as:
- spreadsheet import
- automation execution
- background processing
- execution progress persistence

### Models
Represent domain entities and database tables using Django ORM.

### Database
Stores:
- imported spreadsheets
- imported records
- execution metadata
- per-record execution results

---

## Main Apps

### registros
Handles spreadsheet import and imported records.

### automations
Handles browser automation execution and execution history.

Main apps currently in active use:

- registros
- automations

---

## Core Domain Models

### Model: ImportacaoPlanilha

Represents a spreadsheet import batch.

Fields:
- nome_arquivo
- status
- total_registros
- criado_em

Purpose:
- keep import history
- group imported records
- represent the origin of a set of rows

---

### Model: Registro

Represents one row imported from a spreadsheet.

Fields:
- importacao
- nome
- empresa
- email
- telefone
- status
- mensagem_erro
- executado_em
- criado_em

Purpose:
- store structured input data
- represent a record that can be edited and later used by automation

Statuses:
- pendente
- executando
- executado
- erro

---

### Model: Execution

Represents a single automation run.

Fields:
- importacao
- user
- status
- target_url
- total_linhas
- linhas_processadas
- sucesso_count
- erro_count
- mensagem_erro
- criado_em
- finalizado_em

Purpose:
- track the execution lifecycle
- persist aggregated automation results

Statuses:
- pending
- running
- completed
- error

---

### Model: ResultadoExecucaoRegistro

Represents the result of processing one record inside one execution.

Fields:
- execution
- registro
- status
- mensagem_erro
- executado_em

Purpose:
- keep execution history per record
- support execution detail pages
- support failed-record reprocessing

Statuses:
- executado
- erro

---

## Feature 1 - Spreadsheet Import

### Route
- `/upload/`

### View
- `upload_planilha`

### Service
- `importar_planilha()`

### Flow

User uploads spreadsheet  
-> View receives file  
-> Service creates `ImportacaoPlanilha`  
-> Service loads workbook with `openpyxl`  
-> Rows are converted into `Registro` objects  
-> Records are linked to the import batch  
-> Records are saved using `bulk_create()`  
-> Import batch is updated with total record count and final status

### Important behavior

- Old records are no longer deleted
- Each upload creates a new import batch
- Imported records remain associated with their original spreadsheet import

---

## Feature 2 - List Imported Records

### Route
- `/registros/`

### View
- `listar_registros`

### Behavior

- fetches the most recent `ImportacaoPlanilha`
- loads up to 50 records from that import
- renders the records in a table
- shows latest import information
- shows latest execution information
- polls execution status when an automation is running

### Extra behavior

- the error column is shown only when at least one record has an error
- each row can be edited from the list page

---

## Feature 3 - Edit Imported Record

### Route
- `/registros/<id>/editar/`

### View
- `editar_registro`

### Behavior

- allows editing one imported record directly in the app
- resets automation state when a record is changed

When a record is edited:
- status becomes `pendente`
- previous error message is cleared
- previous execution timestamp is cleared

This ensures the edited row is considered a fresh input for future automation runs.

---

## Feature 4 - Automation Test Page

### Route
- `/form-teste/`

### View
- `form_teste`

### Purpose

This page simulates an external target system for Playwright.

Fields:
- nome
- empresa
- email
- telefone

When submitted, the page renders the received data in a result template.

Used only for internal testing and automation validation.

---

## Feature 5 - Automation Execution

### Trigger

On the records page there is a button:
- `Iniciar automação`

### Route
- `POST /automations/executar/`

### View
- `executar_automacao_view`

### Current behavior

- starts the automation in background
- creates an `Execution`
- redirects back to the records page with the current execution id
- the records page polls execution status in real time

---

## Automation Service

### File
- `automations/services.py`

### Main responsibilities

- create `Execution`
- resolve which records will be processed
- process records one by one
- persist progress after each record
- create `ResultadoExecucaoRegistro`
- update `Registro` state in real time

### Current flow

Resolve import / records  
-> Create `Execution`  
-> Start background thread  
-> For each record:
   - mark record as `executando`
   - open Playwright browser
   - navigate to target page
   - fill fields using record data
   - submit form
   - persist result immediately
   - update execution counters
-> Finish execution with final status

### Important note

The current MVP uses an in-process background thread for async execution.
This is enough for learning and portfolio purposes, but not ideal for production.

Production-ready evolution would use:
- queue
- worker
- broker (e.g. Redis)
- task processor (e.g. Celery)

---

## Real-Time Status Updates

### Current implementation

The system now supports line-by-line status updates while automation is still running.

How it works:

- automation runs in a background thread
- each record is persisted immediately after processing
- `/automations/execucoes/<id>/status/` exposes execution progress as JSON
- the records page polls this endpoint using JavaScript
- DOM is updated without full page reload

This allows the user to see:
- execution status
- processed count
- success count
- error count
- per-row status changes
- per-row error messages

in near real time

---

## Feature 6 - Execution Detail Page

### Route
- `/automations/execucoes/<id>/`

### View
- `detalhe_execucao_view`

### Behavior

- shows execution summary
- shows all per-record results linked to that execution
- polls the execution status endpoint while the execution is running

This page exists as a dedicated execution history / monitoring screen.

---

## Feature 7 - Reprocess Failed Records

### Route
- `POST /automations/execucoes/<id>/reprocessar-erros/`

### View
- `reprocessar_erros_view`

### Behavior

- filters only records that failed in a previous execution
- starts a new background execution using just those failed records
- keeps execution history for comparison

---

## Current Request / Data Flow

### Import Flow

Spreadsheet upload  
-> Django view receives file  
-> Import service parses workbook  
-> `ImportacaoPlanilha` is created  
-> `Registro` rows are persisted  
-> Latest import is available in `/registros/`

### Automation Flow

User clicks start  
-> `Execution` is created  
-> background thread starts  
-> Playwright processes records  
-> each row updates status immediately  
-> JSON status endpoint exposes progress  
-> frontend polling updates the page live  
-> execution detail page stores final history

---

## Current Status

Working features:

- Spreadsheet upload
- Import batch history
- Database persistence
- Imported record listing
- Record editing inside the app
- Automation trigger
- Playwright browser automation
- Real-time status updates per row
- Execution detail page
- Failed-record reprocessing
- Automated tests for import, edit, execution, status API, and reprocessing

---

## Known Limitations

1. Spreadsheet structure is strict

The import service currently assumes exactly four columns:
- nome
- empresa
- email
- telefone

If the spreadsheet has more or fewer columns, import may fail.

2. Background execution uses local threads

This works for MVP and local development, but is not production-grade.

3. No robust spreadsheet validation yet

There is no formal validation for:
- extra columns
- missing columns
- invalid data types
- malformed emails

4. No production queue / worker yet

The current architecture intentionally stops short of Celery/Redis.

---

## Suggested Next Improvements

1. Spreadsheet validation layer
2. Background workers with Celery + Redis
3. Authentication and per-user ownership
4. Logging system
5. API endpoints
6. PostgreSQL for production
7. Dockerized deployment
8. Better automation target abstraction

---

## AI / Code Generation Guidelines

When generating code for this project:

- Keep business logic inside services
- Avoid heavy logic in views
- Automation logic must stay in `automations`
- Spreadsheet logic must stay in `registros`
- Templates should remain simple and mostly presentational
- Preserve clear separation between import domain and automation domain

---

## Project Goal

Build a data-driven automation platform where spreadsheet records control automated web interactions, with clear backend architecture, execution history, and real-time monitoring suitable for learning Django and backend engineering.
