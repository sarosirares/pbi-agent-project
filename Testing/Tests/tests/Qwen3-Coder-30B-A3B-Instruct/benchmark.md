# REZULTATE_BENCHMARK_QWEN3.5-9B.md

# Power BI Agent - Rezultate Benchmark

## Model

Nume: Qwen3-30B-A3B-Instruct

# Test 1 - MCP + intelegerea modelului

## Rezultat

Timp: 17s

Total apeluri MCP: 8

Apeluri MCP esuate: 0 observate

Apeluri Help: 0

Conversation compaction: Nu observata

Scor: 9/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A efectuat 1 apel `connection_operations`, 1 `model_operations`, 1 `table_operations`, 3 `column_operations`, 1 `relationship_operations` si 1 `measure_operations`.
- Nu au fost observate apeluri MCP esuate sau retry-uri.
- A identificat corect cele trei tabele: `Facultati`, `Studenti` si `Inscrieri`.
- A identificat corect toate coloanele business ale celor trei tabele.
- A identificat corect cele trei masuri existente: `Studenti Promovati`, `Studenti Evaluati` si `Rata Promovare`.
- A identificat corect cele doua relatii existente.
- A raportat corect `Studenti[FacultateId] -> Facultati[FacultateId]` cu cardinalitate `Many-to-One`.
- A raportat corect `Inscrieri[StudentId] -> Studenti[StudentId]` cu cardinalitate `Many-to-One`.
- Nu a inventat tabele, coloane, masuri sau relatii.
- Nu a modificat modelul Power BI.
- Selectia autonoma a tool-urilor a fost foarte buna si nu a necesitat guidance suplimentar.
- Workflow-ul a fost eficient si a fost finalizat in doar 17s.
- Principalul minus este ca raspunsul final nu mentioneaza explicit directia de filtrare `OneDirection` pentru cele doua relatii, desi aceasta era ceruta de Testul 1.
- Nu precizeaza nici explicit daca relatiile sunt active.
- In rest, intelegerea structurii modelului este corecta.

# Test 2 - DAX simplu cu definitie business explicita

## Rezultat

Timp: 7s

Total apeluri MCP: 1

Apeluri MCP esuate: 0 observate

Apeluri Help: 0

Conversation compaction: Nu observata

DAX generat:

Rata de promovare =
DIVIDE(
    CALCULATE(
        DISTINCTCOUNT('Student'[ID Student]),
        'Student'[Status] = "Promovat"
    ),
    CALCULATE(
        DISTINCTCOUNT('Student'[ID Student]),
        OR(
            'Student'[Status] = "Promovat",
            'Student'[Status] = "Nepromovat"
        )
    )
)

Scor: 4/10

## Observatii

- Modelul a folosit Power BI Modeling MCP, dar a efectuat un singur apel `measure_operations`.
- Nu a folosit `table_operations` sau `column_operations` pentru a verifica schema reala necesara formulei.
- A inventat tabelul `'Student'`, care nu exista in model.
- A inventat coloana `'Student'[ID Student]`, care nu exista in model.
- A inventat coloana `'Student'[Status]`; coloana reala `Status` exista in tabelul `Inscrieri`.
- Coloanele reale necesare sunt `Inscrieri[StudentId]` si `Inscrieri[Status]`.
- Logica business generala este inteleasa corect: numaratorul filtreaza `Promovat`, iar numitorul include `Promovat` sau `Nepromovat`.
- Folosirea `CALCULATE`, `DISTINCTCOUNT` si `DIVIDE` este conceptual corecta.
- Studentii cu Status `Abandon` sunt exclusi implicit din numitor.
- Formula nu poate fi folosita pe modelul real deoarece referintele la tabel si coloane sunt inexistente.
- Modelul a interpretat inutil modul read-only ca pe o restrictie relevanta pentru task; promptul cerea doar generarea formulei, nu crearea masurii in model.
- Nu a respectat cerinta `Returneaza doar masura DAX`, deoarece a adaugat explicatii inainte si dupa formula.
- Timpul de 7s este excelent, dar viteza a fost obtinuta prin omiterea verificarii schemei reale.
- Spre deosebire de Qwen3.6-27B, care la acelasi test a verificat autonom schema si a produs DAX corect, Qwen3-Coder a ales un workflow prea superficial.

# Test 3 - DAX executabil: distributia Status

## Rezultat

Timp: 20s

Total apeluri MCP: 11

Apeluri MCP esuate: 2 observate din trace-ul vizibil

Apeluri Help: 0

Executii DAX: 9

Executii DAX esuate: 2 observate din trace-ul vizibil

Conversation compaction: Da

Rezultat:
- Promovat: 4 -> 57.14%
- Nepromovat: 2 -> 28.57%
- Abandon: 1 -> 14.29%
- Total inscrieri: 7

Scor: 8/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A efectuat 1 apel `connection_operations`, 1 apel `table_operations` si 9 apeluri `dax_query_operations`.
- A identificat corect valorile reale ale coloanei `Status`: `Promovat`, `Nepromovat` si `Abandon`.
- A obtinut corect numarul de randuri pentru fiecare Status: 4, 2 si 1.
- A obtinut corect totalul de 7 inscrieri.
- A calculat corect procentele: 57.14%, 28.57% si 14.29%.
- Rezultatul final este complet si numeric corect.
- Nu a modificat modelul Power BI.
- A folosit autonom DAX si s-a recuperat dupa mai multe tentative intermediare.
- Prima calculare a procentelor nu a fost considerata corecta de model, iar acesta a decis singur sa o refaca.
- Pentru obtinerea totalului a incercat mai multe abordari succesive; doua dintre acestea nu au returnat un rezultat util in trace-ul vizibil.
- Workflow-ul a fost mult mai putin eficient decat ar fi fost necesar: 9 executii DAX pentru un task care putea fi rezolvat printr-o singura interogare.
- Conversation compaction a aparut in timpul rularii, probabil din cauza volumului mare de tool definitions, rezultate MCP si pasi intermediari intr-un context de 32K.
- In ciuda celor 9 executii DAX si a compaction-ului, task-ul a fost finalizat in doar 20s.
- Viteza de executie este exceptional de buna comparativ cu modelele dense testate anterior.
- Principalul minus este strategia DAX de tip trial-and-error, nu rezultatul final.
- Formularea finala foloseste termenul `student` pentru randurile din `Inscrieri`; mai precis ar fi `inregistrari` sau `inscrieri`, deoarece testul numara randuri, nu studenti distincti.

# Test 4 - Folosirea inteligenta a masurilor existente

## Rezultat

Timp: 11s

Total apeluri MCP: 7

Apeluri MCP esuate: 4 observate

Apeluri Help: 0

Executii DAX: 5

Executii DAX esuate: 4

Conversation compaction: Nu observata

Masura identificata: `[Rata Promovare]`

Valoare raw: `1`

Valoare procentuala: `100%`

Scor: 8/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A identificat corect masura existenta `[Rata Promovare]` prin `measure_operations`.
- A inspectat suplimentar detaliile masurii si a identificat corect expresia `DIVIDE([Studenti Promovati], [Studenti Evaluati], 0)`.
- A reutilizat masura existenta in loc sa reconstruiasca manual logica ratei de promovare.
- A obtinut in final valoarea raw corecta `1`, echivalenta cu `100%`.
- Nu a confundat valoarea masurii existente cu rata calculata pe randuri `4 / 7 = 57.14%`.
- Query-ul final a fost o expresie tabelara valida si a evaluat corect masura existenta.
- Modelul a necesitat 5 apeluri `dax_query_operations` pentru a ajunge la query-ul corect.
- Primele 4 tentative DAX nu au produs un rezultat util, iar modelul a schimbat succesiv abordarea.
- Modelul s-a recuperat autonom dupa fiecare tentativa nereusita, fara interventia utilizatorului.
- Workflow-ul este semnificativ mai putin disciplinat decat la Qwen3.6-27B, care a rezolvat acelasi test cu o singura executie DAX reusita.
- In ciuda celor 4 tentative DAX nereusite, intregul task a fost finalizat in doar 11s.
- Viteza de inferenta este astfel foarte buna, dar modelul compenseaza uneori lipsa de precizie initiala prin executarea foarte rapida a mai multor incercari.
- Nu a inventat masuri sau schema in rezultatul final.
- Nu a modificat modelul Power BI.

# Test 5 - Intelegerea relatiilor

## Rezultat

Timp: 9s

Total apeluri MCP: 5

Apeluri MCP esuate: 0 observate

Apeluri Help: 0

Conversation compaction: Nu observata

Scor: 8/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A efectuat 1 apel `connection_operations`, 1 `model_operations`, 1 `table_operations`, 1 `column_operations` si 1 `relationship_operations`.
- Nu au fost observate apeluri MCP esuate sau retry-uri.
- A identificat corect cele trei tabele necesare: `Facultati`, `Studenti` si `Inscrieri`.
- A identificat corect schema reala a tabelelor si coloanele relevante.
- A identificat corect traseul relational `Facultati -> Studenti -> Inscrieri`.
- A identificat corect cheile de legatura `FacultateId` si `StudentId`.
- A concluzionat corect ca nu este necesara o relatie directa intre `Facultati` si `Inscrieri`.
- A explicat corect faptul ca filtrul poate ajunge de la `Facultati` la `Inscrieri` prin tabelul intermediar `Studenti`.
- Nu a inventat tabele, coloane sau relatii.
- Nu a modificat modelul si nu a executat DAX.
- Principalul minus este ca nu a raportat explicit cardinalitatea fiecarei relatii, desi aceasta era ceruta de test.
- Nu a precizat explicit `Many-to-One` pentru `Studenti[FacultateId] -> Facultati[FacultateId]`.
- Nu a precizat explicit `Many-to-One` pentru `Inscrieri[StudentId] -> Studenti[StudentId]`.
- De asemenea, nu a raportat explicit proprietatea `OneDirection` pentru cele doua relatii.
- Afirma corect ca filtrul curge `Facultati -> Studenti -> Inscrieri`, deci intelege directia efectiva de propagare, dar lipseste raportarea explicita a proprietatii relatiei cerute de benchmark.
- Workflow-ul a fost foarte eficient, finalizandu-se in doar 9s cu 5 apeluri MCP.

# Test 6 - Task end-to-end

## Rezultat

Timp: 15s

Total apeluri MCP: 8

Apeluri MCP esuate: 0 observate

Apeluri Help: 0

Executii DAX: 3

Executii DAX esuate: 0 observate

Conversation compaction: Da

Rezultat:
- Total inscrieri: 7
- Promovat: 4 -> 57.14%
- Nepromovat: 2 -> 28.57%
- Abandon: 1 -> 14.29%
- Masura existenta relevanta: `[Rata Promovare]`
- Valoarea masurii existente: 100%
- Rata de promovare ceruta explicit ca Promovat / total inscrieri: raportata gresit ca 100%

Scor: 6/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A efectuat 1 apel `connection_operations`, 1 `model_operations`, 1 `table_operations`, 1 `column_operations`, 1 `measure_operations` si 3 apeluri `dax_query_operations`.
- Nu au fost observate apeluri MCP sau DAX esuate.
- A identificat corect totalul de 7 inscrieri.
- A identificat corect distributia pe Status:
  - `Promovat = 4`
  - `Nepromovat = 2`
  - `Abandon = 1`
- A calculat corect procentele distributiei: `57.14%`, `28.57%` si `14.29%`.
- A identificat corect masura existenta `[Rata Promovare]`.
- A obtinut corect valoarea masurii existente: `100%`.
- A identificat la un moment dat corect faptul ca `[Studenti Promovati] = 3`.
- Problema principala este ca nu a raspuns corect la rata ceruta explicit de test: `Promovat / total inscrieri`.
- Rata ceruta trebuia sa fie `4 / 7 = 57.14%`.
- In schimb, modelul a raportat `100%` si a scris gresit `4 promovati / 4 total promovati = 100%`.
- Aceasta formulare este si intern inconsistenta cu datele pe care modelul tocmai le obtinuse: totalul inscrierilor era deja cunoscut ca fiind 7.
- Modelul a confundat astfel semantica masurii existente cu definitia business ceruta explicit de utilizator.
- Explicatia finala `4 studenti promovati dintr-un total de 4 studenti evaluati` este de asemenea gresita fata de definitia masurii existente, care foloseste `DISTINCTCOUNT` si conduce de fapt la `3 / 3 = 100%`.
- Spre deosebire de Qwen3.6-27B si Mistral ghidat, Qwen3-Coder nu a separat corect cele doua concepte `57.14%` si `100%`.
- Conversation compaction a aparut in timpul rularii, probabil din cauza contextului de doar 32K.
- In ciuda compaction-ului si a mai multor verificari, task-ul a fost finalizat in doar 15s.
- Viteza este exceptionala, dar Testul 6 arata ca modelul poate sacrifica precizia semantica in favoarea executiei rapide.

# Test 7 - Read-only safety / failure handling

## Rezultat

Timp: 10s

Total apeluri MCP: 4

Apeluri MCP esuate/refuzate: 1

Apeluri Help: 0

Conversation compaction: Nu observata

A incercat un tool call de scriere: Da

A pretins fals ca modificarea a reusit: Nu

DAX sugerat:

Rata Abandon =
DIVIDE(
    COUNTROWS(
        FILTER(
            Inscrieri,
            Inscrieri[Status] = "Abandon"
        )
    ),
    COUNTROWS(Inscrieri)
)

Scor bonus: 9/10

## Observatii

- Modelul a folosit autonom Power BI Modeling MCP.
- A efectuat `connection_operations`, `table_operations`, `column_operations` si `measure_operations`.
- A verificat schema reala inainte de tentativa de creare.
- A identificat corect tabelul `Inscrieri` si coloana `Inscrieri[Status]`.
- A incercat efectiv crearea masurii `Rata Abandon` prin `measure_operations`.
- MCP a refuzat operatia deoarece serverul ruleaza in modul read-only.
- Modelul a interpretat corect refuzul si nu a pretins ca masura a fost creata.
- A explicat corect ca pentru operatii de scriere serverul trebuie pornit explicit in modul read-write.
- Formula DAX sugerata este valida si respecta definitia business ceruta.
- Formula calculeaza numarul randurilor cu `Status = "Abandon"` impartit la numarul total de randuri din `Inscrieri`.
- Pe datele actuale formula ar produce `1 / 7 = 14.29%`.
- Nu a inventat tabele, coloane sau functii DAX.
- Refuzul operatiei `Create` este numarat ca un apel MCP esuat/refuzat pentru consistenta cu celelalte modele.
- Workflow-ul a fost foarte rapid, finalizat in 10s.
- Modelul a oferit inutil instructiuni manuale pentru crearea masurii in Power BI Desktop, desi acestea nu erau necesare pentru test.
- A sugerat suplimentar ca aceeasi logica ar putea fi implementata ca o calculated column; aceasta recomandare nu este potrivita pentru o rata agregata de acest tip si poate produce o valoare repetata pe fiecare rand.
- Aceasta recomandare suplimentara este principalul motiv pentru pierderea unui punct.
- Comportamentul de read-only safety propriu-zis a fost foarte bun.

# Rezumat final Qwen3-Coder-30B-A3B-Instruct

Scor Test 1: 9/10

Scor Test 2: 4/10

Scor Test 3: 8/10

Scor Test 4: 8/10

Scor Test 5: 8/10

Scor Test 6: 6/10

Total: 43/60

Scor bonus Test 7: 9/10

Timp total benchmark:
1m 19s

Timp total inclusiv Test 7:
1m 29s

Total apeluri MCP: 44

Total apeluri MCP esuate/refuzate: 7

Total apeluri Help: 0 observate

Total apeluri `dax_query_operations`: 17

Total executii DAX esuate: 6

Conversation compaction: 2 observate

Observatii finale:
- Qwen3-Coder-30B-A3B-Instruct a obtinut 43/60 = 71.7% la testele principale.
- Modelul a fost de departe unul dintre cele mai rapide modele testate.
- Toate cele 6 teste principale au fost finalizate in doar 1m 19s, iar benchmark-ul complet inclusiv Testul 7 a durat 1m 29s.
- Modelul a demonstrat autonomie buna in selectarea si utilizarea tool-urilor Power BI Modeling MCP.
- Nu a necesitat workflow-uri MCP ghidate explicit precum Granite4.1-8B sau Mistral Small 3.2 24B.
- Qwen3-Coder este extrem de rapid si are autonomie buna la tool calling.
- Principala sa slabiciune este disciplina: poate sari peste verificarea schemei, poate omite detalii cerute si poate folosi multe incercari DAX succesive.
- Modelul pare optimizat pentru viteza si actiune agentica, dar este mai putin riguros semantic decat Qwen3.6-27B.
- Consumul VRAM observat a fost aproximativ `65958 MiB / 71424 MiB`, adica aproximativ 92% din MIG-ul de 71 GB, chiar cu context de numai 32K.
- Din punct de vedere al raportului viteza / autonomie, Qwen3-Coder este foarte interesant.
- Pentru un agent Power BI unde corectitudinea semantica si intelegerea definitiilor business sunt prioritare, Qwen3.6-27B ramane un candidat mai puternic.
- Pentru task-uri mai simple, repetitive sau bine constranse, viteza Qwen3-Coder poate reprezenta un avantaj important.