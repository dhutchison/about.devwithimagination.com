#!/usr/bin/env python3
"""Generate the CV PDF directly from the structured resume data."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Iterable, List

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data" / "resume"
DEFAULT_OUTPUT = ROOT / "assets" / "pdf" / "DavidHutchison.pdf"

INK = colors.HexColor("#24313d")
MUTED = colors.HexColor("#5f6b75")
ACCENT = colors.HexColor("#0f7d93")
RULE = colors.HexColor("#d8e1e8")
ACCENT_SOFT = colors.HexColor("#e7f4f6")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def markdown_inline(text: str) -> str:
    escaped = html.escape(text.strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def markdown_blocks(text: str, styles) -> List:
    flowables: List = []
    paragraph_lines: List[str] = []
    bullet_lines: List[str] = []

    def flush_paragraph():
        if paragraph_lines:
            flowables.append(Paragraph(markdown_inline(" ".join(paragraph_lines)), styles["Body"]))
            flowables.append(Spacer(1, 2.2 * mm))
            paragraph_lines.clear()

    def flush_bullets():
        if bullet_lines:
            items = [
                ListItem(Paragraph(markdown_inline(line), styles["CvBullet"]), leftIndent=0)
                for line in bullet_lines
            ]
            flowables.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=5 * mm,
                    bulletFontSize=5,
                    bulletColor=ACCENT,
                )
            )
            flowables.append(Spacer(1, 2.4 * mm))
            bullet_lines.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_bullets()
            continue
        if line.startswith("* "):
            flush_paragraph()
            bullet_lines.append(line[2:])
        else:
            flush_bullets()
            paragraph_lines.append(line)

    flush_paragraph()
    flush_bullets()
    return flowables


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "Name",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=25,
            textColor=INK,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Kicker",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=ACCENT,
            uppercase=True,
            spaceAfter=1 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Role",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            "Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            alignment=TA_RIGHT,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=ACCENT,
            spaceBefore=5 * mm,
            spaceAfter=1.8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.9,
            leading=12,
            textColor=INK,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            "CvBullet",
            parent=styles["Body"],
            leftIndent=0,
            firstLineIndent=0,
        )
    )
    styles.add(
        ParagraphStyle(
            "Company",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=12,
            textColor=INK,
            spaceBefore=2 * mm,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10,
            textColor=MUTED,
            spaceAfter=1 * mm,
        )
    )
    return styles


def section_title(title: str, styles) -> List:
    return [
        Paragraph(title.upper(), styles["Section"]),
        HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=2 * mm),
    ]


def append_section(story: List, title: str, content: List, styles):
    if not content:
        return

    story.append(KeepTogether(section_title(title, styles) + [content[0]]))
    story.extend(content[1:])


def contact_lines(info: dict) -> str:
    values = [info.get("email"), info.get("website_display"), info.get("phone")]
    return "<br/>".join(html.escape(value) for value in values if value)


def role_line(role: dict) -> str:
    title = markdown_inline(role.get("title", ""))
    when = html.escape(role.get("when", ""))
    return f"<b>{title}</b> <font color='#5f6b75'>{when}</font>"


def role_group(item: dict, styles) -> List:
    intro = [
        Paragraph(html.escape(item["where"]), styles["Company"]),
        Paragraph("<br/>".join(role_line(role) for role in item.get("roles", [])), styles["Meta"]),
    ]
    body = markdown_blocks(item["text"], styles)

    if not body:
        return [KeepTogether(intro)]

    return [KeepTogether(intro + [body[0]])] + body[1:]


def build_story(info: dict, experience: Iterable[dict], skills: dict, education: Iterable[dict], styles) -> List:
    story: List = []

    story.append(Paragraph("CURRICULUM VITAE", styles["Kicker"]))
    story.append(Paragraph(html.escape(info["name"]), styles["Name"]))
    story.append(Paragraph(html.escape(info["position"]), styles["Role"]))
    if contact_lines(info):
        story.append(Paragraph(contact_lines(info), styles["Contact"]))
    story.append(HRFlowable(width="100%", thickness=1.4, color=ACCENT, spaceBefore=4 * mm, spaceAfter=4 * mm))

    append_section(story, "Profile", markdown_blocks(info["text"], styles), styles)

    experience_content: List = []
    for item in experience:
        experience_content.extend(role_group(item, styles))
    append_section(story, "Experience", experience_content, styles)

    append_section(story, "Technical Skills", markdown_blocks(skills["text"], styles), styles)

    education_content: List = []
    for item in education:
        when = item.get("when") or f"{item.get('when_from', '')}-{item.get('when_to', '')}"
        qualification = markdown_inline(item["qualification"])
        location = html.escape(item["location"])
        education_content.append(KeepTogether([
            Paragraph(f"<b>{qualification}</b> <font color='#5f6b75'>{html.escape(when)}</font>", styles["Body"]),
            Paragraph(location, styles["Meta"]),
        ]))
    append_section(story, "Education & Certification", education_content, styles)

    return story


def draw_page_frame(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(ACCENT_SOFT)
    canvas.rect(0, 0, 5 * mm, A4[1], stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 44 * mm, 5 * mm, 44 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, 10 * mm, A4[0] - doc.rightMargin, 10 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(A4[0] - doc.rightMargin, 6.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def generate(output: Path):
    info = load_yaml(DATA / "info.yaml")
    experience = load_yaml(DATA / "experience.yaml")
    skills = load_yaml(DATA / "skills.yaml")
    education = load_json(DATA / "education.json")

    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"{info['name']} CV",
        author=info["name"],
    )
    styles = build_styles()
    story = build_story(info, experience, skills, education, styles)
    doc.build(story, onFirstPage=draw_page_frame, onLaterPages=draw_page_frame)


def main():
    parser = argparse.ArgumentParser(description="Generate the resume PDF from _data/resume.")
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate(args.output)
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
