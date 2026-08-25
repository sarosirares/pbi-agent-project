# Power BI AI Agent

Aplicatie pentru interogarea unei baze de date SQL Server si generarea de rapoarte Power BI din cereri formulate in limbaj natural.

Aplicatia foloseste Qwen3.6-27B prin vLLM. Modelul, backend-ul FastAPI si SQL Server ruleaza pe infrastructura HPC, iar utilizatorul acceseaza aplicatia din browser prin SSH.

## Repository

```text
pbi-agent-project/
    powerbi-agent/       aplicatia
    Testing/             teste si benchmark-uri
    PowerBI Models/      proiecte Power BI folosite pentru testare
    README.md
```

Codul principal este in `powerbi-agent/`.

## Cerinte

Pe infrastructura HPC sunt necesare:

- SLURM;
- Apptainer;
- Qwen3.6-27B;
- vLLM;
- SQL Server;
- Python;
- ODBC Driver 18 for SQL Server;
- Node.js;
- Power BI Report Authoring CLI.

Pe calculatorul utilizatorului sunt necesare:

- SSH;
- un browser web;
- Power BI Desktop pentru deschiderea rapoartelor generate.

Backend-ul si SQL Server nu trebuie sa ruleze local pe calculatorul utilizatorului.

## Configurare

Aplicatia foloseste un fisier `.env`.

Exemplu:

```env
VLLM_BASE_URL=http://127.0.0.1:8000/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL=Qwen3.6-27B

SQLSERVER_SERVER=127.0.0.1,1433
SQLSERVER_DATABASE=<DATABASE_NAME>
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_TRUSTED_CONNECTION=no
SQLSERVER_USERNAME=<USERNAME>
SQLSERVER_PASSWORD=<PASSWORD>
SQLSERVER_ENCRYPT=yes
SQLSERVER_TRUST_SERVER_CERTIFICATE=yes
```

Contul SQL folosit de aplicatie trebuie sa aiba acces read-only.

## Pornire

### Prima configurare

Pentru SQL Server:

```bash
cd sqlserver
cp sqlserver.env.example sqlserver.env
chmod 600 sqlserver.env
```

Se completeaza `sqlserver.env` cu parola SQL Server.

Pentru backend se copiaza:

```bash
cd ../powerbi-agent
cp .env.example .env
chmod 600 .env
```

si se completeaza configuratia SQL Server.

Imaginile Apptainer se construiesc o singura data:

```bash
cd powerbi-agent
sbatch build_backend.sh
```

```bash
cd ../sqlserver
sbatch build_sqlserver.sh
```

### Pornirea unei sesiuni de test

Se pornesc cele trei componente:

```bash
cd sqlserver
sbatch run_sqlserver.sh
```

```bash
cd ../Testing/Tests/cluster
sbatch run_vllm_qwen36_27b.sh
```

```bash
cd ../../../powerbi-agent
sbatch run_backend.sh
```

Job-urile trebuie sa ramana active pe durata testarii.

Backend-ul poate fi verificat cu:

```bash
curl http://<COMPUTE_NODE>:8080/health
```

Raspuns asteptat:

```json
{"status":"ok"}
```

## Acces din browser

De pe calculatorul client se creeaza un SSH tunnel catre backend:

```bash
ssh -N -L 8081:<COMPUTE_NODE>:8080 <HPC_HOST>
```

Aplicatia poate fi apoi accesata la:

```text
http://127.0.0.1:8081
```

## Utilizare

Aplicatia accepta intrebari in limbaj natural, de exemplu:

```text
Care este valoarea totala a taxelor studentilor?
```

sau:

```text
Care este rata de promovare pentru fiecare disciplina?
```

Conversatiile sunt pastrate intre sesiuni si pot fi sterse direct din sidebar.

## Generarea unui raport

Exemplu:

```text
Creeaza un raport Power BI despre taxele studentilor, cu valoarea totala,
distributia pe categorii si un slicer dupa tipul de finantare.
```

Fluxul este:

```text
cerere
-> planificare
-> generare si validare SQL
-> afisare SQL in chatbot
-> Approve / Reject
-> generare raport
```

Raportul este generat numai dupa `Approve`.

Dupa aprobare este folosit acelasi query care a fost afisat si verificat. SQL-ul nu este regenerat de model.

Rezultatul este un proiect Power BI (`PBIP`) livrat ca arhiva ZIP.

## Deschiderea raportului in Power BI Desktop

SQL Server ruleaza pe HPC, iar Power BI Desktop ruleaza pe calculatorul utilizatorului.

Pentru refresh-ul raportului se creeaza un al doilea SSH tunnel:

```bash
ssh -N -L 1433:<COMPUTE_NODE>:1433 <HPC_HOST>
```

In Power BI Desktop conexiunea este:

```text
127.0.0.1,1433
```

La autentificare se foloseste optiunea `Database` si credentialele SQL Server read-only furnizate pentru testare.

## Functionalitati

Versiunea curenta suporta:

- intrebari in limbaj natural despre SQL Server;
- agregari, filtre, procente si metrici derivate;
- query-uri multi-table pe relatii aprobate;
- follow-up-uri in aceeasi conversatie;
- validarea query-urilor SQL;
- aprobarea sau respingerea query-ului unui raport;
- generarea proiectelor Power BI;
- generarea arhivelor PBIP ZIP;
- card, bar chart, line chart, pie chart, slicer si table;
- persistenta si stergerea conversatiilor.

## Testing

Directorul `Testing/` contine scripturile si rezultatele folosite pentru evaluarea modelelor.

Modelul folosit in versiunea curenta este:

```text
Qwen3.6-27B
```

## Limitari

Versiunea curenta este un prototip.

- componentele HPC ruleaza ca job-uri SLURM, nu ca servicii permanente;
- tunelurile SSH trebuie sa ramana active in timpul testarii;
- Power BI Desktop este necesar pentru deschiderea raportului final;
- relatiile si contextul semantic trebuie adaptate pentru o baza de date noua;
- modificarile facute manual ulterior in Power BI Desktop nu sunt sincronizate inapoi in agent.