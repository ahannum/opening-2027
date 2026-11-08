"""Copy the choreo notes from the PUBLIC Ground Truth decks into deck/notes.json for the phone player.

The "Choreo notes" GitHub workflow runs this every hour (deck edits don't trigger a push). To run it
by hand, from the repo root:

    python3 tools/sync_notes.py

It downloads each public deck as PowerPoint (which keeps tables as tables), and for every slide with
a measure table it saves the slide's section ("5 · Hearts adrift: Part 1" → section 5), the table's
columns (Counts, Choreo, F notes, L notes, …) and rows, and the slide's "Overall choreo notes". The
player matches a part to its section by the number before "·" and shows the rows for the frame's
measures. Only the public decks are read: the WIP decks need a Google sign-in.
"""
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

DECKS = [
    ("Polka", "1Ezgd0IjRn6hVH9Cl82wFNgZOM_e7ImAyuUzWlN7bXyU"),
    ("Waltz", "1Mi6bg3E81TKhUepr0r_7uvpa856pUo3dvHjQBszMLmY"),
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deck", "notes.json")
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
HEADER = re.compile(r"^(\d+)(?:\s*→\s*\d+)?\s*·\s*(.+)$")


def paragraph(p):
    parts = []
    for node in p.iter():
        if node.tag == A + "t":
            parts.append(node.text or "")
        elif node.tag == A + "br":
            parts.append("\n")
    return "".join(parts).replace("\u000b", "\n")


def text_of(element):
    lines = [paragraph(p) for p in element.iter(A + "p")]
    text = "\n".join(line.rstrip() for line in lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def slides(data):
    z = zipfile.ZipFile(BytesIO(data))
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    rels = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    target = {rel.get("Id"): rel.get("Target") for rel in rels}
    for slide_id in pres.find(P + "sldIdLst"):
        yield ET.fromstring(z.read("ppt/" + target[slide_id.get(R + "id")]))


def sections(dance, data):
    found = []
    for slide in slides(data):
        tables = list(slide.iter(A + "tbl"))
        if not tables:
            continue
        texts = [text_of(shape) for shape in slide.iter(P + "sp")]
        header = next((HEADER.match(t) for t in texts if HEADER.match(t)), None)
        if not header:
            continue
        overview = next((t for t in texts if t.lower().startswith("overall choreo notes")), "")
        overview = re.sub(r"^overall choreo notes:?\s*", "", overview, flags=re.I).strip()
        for table in tables:
            rows = [[text_of(cell) for cell in row.findall(A + "tc")] for row in table.findall(A + "tr")]
            if len(rows) < 2:
                continue
            columns, body = rows[0], rows[1:]
            body = [row for row in body if any(cell for cell in row)]
            found.append({
                "dance": dance,
                "number": int(header.group(1)),
                "title": f"{header.group(1)} · {header.group(2).strip()}",
                "overview": overview,
                "columns": [c or f"Column {i + 1}" for i, c in enumerate(columns)],
                "rows": body,
            })
    return found


def main():
    result = {"source": {}, "sections": []}
    for dance, deck_id in DECKS:
        url = f"https://docs.google.com/presentation/d/{deck_id}/export/pptx"
        result["source"][dance] = f"https://docs.google.com/presentation/d/{deck_id}/edit"
        with urllib.request.urlopen(url, timeout=120) as response:
            result["sections"].extend(sections(dance, response.read()))
    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if text == old:
        print("Choreo notes already up to date.")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(text)
    counts = {}
    for section in result["sections"]:
        counts[section["dance"]] = counts.get(section["dance"], 0) + 1
    print("Saved deck/notes.json:", ", ".join(f"{n} {dance} tables" for dance, n in counts.items()))


if __name__ == "__main__":
    sys.exit(main())
