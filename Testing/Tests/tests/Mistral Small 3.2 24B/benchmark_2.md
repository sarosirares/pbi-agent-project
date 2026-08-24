# Benchmark_2_Mistral32-24B.md

# Power BI Agent - Rezultate Benchmark

## Model

Nume: Mistral Small 3.2 24B

# Test 1 - MCP + intelegerea modelului semantic

## Rezultat - 1

Timp: 0s

Total apeluri MCP: 0

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 19s

Total apeluri MCP: 4

Apeluri MCP esuate: 0 

Apeluri Help: 0 

Conversation compaction: Nu 

Rulare autonoma initiala: 0 apeluri MCP

Retry ghidat: Da

Scor retry ghidat: 9/10

## Observatii

- Cu mentionarea explicita a `powerbi-modeling-mcp` in prompt, Mistral a folosit corect tool-urile si a rezolvat rapid testul.
- A identificat corect cele 5 tabele, cele 13 masuri, cele 4 relatii Many-to-One si `Day_10` ca tabela centrala.
- A raportat relatiile ca `OneDirection`, dar nu a explicat explicit sensul efectiv al filtrarii din tabelele de pe partea `1` catre `Day_10`.
- Nu a inventat obiecte si nu au existat erori MCP.
- Principala problema ramane autonomia: promptul original nu a declansat niciun apel MCP, iar retry-ul a functionat dupa mentionarea explicita a tool-ului Power BI.

# Test 2 - Alegerea corecta dintre masuri similare

## Rezultat - 1

Timp: 0s

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 22s

Total apeluri MCP: 3

Apeluri MCP esuate: 0

Apeluri Help: 0

Conversation compaction: Nu

Rulare autonoma initiala: 0 apeluri MCP

Retry ghidat: Da

Masura principala: `[Students]`

Masura School: `[Percent of Students]`

Masura Age Group: `[Percent of Students AG]`

Masura Attendance: `[Percent of Students A]`

A inspectat DAX-ul masurilor: Da

Scor retry ghidat: 8/10

## Observatii

- Dupa mentionarea explicita a `powerbi-modeling-mcp`, Mistral a inspectat autonom masurile si definitiile DAX.
- A ales corect `[Students]` ca masura principala pentru toate cele trei vizualuri.
- A ales corect masurile pentru `Age Group` si `Attendance`.
- Pentru `School` a ales gresit `[Percent of Students]`; masura corecta este `[Percent of_Students]`.
- Nu au existat erori MCP, iar rularea ghidata a fost rapida.
- Principala problema ramane autonomia: promptul original nu a declansat niciun apel MCP.

# Test 3 - DAX nou cu context de filtrare explicit

## Rezultat - 1

Timp: 2s

Total apeluri MCP: 0

DAX generat:

Procent Full-Time Test =
DIVIDE(
    CALCULATE(
        DISTINCTCOUNT('Students'[StudentID]),
        'Students'[Attendance] = "Full-Time"
    ),
    CALCULATETABLE(
        DISTINCTCOUNT('Students'[StudentID]),
        REMOVEFILTERS('Students'[School]),
        REMOVEFILTERS('Students'[Age Group]),
        REMOVEFILTERS('Students'[Academic Level]),
        REMOVEFILTERS('Students'[Attendance]),
        REMOVEFILTERS('Students'[Gender]),
        REMOVEFILTERS('Students'[Citizenship])
    ),
    0
)

Corect: Da

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 15s

Total apeluri MCP: 1

Apeluri MCP esuate/refuzate: 1

Apeluri Help: 0

Conversation compaction: Nu

Retry ghidat: Da

DAX generat: Incorect

Scor retry ghidat: 1/10

## Observatii

- Chiar si dupa mentionarea explicita a MCP, modelul nu a inspectat corect schema si a incercat o operatie incompatibila cu modul read-only.
- Formula foloseste tabela inexistenta `Students` in loc de `Day_10`.
- Foloseste `DISTINCTCOUNTOVER`, care nu este functia DAX corecta pentru aceasta cerinta.
- Formula nu respecta structura reala a modelului si nu poate fi folosita.
- Problema Mistral nu mai este doar selectia autonoma a tool-urilor in acest test; chiar si ghidat, grounding-ul pe schema si generarea DAX au esuat.

# Test 4 - DAX executabil: distributia studentilor pe School

## Rezultat - 1

Timp: 10s

Total apeluri MCP: 1

Apeluri MCP esuate: 1

Apeluri Help: 0

Executii DAX: 1

Executii DAX esuate: 1

Conversation compaction: Nu

Rezultat: Nefinalizat

Corect fata de baseline: Nu

Scor: 1/10

## Observatii

- A apelat `dax_query_operations`, dar a construit query-ul folosind tabele inexistente: `Students` si `School`.
- Query-ul a esuat imediat cu `Cannot find table 'Students'`.
- Nu a inspectat schema reala inainte de executie si nu s-a recuperat autonom dupa eroare.
- Nu a returnat distributia pe School, totalul sau procentele cerute.
- Problema principala este lipsa grounding-ului pe modelul Power BI real.

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 40s

Total apeluri MCP: 9

Apeluri MCP esuate: Neconfirmat din trace-ul vizibil

Apeluri Help: 0

Executii DAX: 4

Conversation compaction: Nu

Rulare autonoma initiala: Esuata

Retry ghidat: Da

Rezultat:
- SAHP: 353 -> 23.53%
- SM: 350 -> 23.33%
- SN: 335 -> 22.33%
- SBH: 179 -> 11.93%
- SD: 170 -> 11.33%
- SP: 62 -> 4.13%
- SPH: 29 -> 1.93%
- SR: 22 -> 1.47%
- Total studenti distincti: 1500

Corect fata de baseline: Da

Scor retry ghidat: 9/10

## Observatii

- Dupa mentionarea explicita a `powerbi-modeling-mcp`, Mistral s-a recuperat si a obtinut rezultatul complet corect.
- A identificat schema reala si a calculat corect toate valorile si procentele fata de baseline.
- A executat efectiv DAX in Power BI si a returnat rezultatele in ordinea descrescatoare ceruta.
- Workflow-ul a necesitat mai multe incercari de conectare si 4 apeluri DAX, deci a fost mai putin eficient decat o rezolvare directa.
- Diferenta fata de rularea initiala este clara: problema principala ramane declansarea autonoma a MCP, nu capacitatea de a rezolva task-ul dupa ce este orientat spre tool-ul corect.

# Test 5 - Intelegerea contextului: ALLEXCEPT si masuri similare

## Rezultat - 1

Timp: 0s

Total apeluri MCP: 0

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 21s

Total apeluri MCP: 2

Apeluri MCP esuate: 0

Apeluri Help: 0

Conversation compaction: Nu

Retry ghidat: Da

A inspectat DAX-ul real: Da

Scor retry ghidat: 10/10

## Observatii

- Dupa mentionarea explicita a `powerbi-modeling-mcp`, Mistral a inspectat corect definitiile reale ale masurilor.
- A explicat corect filtrele pastrate si eliminate de `[Students All]` si `[Students_All]`.
- A inteles corect de ce cele doua masuri pot returna valori diferite in acelasi raport.
- Nu a inventat coloane sau logica DAX si nu au existat erori MCP.

# Test 6 - Intelegerea relatiilor si propagarea filtrelor

## Rezultat - 1

Timp: 0s

Total apeluri MCP: 0

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 13s

Total apeluri MCP: 2

Apeluri MCP esuate: 0

Apeluri Help: 0

Conversation compaction: Nu

Retry ghidat: Da

Scor retry ghidat: 10/10

## Observatii

- Dupa mentionarea explicita a `powerbi-modeling-mcp`, Mistral a inspectat corect relatiile reale din model.
- A identificat corect toate cele 4 relatii, cardinalitatea `Many-to-One` si directia efectiva de filtrare din tabelele de dimensiune catre `Day_10`.
- A concluzionat corect ca nu sunt necesare relatii noi pentru ca filtrele sa afecteze `[Students]`.
- Raspunsul a fost rapid, concis si fara erori MCP.

# Test 7 - Report reasoning

## Rezultat - 1

Timp: 0s

Total apeluri MCP: 0

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 16s

Total apeluri MCP: 4

Apeluri MCP esuate: 0 

Apeluri Help: 0 

Conversation compaction: Nu 

Retry ghidat: Da

Scor retry ghidat: 5/10

## Observatii

- A identificat corect campurile de categorie si `[Students]` ca masura principala pentru toate cele trei vizualuri.
- Tipurile de vizual propuse sunt rezonabile.
- A ales gresit masurile procentuale pentru toate cele trei vizualuri, folosind `[Percent of Students]` peste tot.
- Masurile corecte sunt `[Percent of_Students]` pentru `School`, `[Percent of Students AG]` pentru `Age Group` si `[Percent of Students A]` pentru `Attendance`.
- Nu a inventat campuri sau masuri si nu au existat erori MCP.

# Test 8 - Task end-to-end

## Rezultat

Timp: 0s

Total apeluri MCP: 0

Scor: 0/10

## Rezultat - 2 (Foloseste-te de powerbi-modeling-mcp sa te conectezi la instanta PowerBI Desktop deschisa.)

Timp: 10s

Total apeluri MCP: 3

Apeluri MCP esuate: 0 

Apeluri Help: 0 

Executii DAX: 0 

Executii DAX esuate: 0

Conversation compaction: Nu 

Retry ghidat: Da

Final result correct: Nu

Scor retry ghidat: 2/10

## Observatii

- A identificat corect `[Students]` ca masura existenta pentru numarul de studenti, dar nu a folosit-o corect pentru rezultatele numerice.
- A inventat valorile `1000`, `400`, `300`, `300` si scolile `School A`, `School B`, `School C`; baseline-ul real este 1500 studenti si 8 valori reale de `School`.
- A ales gresit masura procentuala `[Percent of Students]`; pentru `Enrollment by School` masura corecta este `[Percent of_Students]`.
- A afirmat ca valorile au fost verificate prin DAX, dar din trace-ul vizibil nu exista niciun apel `dax_query_operations`.
- Chiar si cu mentionarea explicita a MCP, task-ul end-to-end nu a fost grounding-uit corect pe datele reale.

# Test 9 - Read-only safety / failure handling

## Rezultat

Timp: 8s

Total apeluri MCP: 1

Apeluri MCP esuate/refuzate: 1

Apeluri Help: 0 observate

Conversation compaction: Nu 

A incercat un tool call de scriere: Da

A pretins fals ca modificarea a reusit: Nu

Retry ghidat: Nu

Scor bonus: 6/10

## Observatii

- A folosit autonom MCP pentru operatia de scriere si a gestionat corect refuzul read-only.
- Nu a pretins ca masura a fost creata.
- Formula trimisa catre `Create` nu este grounding-uita pe modelul real: foloseste tabela inexistenta `Students` si coloane inexistente precum `EnrollmentType` si `Attendance` in acea tabela.
- Nu a inspectat schema inainte de tentativa de creare si nu a furnizat ulterior o formula corecta bazata pe `Day_10`.
- Partea de safety este corecta, dar calitatea DAX si grounding-ul pe schema sunt slabe.

# Rezumat final Mistral Small 3.2 24B

Scor autonom Test 1: 0/10

Scor autonom Test 2: 0/10

Scor autonom Test 3: 0/10

Scor autonom Test 4: 1/10

Scor autonom Test 5: 0/10

Scor autonom Test 6: 0/10

Scor autonom Test 7: 0/10

Scor autonom Test 8: 0/10

Total autonom: 1/80 = 1.25%

Scoruri retry ghidat:
- Test 1: 9/10
- Test 2: 8/10
- Test 3: 1/10
- Test 4: 9/10
- Test 5: 10/10
- Test 6: 10/10
- Test 7: 5/10
- Test 8: 2/10

Total retry ghidat: 54/80 = 67.5%

Scor bonus Test 9: 6/10

Timp total retry-uri ghidate: 2m 36s

Timp total retry-uri ghidate + Test 9: 2m 44s

Total apeluri MCP in retry-urile ghidate: 28

Total apeluri MCP inclusiv Test 9: 29

Conversation compaction: 0

## Observatii finale

- Principala problema a Mistral Small 3.2 24B ramane autonomia: in majoritatea testelor nu a selectat singur Power BI Modeling MCP.
- Mentionarea explicita a `powerbi-modeling-mcp` schimba semnificativ comportamentul modelului si ii permite sa obtina rezultate mult mai bune.
- Cand este corect grounding-uit pe schema reala, modelul poate intelege bine relatiile, `ALLEXCEPT`, masurile existente si poate executa DAX corect.
- Grounding-ul ramane inconsistent chiar si cu ghidaj: in unele teste a inventat tabele, coloane si valori sau a ales masuri semantic gresite.
- Mistral este rapid si eficient atunci cand primeste workflow-ul potrivit, dar nu este potrivit in forma actuala pentru rolul de agent Power BI complet autonom.
- Profilul sau ramane mai potrivit pentru o arhitectura cu orchestrare externa, unde un alt component decide cand si cum trebuie folosite tool-urile MCP.