import json
from typing import Any

from intent_models import IntentResult
from llm_client import VLLMClient


CLASSIFICATION_PROMPT = """
Clasifica mesajul utilizatorului pentru o aplicatie care lucreaza cu
Power BI si cu baza de date SQL Server configurata prin aplicatie.

Aplicatia poate avea in sesiunea curenta un raport Power BI generat anterior.

Intentii permise:

- general_question:
  intrebare generala despre Power BI, SQL, raportare sau despre
  capabilitatile si modul general de lucru al aplicatiei.
  Include intrebari despre ce poate face aplicatia, daca poate folosi baza de date configurata
  sau cum ar aborda in general crearea unui raport, atunci cand utilizatorul
  NU cere inspectarea efectiva a schemei sau a datelor;

- project_question:
  intrebare despre ultimul raport Power BI generat in sesiunea curenta.
  Include intrebari despre sursele folosite pentru acel raport, modelul
  semantic creat, tabele, coloane, masuri, pagini, vizualizari sau campurile
  folosite in raport;

- database_question:
  cerere de inspectare a STRUCTURII sau METADATA bazei de date configurate.
  Include intrebari despre ce tabele, coloane, chei sau tipuri de informatii
  exista efectiv in baza.
  Acest intent nu necesita citirea randurilor din tabele;

- database_query:
  intrebare care necesita citirea efectiva a valorilor din baza de date configurata.
  Include numarari, agregari, valori, liste de inregistrari, filtre,
  sortari sau alte rezultate obtinute prin executarea unei interogari;

- report_request:
  cerere de creare a unui raport Power BI nou;

- report_follow_up:
  cerere de modificare, completare sau continuare a unui raport generat
  anterior in aceeasi conversatie;

- unclear:
  mesajul nu este suficient de clar pentru a determina intentia.

Exemple pentru general_question:
- "Ce este un slicer in Power BI?" -> general_question
- "Ce este un primary key?" -> general_question
- "Ce poti face?" -> general_question
- "Ai acces la baza de date?" -> general_question
- "Daca iti cer un raport despre studenti, cu ce date il vei crea?"
  -> general_question
- "Cum alegi datele necesare pentru un raport?" -> general_question

Exemple pentru project_question:
- "Ce pagini are raportul pe care l-ai generat?" -> project_question
- "Ce tabele ai folosit pentru acest raport?" -> project_question
- "Ce campuri foloseste graficul?" -> project_question
- "Din ce tabela SQL ai luat datele pentru raport?" -> project_question
- "Ce coloane are modelul semantic al raportului?" -> project_question

Exemple pentru database_question:
- "Ce tabele exista in baza de date?" -> database_question
- "Ce coloane are tabela X din baza de date?" -> database_question
- "Ce informatii despre studenti sunt disponibile in baza de date?"
  -> database_question
- "Exista foreign keys in baza de date?" -> database_question
- "Ce tabele contin informatii despre studenti?" -> database_question

Exemple pentru database_query:
- "Cati studenti exista?" -> database_query
- "Cate inregistrari sunt in tabela studentilor?" -> database_query
- "Arata primii 20 de studenti." -> database_query
- "Care este media valorii X?" -> database_query
- "Arata doar studentii activi." -> database_query
- "Cati studenti sunt pe fiecare gen?" -> database_query

Exemple pentru report_request:
- "Creeaza un raport cu numarul total de studenti." -> report_request
- "Fa-mi un raport cu numarul de studenti pe gen." -> report_request
- "Vreau un raport Power BI despre studenti." -> report_request

Exemple pentru report_follow_up:
- "Adauga si un grafic pe gen." -> report_follow_up
- "Mai pune un filtru pentru an." -> report_follow_up
- "Schimba graficul de bare intr-un pie chart." -> report_follow_up

Reguli de diferentiere:

- O intrebare despre CUM ar lucra aplicatia sau CE ar putea folosi in
  general este general_question.
- O intrebare care cere sa inspectezi efectiv ce exista in baza de date este
  database_question.

Exemplu important:
- "Daca iti cer un raport despre studenti, cu ce date il vei crea?"
  -> general_question
- "Ce date despre studenti sunt disponibile in baza de date?"
  -> database_question

- Daca utilizatorul cere informatii despre raportul deja generat in
  sesiunea curenta, foloseste project_question.

- Daca raspunsul necesita valori din randuri, COUNT, SUM, AVG, MIN, MAX,
  filtrare, sortare sau listarea unor inregistrari, foloseste
  database_query.

- Daca utilizatorul cere efectiv crearea unui raport nou, foloseste
  report_request chiar daca cererea mentioneaza date din baza de date configurata.

- Daca utilizatorul cere modificarea unui raport deja generat, foloseste
  report_follow_up.

- Nu clasifica o intrebare drept database_question doar pentru ca
  mentioneaza studenti, tabele sau date. Trebuie sa ceara efectiv
  informatii despre structura bazei de date configurate.

- Nu clasifica o intrebare drept database_query doar pentru ca mentioneaza
  o entitate din baza. Trebuie sa necesite citirea valorilor din randuri.

- Foloseste istoricul conversatiei pentru a interpreta follow-up-uri,
  referinte la raspunsurile anterioare si cereri incomplete care depind
  de context.

- Un project_question se refera exclusiv la un raport Power BI generat
  anterior in sesiune. O intrebare despre un raspuns anterior obtinut din
  baza de date nu este project_question doar pentru ca se refera la ceva
  spus anterior.

- Daca mesajul continua, corecteaza, reformuleaza sau restrange o intrebare
  anterioara despre valori din baza de date, pastreaza intentul
  database_query atunci cand raspunsul necesita in continuare citirea
  valorilor din baza.

- Pentru database_question si database_query completeaza resolved_message
  cu o formulare standalone a cererii utilizatorului.

- resolved_message trebuie sa poata fi inteles fara istoricul conversatiei.

- Daca mesajul curent este deja complet si standalone, copiaza sensul lui
  fara sa adaugi cerinte noi.

- Daca mesajul este un follow-up, foloseste istoricul doar pentru a recupera
  informatia necesara si pastreaza toate restrictiile relevante ale
  utilizatorului.

- Nu inventa filtre, valori, tabele, coloane sau criterii care nu apar in
  mesaj sau in istoricul conversatiei.

- Pentru intentii diferite de database_question si database_query,
  resolved_message trebuie sa fie null.

- Daca mesajul ramane ambiguu dupa folosirea istoricului, foloseste
  unclear.

Returneaza numai un obiect JSON valid, cu exact aceste campuri:

{
  "intent": "...",
  "summary": "...",
  "resolved_message": null,
  "requires_database_schema": true,
  "requires_report_generation": true,
  "confidence": 0.0
}

Reguli pentru campurile requires_*:

- general_question:
  requires_database_schema = false
  requires_report_generation = false

- project_question:
  requires_database_schema = false
  requires_report_generation = false

- database_question:
  requires_database_schema = true
  requires_report_generation = false

- database_query:
  requires_database_schema = true
  requires_report_generation = false

- report_request:
  requires_database_schema = true
  requires_report_generation = true

- report_follow_up:
  requires_database_schema = true
  requires_report_generation = true

- unclear:
  requires_database_schema = false
  requires_report_generation = false

Nu adauga explicatii in afara JSON-ului.
Nu inventa informatii care nu apar in mesaj sau in istoricul conversatiei.
"""


def _stabilize_intent(
    message: str,
    result: IntentResult,
) -> IntentResult:
    if result.intent != "report_request":
        return result

    normalized_message = message.casefold()

    report_markers = (
        "raport",
        "power bi",
        "dashboard",
        "grafic",
        "vizualizare",
        "vizual",
    )

    explicitly_requests_report = any(
        marker in normalized_message
        for marker in report_markers
    )

    if explicitly_requests_report:
        return result

    return result.model_copy(
        update={
            "intent": "database_query",
            "resolved_message": message,
            "requires_database_schema": True,
            "requires_report_generation": False,
        }
    )


class IntentClassifier:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = (
            llm
            or VLLMClient()
        )

    def classify(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> IntentResult:
        clean_message = message.strip()

        if not clean_message:
            raise ValueError(
                "The message cannot be empty."
            )

        recent_history = (
            history
            or []
        )

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": CLASSIFICATION_PROMPT,
            },
            *recent_history,
            {
                "role": "user",
                "content": clean_message,
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=384,
            temperature=0.0,
            enable_thinking=False,
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise RuntimeError(
                "The model returned no intent classification."
            )

        parsed_result = self._parse_json(
            content
        )

        result = IntentResult.model_validate(
            parsed_result
        )

        return _stabilize_intent(
            message=clean_message,
            result=result,
        )

    @staticmethod
    def _parse_json(
        content: str,
    ) -> dict[str, Any]:
        clean_content = (
            content.strip()
        )

        if clean_content.startswith(
            "```"
        ):
            lines = (
                clean_content
                .splitlines()
            )

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip()
                == "```"
            ):
                lines = lines[:-1]

            clean_content = (
                "\n"
                .join(lines)
                .strip()
            )

        return json.loads(
            clean_content
        )