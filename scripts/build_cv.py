#!/usr/bin/env python3
"""Build the downloadable English CV directly from cv/index.html.

Run: python3 -m pip install -r scripts/requirements-cv.txt
     python3 scripts/build_cv.py
The English page is the content source; update its Chinese translation alongside it.
"""

from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
import re
import os

from lxml import html
import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = html.fromstring((ROOT / "cv/index.html").read_bytes())
FONT_DIR = Path(reportlab.__file__).parent / "fonts"
for name, filename in [
    ("CV", "Vera.ttf"), ("CV-Bold", "VeraBd.ttf"),
    ("CV-Italic", "VeraIt.ttf"), ("CV-BoldItalic", "VeraBI.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily(
    "CV", normal="CV", bold="CV-Bold", italic="CV-Italic", boldItalic="CV-BoldItalic"
)
pdfmetrics.registerFont(TTFont("CVSymbols", str(ROOT / "scripts/fonts/CVSymbols.ttf")))


def normalized(value):
    return re.sub(r"\s+", " ", value).strip().translate(str.maketrans({
        "–": "-", "—": "-", "−": "-", "‑": "-", "’": "'", "“": '"', "”": '"',
    }))


def text(node):
    return normalized("".join(node.itertext()))


def inline(node):
    """Preserve emphasis, links, and mathematical sub/superscripts."""
    out = escape(node.text or "")
    for child in node:
        content = inline(child)
        tag = {"strong": "b", "em": "i"}.get(child.tag, child.tag)
        if tag in ("b", "i", "sub", "sup"):
            out += f"<{tag}>{content}</{tag}>"
        elif tag == "a" and child.get("href", "").startswith(("https://", "mailto:")):
            out += f'<a href="{escape(child.get("href"), quote=True)}">{content}</a>'
        else:
            out += content
        out += escape(child.tail or "")
    return normalized(out)


def with_class(node, cls, tag="*"):
    return node.xpath(f'.//{tag}[contains(concat(" ", normalize-space(@class), " "), " {cls} ")]')


INK = colors.HexColor("#161616")
GRAY = colors.HexColor("#545454")
BASE = ParagraphStyle("body", fontName="CV", fontSize=9.3, leading=12.7,
                      textColor=INK, spaceAfter=3)
STYLES = {
    "body": BASE,
    "name": ParagraphStyle("name", parent=BASE, fontName="CV-Bold", fontSize=23,
                           leading=28, alignment=TA_CENTER, spaceAfter=4),
    "contact": ParagraphStyle("contact", parent=BASE, fontSize=8.6, leading=12,
                              alignment=TA_CENTER, spaceAfter=2),
    "section": ParagraphStyle("section", parent=BASE, fontName="CV-Bold", fontSize=11,
                              leading=15, spaceBefore=12, spaceAfter=6, keepWithNext=True),
    "title": ParagraphStyle("title", parent=BASE, fontName="CV-Bold", fontSize=9.5,
                            leading=13, spaceAfter=2, keepWithNext=True),
    "meta": ParagraphStyle("meta", parent=BASE, fontSize=8.8, leading=12, textColor=GRAY,
                           spaceAfter=3, keepWithNext=True),
    "small": ParagraphStyle("small", parent=BASE, fontSize=8.8, leading=12),
    "date": ParagraphStyle("date", parent=BASE, fontSize=8.8, leading=12,
                           alignment=TA_RIGHT, textColor=GRAY),
    "bullet": ParagraphStyle("bullet", parent=BASE, leftIndent=10, firstLineIndent=0,
                             bulletIndent=0, spaceAfter=3),
}
WIDTH = letter[0] - 90 - 12  # Account for the document frame's internal padding.
story = []


def p(value, kind="body"):
    value = value.replace("γ", '<font name="CVSymbols">γ</font>')
    return Paragraph(value, STYLES[kind], bulletText="•" if kind == "bullet" else None)


def heading(section):
    story.append(p(escape(text(section.find("h2"))), "section"))


def head(node):
    row = with_class(node, "cv-item-head")[0]
    left = row.find("div")
    title = inline(left.find("h3"))
    subtitle = inline(left.find("p"))
    when = inline(row.find("p"))
    story.append(p(title, "title"))
    table = Table([[p(subtitle, "meta"), p(when, "date")]], colWidths=[WIDTH-143, 143])
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    table.keepWithNext = True
    story.append(table)


def bullets(node):
    for li in node.xpath("./ul/li"):
        story.append(p(inline(li), "bullet"))


stamp = DOC.xpath('//time[@datetime]')[0]
UPDATED = date.fromisoformat(stamp.get("datetime"))
os.environ["SOURCE_DATE_EPOCH"] = str(int(datetime(
    UPDATED.year, UPDATED.month, UPDATED.day, tzinfo=timezone.utc
).timestamp()))
DATE_LABEL = f"{UPDATED.strftime('%B')} {UPDATED.day}, {UPDATED.year}"
name = text(with_class(DOC, "eyebrow")[0])
story.append(p(escape(name), "name"))
contact = with_class(DOC, "cv-contact")[0]
contacts = []
for a in contact.findall("a"):
    label = text(a) if a.get("href").startswith("mailto:") else a.get("href").removeprefix("https://www.")
    contacts.append(f'<a href="{escape(a.get("href"), quote=True)}">{escape(label)}</a>')
story.append(p(" &nbsp;|&nbsp; ".join(contacts), "contact"))
domain = (ROOT / "CNAME").read_text().strip()
story.append(p(f'<a href="https://{escape(domain)}">{escape(domain)}</a> &nbsp;|&nbsp; Updated {DATE_LABEL}', "contact"))

sections = {s.get("id"): s for s in with_class(DOC, "cv-section", "section")}
section = sections["education"]
heading(section)
head(section)
story.append(p(inline(with_class(section, "cv-gpa")[0])))

section = sections["research-experience"]
heading(section)
for entry in with_class(section, "cv-entry"):
    head(entry)
    for child in entry:
        if child.tag == "p":
            story.append(p(inline(child), "small"))
        elif child.tag == "ul":
            for li in child:
                story.append(p(inline(li), "bullet"))
    story.append(Spacer(1, 4))

section = sections["manuscripts"]
heading(section)
for entry in with_class(section, "manuscript-entry"):
    group = [p(inline(entry.find("h3")), "title")]
    group.extend(p(inline(child), "small") for child in entry.findall("p"))
    group.append(Spacer(1, 4))
    story.append(KeepTogether(group))

story.append(PageBreak())
section = sections["directed-studies"]
heading(section)
story.append(p(inline(with_class(section, "cv-section-intro")[0]), "small"))
for entry in with_class(section, "cv-study-card"):
    title = inline(entry.find("h3"))
    mentor = inline(with_class(entry, "cv-label")[0])
    group = [p(f"{title} <font name='CV'>| {mentor}</font>", "title")]
    group.extend(p(inline(child), "small") for child in entry.findall("p") if "cv-label" not in child.get("class", ""))
    group.append(Spacer(1, 2))
    story.append(KeepTogether(group))

section = sections["coursework"]
heading(section)
for block in with_class(section, "coursework-block") + with_class(section, "completed-coursework"):
    story.append(p(inline(with_class(block, "cv-label")[0]), "title"))
    courses = [inline(li) for li in block.xpath("./ul/li")]
    story.append(p("; ".join(courses) + ".", "small"))

section = sections["honors"]
heading(section)
honor_rows = []
for row in with_class(section, "cv-honor-list")[0].findall("div"):
    honor_rows.append([p(inline(row.find("strong")), "small"), p(inline(row.find("span")), "date")])
honors = Table(honor_rows, colWidths=[WIDTH-150, 150])
honors.setStyle(TableStyle([
    ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ("TOPPADDING", (0,0), (-1,-1), 0), ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
]))
story.append(honors)

section = sections["athletics"]
heading(section)
head(section)
story.append(p(" ".join(inline(li) for li in section.xpath("./ul/li")), "small"))

section = sections["technical-skills"]
heading(section)
for row in section.xpath("./dl/div"):
    story.append(p(f'<b>{inline(row.find("dt"))}:</b> {inline(row.find("dd"))}', "small"))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("CV", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(45, 26, f"{name} | Curriculum Vitae | {DATE_LABEL}")
    canvas.drawRightString(letter[0]-45, 26, str(doc.page))
    canvas.restoreState()


output = ROOT / "cv.pdf"
pdf = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=45, leftMargin=45,
                        topMargin=33, bottomMargin=43, title=f"{name} - Curriculum Vitae",
                        author=name, subject=f"Academic CV updated {DATE_LABEL}",
                        creator="scripts/build_cv.py (source: cv/index.html)", invariant=1)
pdf.build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
