"""
Chatbot over de aftrek van innovatie-inkomsten (België).
Laadt documenten uit de docs/ map en beantwoordt vragen op basis daarvan.
"""

import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Probeer pypdf te importeren voor PDF-ondersteuning
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

load_dotenv()


SYSTEM_PROMPT_BASE = """Je bent een fiscaal expert gespecialiseerd in de Belgische **aftrek van innovatie-inkomsten** (ook bekend als de Innovation Income Deduction of IID).

Je taak is om vragen te beantwoorden op basis van de documenten die hieronder zijn opgenomen. Gebruik uitsluitend de inhoud van die documenten als bron. Als een vraag niet beantwoord kan worden op basis van de documenten, zeg dat dan duidelijk.

Richtlijnen:
- Geef duidelijke, accurate antwoorden in het Nederlands (of de taal van de vraag).
- Verwijs waar relevant naar specifieke artikelen, percentages of voorwaarden uit de documenten.
- Wees voorzichtig met fiscale adviezen: geef aan wanneer raadpleging van een belastingadviseur aanbevolen is.
- Structureer je antwoorden overzichtelijk met opsommingen of kopjes waar nuttig.

{document_section}"""


def load_documents(docs_dir: Path) -> str:
    """Laad alle documenten uit de docs/ map en geef de gecombineerde tekst terug."""
    if not docs_dir.exists():
        return ""

    texts = []
    supported = [".txt", ".md"]
    if PDF_SUPPORT:
        supported.append(".pdf")

    files = sorted(docs_dir.iterdir())
    loaded = 0

    for filepath in files:
        if filepath.suffix.lower() not in supported:
            continue
        if filepath.name.startswith("."):
            continue

        try:
            if filepath.suffix.lower() == ".pdf":
                reader = PdfReader(str(filepath))
                pages = [page.extract_text() or "" for page in reader.pages]
                content = "\n".join(pages).strip()
            else:
                content = filepath.read_text(encoding="utf-8").strip()

            if content:
                texts.append(f"### Document: {filepath.name}\n\n{content}")
                loaded += 1
                print(f"  [OK] {filepath.name}")
        except Exception as e:
            print(f"  [FOUT] {filepath.name}: {e}")

    if loaded == 0:
        return ""

    return "\n\n---\n\n".join(texts)


def build_system_prompt(docs_text: str) -> str:
    """Bouw de system prompt op, inclusief de documenten."""
    if docs_text:
        doc_section = (
            "## Beschikbare documenten\n\n"
            "De volgende documenten vormen je kennisbasis:\n\n"
            f"{docs_text}"
        )
    else:
        doc_section = (
            "## Let op: geen documenten geladen\n\n"
            "Er zijn momenteel geen documenten beschikbaar in de docs/ map. "
            "Beantwoord vragen op basis van je algemene kennis over de Belgische "
            "aftrek van innovatie-inkomsten, maar vermeld dat je geen specifieke "
            "documentatie hebt geladen."
        )
    return SYSTEM_PROMPT_BASE.format(document_section=doc_section)


def chat():
    """Start de interactieve chatbot."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Fout: ANTHROPIC_API_KEY is niet ingesteld.\n"
            "Maak een .env bestand aan met: ANTHROPIC_API_KEY=your-key-here"
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    docs_dir = Path(__file__).parent / "docs"

    print("=" * 60)
    print("  Chatbot: Aftrek van Innovatie-Inkomsten (België)")
    print("=" * 60)
    print(f"\nDocumenten laden uit: {docs_dir}")

    if not PDF_SUPPORT:
        print("  [INFO] PDF-ondersteuning niet beschikbaar. Installeer pypdf.")

    docs_text = load_documents(docs_dir)

    if not docs_text:
        print("  [WAARSCHUWING] Geen documenten gevonden in docs/")
        print("  Voeg .txt, .md of .pdf bestanden toe aan de docs/ map.\n")
    else:
        print()

    system_prompt = build_system_prompt(docs_text)
    conversation_history = []

    print("Typ je vraag over de innovatie-aftrek. Typ 'stop' of 'exit' om te beëindigen.\n")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nJij: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nChatbot beëindigd.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("stop", "exit", "quit", "q"):
            print("Chatbot beëindigd. Tot ziens!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        try:
            # Gebruik prompt caching voor de stabiele system prompt met documenten
            system_blocks = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=system_blocks,
                messages=conversation_history,
                thinking={"type": "adaptive"},
            )

            # Haal de tekstrespons op
            assistant_text = ""
            for block in response.content:
                if block.type == "text":
                    assistant_text = block.text
                    break

            conversation_history.append(
                {"role": "assistant", "content": assistant_text}
            )

            print(f"\nChatbot: {assistant_text}")

        except anthropic.AuthenticationError:
            print("\nFout: Ongeldige API-sleutel. Controleer je ANTHROPIC_API_KEY.")
            break
        except anthropic.RateLimitError:
            print("\nFout: Te veel verzoeken. Wacht even en probeer opnieuw.")
        except anthropic.APIError as e:
            print(f"\nAPI-fout: {e}")


if __name__ == "__main__":
    chat()
