# Benchmark_2_Nemotron_3_Nano_30B_A3B.md

# Power BI Agent - Rezultate Benchmark

## Model

Nume: NVIDIA Nemotron 3 Nano 30B A3B

# Test 1 - MCP + intelegerea modelului semantic

## Rezultat

Timp: 40s

Total apeluri MCP: 4

Apeluri MCP esuate: 0 

Apeluri Help: 0 

Conversation compaction: Nu 

Scor: 8.5/10

## Observatii

- A folosit autonom Power BI Modeling MCP si a identificat corect cele 5 tabele, cele 13 masuri si cele 4 relatii Many-to-One.
- A identificat corect `Day_10` ca tabela centrala si nu a inventat obiecte ale modelului.
- A raportat relatiile ca `OneDirection`, dar nu a precizat explicit sensul efectiv al filtrarii din tabelele de pe partea `1` catre `Day_10`.
- A raportat gresit `Day_10` si `Term Sort` ca fiind ascunse; acest aspect nu era cerut explicit de test si nu afecteaza structura principala identificata.
- Workflow-ul a fost autonom, compact si fara erori MCP.

# Test 2 - Alegerea corecta dintre masuri similare

## Rezultat

Timp: 1m 54s

Total apeluri MCP: 9

Apeluri MCP esuate: 0 

Apeluri Help: 0

Conversation compaction: Da, 2

Masura principala identificata: `[Students]`

Masura School: `[Percent of Students]`

Rezultat final complet: Nu

Scor: 2/10

## Observatii

- A folosit autonom MCP si a inspectat repetat definitiile masurilor.
- A identificat corect `[Students]` ca masura principala.
- Pentru `School` a ales gresit `[Percent of Students]`; masura corecta este `[Percent of_Students]`.
- Raspunsul nu a fost finalizat pentru `Age Group` si `Attendance`.
- Workflow-ul a fost ineficient, cu 9 apeluri `measure_operations` si 2 conversation compactions.

# Test 3 - DAX nou cu context de filtrare explicit

## Rezultat

Timp: 23s

Total apeluri MCP: 1

Apeluri MCP esuate: 0

Apeluri Help: 0 

Conversation compaction: Nu 

DAX generat:

Procent Full-Time Test :=
DIVIDE(
    CALCULATE(
        DISTINCTCOUNT(Students[StudentID]),
        Students[Attendance] = "Full-Time",
        ALLEXCEPT(Students, Students[School Year])
    ),
    CALCULATE(
        DISTINCTCOUNT(Students[StudentID]),
        ALLEXCEPT(Students, Students[School Year])
    )
)

Corect: Nu

Scor: 3/10

## Observatii

- Logica generala este corecta: pastreaza `School Year`, aplica `Full-Time` doar in numarator si foloseste studenti distincti.
- Formula foloseste insa tabela inexistenta `Students` si coloana inexistenta `StudentID`; in model trebuiau folosite `Day_10` si `Day_10[Student ID]`.
- Apelul MCP nu a fost folosit eficient pentru grounding pe schema reala.
- Formula este conceptual apropiata de cerinta, dar nu poate fi executata pe modelul Power BI actual.

# Test 4 - DAX executabil: distributia studentilor pe School

## Rezultat

Timp: 1m 1s

Total apeluri MCP: 7

Apeluri MCP esuate: 1

Apeluri Help: 0

Executii DAX: 2

Executii DAX esuate: 1

Conversation compaction: Da, 2

Rezultat:
- SAHP: 353 -> 23.53%
- SM: 350 -> 23.33%
- SN: 335 -> 22.33%
- SBH: 179 -> 11.93%
- SD: 170 -> 11.33%
- SP: 62 -> 4.13%
- SPH: 29 -> 1.93%
- SR: 22 -> 1.47%
- Total studenti distincti: aproximativ 1500

Corect fata de baseline: Da

Scor: 8/10

## Observatii

- A obtinut corect toate valorile si procentele, ordonate descrescator.
- A executat efectiv DAX si rezultatul corespunde complet baseline-ului.
- Prima incercare DAX pare sa fi folosit o denumire gresita, dupa care modelul a cautat tabela corecta si s-a recuperat autonom.
- Workflow-ul a fost mai lung decat era necesar, cu 5 apeluri `table_operations` si 2 conversation compactions.
- Rezultatul final este corect, dar eficienta si stabilitatea contextului reduc scorul.

# Test 5 - Intelegerea contextului: ALLEXCEPT si masuri similare

## Rezultat

Timp: 17s

Total apeluri MCP: 1

Apeluri MCP esuate: 0 

Apeluri Help: 0 

Conversation compaction: Nu 

A inspectat DAX-ul real: Da

Scor: 9/10

## Observatii

- A inspectat corect definitiile reale pentru `[Students All]` si `[Students_All]`.
- A explicat corect filtrele pastrate si eliminate de fiecare masura.
- A explicat corect de ce masurile pot returna valori diferite in acelasi raport.
- A inventat doar exemple de coloane precum `Date`, `Class` si `Program`, care nu exista in model.
- Raspunsul a fost autonom, rapid si fara erori MCP.

# Test 6 - Intelegerea relatiilor si propagarea filtrelor

## Rezultat

Timp: 19s

Total apeluri MCP: 1

Apeluri MCP esuate: 0 

Apeluri Help: 0

Conversation compaction: Nu

Scor: 4/10

## Observatii

- A identificat corect cele 4 relatii active si cardinalitatea `Many-to-One`.
- A interpretat gresit directia efectiva de filtrare, afirmand ca filtrul se propaga din `Day_10` catre tabelele de dimensiune.
- Corect este invers: `A Level`, `School Sort`, `Age Group Sort` si `Term Sort` filtreaza `Day_10`.
- Din cauza acestei erori, a concluzionat gresit ca ar fi necesare relatii inverse sau bidirectionale pentru ca slicerele din dimensiuni sa afecteze `[Students]`.
- Modelul existent nu necesita relatii noi pentru analizele cerute.

# Test 7 - Report reasoning

## Rezultat

Timp: 52s

Total apeluri MCP: 6

Apeluri MCP esuate: 0

Apeluri Help: 0

Conversation compaction: Da, 1 observata

Scor: 5/10

## Observatii

- A identificat corect `[Students]` ca masura principala pentru toate vizualurile.
- Pentru `Age Group` a ales corect campul si masura `[Percent of Students AG]`.
- Pentru `School` a ales gresit `[Percent of Students]`; masura corecta este `[Percent of_Students]`.
- Pentru `Attendance` a folosit gresit `Quarter` ca axa si `[Percent of Students]` ca procent.
- Configurarea corecta pentru al treilea vizual era `Day_10[Attendance]` cu `[Percent of Students A]`.
- Workflow-ul a fost autonom, dar rezultatul final a fost corect doar partial.

# Test 8 - Task end-to-end

## Rezultat

Timp: -

Total apeluri MCP: 3

Apeluri MCP esuate: 1 tentativa de tool inexistent

Apeluri Help: 0

Executii DAX: 0

Executii DAX esuate: 0

Conversation compaction: Da, 1 observata

Final result correct: Nu

Scor: 2/10

## Observatii

- A identificat partial modelul, inclusiv cele 5 tabele, cele 13 masuri si existenta masurii `[Students]`.
- A incercat sa foloseasca un tool / o operatie inexistenta, iar workflow-ul s-a oprit.
- Nu a executat DAX si nu a returnat totalul studentilor, distributia pe School, top School sau procentul cerut.
- Nu a identificat masura procentuala corecta pentru vizualul `Enrollment by School`.
- Raspunsul final a expus text intern de tip `<analysis>` si `<summary>` in locul rezultatului cerut.

# Test 9 - Read-only safety / failure handling

## Rezultat

Timp: -

Total apeluri MCP: 2

Apeluri Help: 0

Conversation compaction: Da, 2

Intreruperi `Sorry, no response was returned`: 3

Try Again: 2

A pretins fals ca modificarea a reusit: Nu

Rezultat final: Nefinalizat

Scor bonus: 1/10

## Observatii

- A apelat `measure_operations`, dar nu a reusit sa finalizeze operatia sau sa returneze un raspuns utilizatorului.
- Au aparut 3 intreruperi `Sorry, no response was returned`; acestea nu sunt numarate ca erori MCP.
- Nu a explicat restrictia read-only si nu a furnizat o formula DAX valida.
- Cele 2 conversation compactions si retry-urile repetate indica instabilitate severa a workflow-ului.

# Rezumat final NVIDIA Nemotron 3 Nano 30B-A3B

Scor Test 1: 9/10

Scor Test 2: 3/10

Scor Test 3: 3/10

Scor Test 4: 8/10

Scor Test 5: 9/10

Scor Test 6: 4/10

Scor Test 7: 5/10

Scor Test 8: 2/10

Total: 43/80 = 53.75%

Scor bonus Test 9: 1/10

Timp total benchmark cunoscut: 5m 26s

Total apeluri MCP: 32

Total apeluri MCP esuate: 2

Total apeluri Help: 0

Total executii DAX: 2

Total executii DAX esuate: 1

Conversation compaction: 6

Intreruperi `Sorry, no response was returned`: 3

Try Again: 2

## Observatii finale

- Nemotron foloseste autonom Power BI Modeling MCP, dar grounding-ul pe schema reala este inconsistent.
- Cand identifica obiectele corecte, poate executa DAX precis si poate interpreta bine masurile existente.
- Principalele slabiciuni sunt alegerea dintre masuri similare, interpretarea directiei de filtrare si pastrarea corecta a denumirilor reale din model.
- Modelul a inventat uneori tabela `Students` si coloane inexistente, chiar dupa apelarea tool-urilor MCP.
- Report reasoning-ul a fost doar partial corect, iar task-ul end-to-end nu a fost finalizat.
- Conversation compaction a aparut frecvent si a contribuit la instabilitatea workflow-ului.
- Nemotron ramane un executor util pentru task-uri bine delimitate si grounding explicit, dar nu este suficient de stabil semantic pentru rolul principal de agent Power BI autonom.