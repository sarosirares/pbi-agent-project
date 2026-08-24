# Power BI AI Agent

Proiect pentru interogarea unei baze de date SQL Server si generarea de rapoarte Power BI din cereri formulate in limbaj natural.

Aplicatia foloseste Qwen3.6-27B servit prin vLLM. Modelul este folosit pentru interpretarea cererilor si pentru planificarea semantica, iar codul Python valideaza query-urile, controleaza accesul la baza de date si construieste proiectele Power BI.

## Continutul repository-ului

Repository-ul contine trei zone principale:

- `powerbi-agent/` - aplicatia curenta;
- `Testing/` - scripturi si rezultate folosite pentru testarea modelelor;
- `PowerBI Models/` - proiecte Power BI folosite ca exemple, baseline-uri si fisiere de verificare.

Structura principala este:

```text
pbi-agent-project/
|-- powerbi-agent/
|-- Testing/
|-- PowerBI Models/
`-- README.md
```

## Aplicatia

Codul principal este in `powerbi-agent/`.

Componentele importante sunt:

- `app.py` - aplicatia FastAPI si endpoint-urile HTTP;
- `agent.py` - orchestrarea cererilor si a raspunsurilor;
- `llm_client.py` - clientul pentru endpoint-ul vLLM;
- `intent_classifier.py` - clasificarea intentiei si rezolvarea follow-up-urilor;
- `database_schema_*` - citirea si selectia metadata SQL Server;
- `database_query_*` - planificarea, validarea, randarea si executia query-urilor;
- `database_semantic_context.py` - context semantic suplimentar pentru concepte business si relatii aprobate;
- `report_planner.py` - planificarea raportului;
- `semantic_model_*` - generarea modelului semantic Power BI;
- `pbir_*` - generarea si validarea modificarilor PBIR;
- `powerbi_sql_project_builder.py` - construirea proiectului PBIP final;
- `templates/blank_powerbi_project/` - proiectul Power BI de baza folosit la generare;
- `pbir_examples/` - exemple PBIR folosite pentru tipurile de vizualuri suportate.

Aplicatia poate in prezent sa:

- raspunda la intrebari despre date din SQL Server;
- foloseasca agregari, filtre, sortari si metrici derivate;
- calculeze procente si agregari conditionale;
- foloseasca JOIN-uri pe relatii aprobate;
- mentina contextul pentru follow-up-uri;
- genereze proiecte Power BI;
- modifice logic ultimul raport generat in aceeasi sesiune;
- valideze query-urile si modificarile PBIR inainte de executie sau scriere.

## Cerinte

Pentru backend:

```text
Python 3.13
ODBC Driver 18 for SQL Server
SQL Server
endpoint vLLM compatibil OpenAI
```

Pentru verificarea rapoartelor generate este necesar Power BI Desktop.

Dependentele Python sunt in:

```text
powerbi-agent/requirements.txt
```

Dependentele frontend sunt in:

```text
powerbi-agent/package.json
```

## Instalare

Din directorul `powerbi-agent/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Pentru dependentele frontend:

```powershell
npm install
```

## Configurare

In `powerbi-agent/` exista fisierul:

```text
.env.example
```

Acesta trebuie copiat ca `.env` si completat pentru mediul local.

Exemplu:

```env
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL=Qwen3.6-27B

SQLSERVER_SERVER=<SQL_SERVER_INSTANCE>
SQLSERVER_DATABASE=<DATABASE_NAME>
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_TRUSTED_CONNECTION=yes
SQLSERVER_ENCRYPT=yes
SQLSERVER_TRUST_SERVER_CERTIFICATE=yes
```

Fisierul `.env` nu trebuie versionat.

## Pornire

Din `powerbi-agent/`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8080
```

Interfata este apoi disponibila la:

```text
http://127.0.0.1:8080
```

Health check:

```text
GET /health
```

## Utilizare

Aplicatia primeste cereri in limbaj natural.

Exemple de query-uri:

```text
Care este rata globala de promovare?
```

```text
Care este rata de promovare pentru fiecare disciplina?
```

```text
Compara rata de promovare dintre programele de studiu.
```

```text
Care este situatia scolara a lui Vlad Munteanu?
```

Follow-up-urile pot folosi contextul conversatiei:

```text
Care este valoarea totala a taxelor studentilor?
Dar media?
```

Pentru generarea unui raport:

```text
Creeaza-mi un raport Power BI despre situatia scolara a studentilor, pe o singura pagina.
Vreau sa vad numarul total de rezultate academice, nota medie pentru fiecare disciplina
si sa pot filtra raportul dupa programul de studiu.
```

Pentru modificarea raportului:

```text
Pastreaza restul raportului si arata nota medie pe discipline intr-un grafic,
apoi adauga un tabel cu studentii si media notelor fiecaruia.
```

Aplicatia genereaza o arhiva ZIP. Proiectul se extrage si fisierul `.pbip` se deschide in Power BI Desktop.

## Accesul la SQL Server

Modelul nu executa SQL direct.

Pentru fiecare cerere despre date, aplicatia:

1. selecteaza partea relevanta din schema;
2. genereaza un plan intermediar de query;
3. valideaza tabelele, coloanele, filtrele si agregarile;
4. valideaza relatiile folosite pentru JOIN;
5. genereaza SQL parametrizat;
6. executa query-ul prin Python;
7. transmite rezultatul catre model pentru formularea raspunsului.

Query-urile directe sunt limitate ca numar de randuri.

Pentru dataseturile folosite de rapoarte, limita poate fi eliminata explicit pentru a evita trunchierea datelor.

## Relatii intre tabele

Baza folosita in dezvoltare nu declara toate relatiile prin FOREIGN KEY-uri.

Din acest motiv, aplicatia nu permite modelului sa inventeze conditii de JOIN.

Relatiile care pot fi folosite in query-uri multi-table sunt definite separat si validate de Python.

Pentru alte baze de date, aceste relatii trebuie revizuite sau inlocuite cu relatiile reale ale mediului respectiv.

## Context semantic

Unele concepte nu pot fi interpretate sigur doar din numele tabelelor si coloanelor.

`database_semantic_context.py` permite adaugarea unor informatii precum:

- semnificatia unui camp;
- denumirea folosita pentru un ID;
- reguli business;
- relatii permise.

Pentru un deployment real este preferabil ca aceste informatii sa provina din documentatia bazei, dintr-un dictionar de date sau din SQL Server extended properties.

## Generarea Power BI

Raportul este construit pornind de la proiectul din:

```text
powerbi-agent/templates/blank_powerbi_project/
```

Aplicatia adauga modelul semantic necesar si apoi genereaza modificarile PBIR.

Inainte de aplicare sunt validate:

- fisierele tinta;
- structura JSON;
- schema PBIR;
- referintele la modelul semantic;
- structura paginilor si vizualurilor;
- layout-ul vizualurilor.

Tipurile de vizualuri testate in versiunea curenta sunt:

- card;
- clustered bar chart;
- line chart;
- pie chart;
- slicer;
- table.

## Testing

Directorul `Testing/` contine materialele folosite in etapa de evaluare a modelelor si a pipeline-ului.

### `Testing/Tests/cluster/`

Contine scripturi SLURM / Apptainer pentru construirea imaginilor, descarcarea modelelor si pornirea serverelor vLLM pe HPC.

Scripturile trebuie adaptate la mediul in care sunt rulate. Pentru caile de lucru HPC se foloseste variabila:

```bash
POWERBI_AGENT_ROOT
```

### `Testing/Tests/tests/`

Contine benchmark-uri si rezultate pentru modelele evaluate.

Au fost testate, intre altele:

- Granite 4.1 8B;
- Mistral Small 3.2 24B;
- NVIDIA Nemotron 3 Nano 30B-A3B;
- Qwen3-Coder-30B-A3B-Instruct;
- Qwen3.5-9B;
- Qwen3.6-27B.

Detaliile pentru fiecare rulare sunt in fisierele din `Testing/Tests/tests/`.

### `Testing/Model date/`

Contine copii ale unor proiecte Power BI folosite in rularile de test.

## PowerBI Models

Directorul `PowerBI Models/` contine proiecte PBIP folosite in timpul dezvoltarii pentru:

- verificarea structurii PBIP;
- inspectarea fisierelor PBIR si TMDL;
- obtinerea unor exemple de vizualuri;
- verificare manuala in Power BI Desktop.

Aceste fisiere nu sunt necesare pentru rularea backend-ului, dar au fost pastrate ca material de test si referinta.

## Persistenta conversatiilor

Conversatiile sunt salvate local in:

```text
powerbi-agent/data/conversations.db
```

Fisierul este runtime data si nu trebuie adaugat in Git.

Contextul unei sesiuni este folosit si pentru follow-up-urile referitoare la ultimul raport generat.

## Limitari cunoscute

Versiunea curenta este un prototip functional.

Cateva limitari importante:

- contextul semantic trebuie adaptat la baza de date tinta;
- relatiile care nu sunt declarate prin FOREIGN KEY trebuie configurate explicit;
- JOIN-urile sunt restrictionate intentionat;
- follow-up-ul pentru un raport regenereaza proiectul pe baza starii logice curente;
- modificarile manuale facute ulterior in Power BI Desktop nu sunt sincronizate inapoi in agent;
- interfata web este inca una de dezvoltare;

## Mentenanta

La modificarea proiectului este util sa se pastreze separarea dintre:

- interpretarea semantica, facuta de model;
- regulile obiective si de securitate, implementate in Python;
- metadata business, pastrata separat;
- erorile istorice, transformate in teste de regresie atunci cand este posibil.

In special, query-urile generate de model si modificarile PBIR nu trebuie aplicate fara validare.