from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent
SOURCE_MD = ROOT / "sprint4-agentes-e-registro.md"
OUTPUT_PDF = ROOT / "sprint4-agentes-e-registro.pdf"


def markdown_to_story(markdown_text: str):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=6,
    )
    h3_style = ParagraphStyle(
        "DocH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=6,
        spaceAfter=4,
    )
    p_style = ParagraphStyle(
        "DocP",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=p_style,
        leftIndent=16,
        bulletIndent=6,
        spaceAfter=4,
    )

    story = []
    lines = markdown_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("# "):
            story.append(Paragraph(stripped[2:].strip(), title_style))
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(stripped[3:].strip(), h2_style))
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(stripped[4:].strip(), h3_style))
            continue
        if stripped.startswith("- "):
            story.append(Paragraph(stripped[2:].strip(), bullet_style, bulletText="•"))
            continue

        # Escapa caracteres básicos de XML usados pelo reportlab Paragraph.
        cleaned = (
            stripped.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        story.append(Paragraph(cleaned, p_style))

    return story


def main():
    markdown = SOURCE_MD.read_text(encoding="utf-8")
    story = markdown_to_story(markdown)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
        title="Sprint 4 - Orquestracao de Agentes Inteligentes",
        author="Grupo YOUVISA",
    )
    doc.build(story)
    print(f"PDF generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
