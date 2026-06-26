"""Journal export — CSV and PDF generation."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from tradeflow.features.journal.schemas import JournalEntryResponse


def export_entries_csv(entries: list[JournalEntryResponse]) -> bytes:
    """Generate CSV bytes for journal entries."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date",
            "title",
            "symbol",
            "side",
            "quantity",
            "entry_price",
            "exit_price",
            "pnl",
            "grade",
            "strategy",
            "emotions",
            "mistakes",
            "tags",
            "lessons_learned",
            "source",
        ],
    )
    for entry in entries:
        writer.writerow(
            [
                entry.session_date.isoformat(),
                entry.title,
                entry.symbol or "",
                entry.side.value if entry.side else "",
                entry.quantity or "",
                entry.entry_price or "",
                entry.exit_price or "",
                entry.pnl or "",
                entry.grade or "",
                entry.strategy.name if entry.strategy else "",
                ";".join(entry.emotions or []),
                ";".join(entry.mistakes or []),
                ";".join(entry.tags or []),
                (entry.lessons_learned or "").replace("\n", " "),
                entry.source.value,
            ],
        )
    return buffer.getvalue().encode("utf-8")


def export_entries_pdf(
    entries: list[JournalEntryResponse],
    *,
    title: str = "TradeFlow Journal",
) -> bytes:
    """Generate a simple PDF report for journal entries."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=title)
    styles = getSampleStyleSheet()
    story: list[object] = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    if not entries:
        story.append(Paragraph("No journal entries.", styles["Normal"]))
    else:
        total_pnl = sum((e.pnl or Decimal("0")) for e in entries)
        story.append(
            Paragraph(
                f"Entries: {len(entries)} · Total P&L: ${total_pnl:,.2f}",
                styles["Normal"],
            ),
        )
        story.append(Spacer(1, 12))
        table_data = [["Date", "Symbol", "Title", "P&L", "Grade", "Strategy"]]
        for entry in entries:
            table_data.append(
                [
                    entry.session_date.isoformat(),
                    entry.symbol or "—",
                    entry.title[:40],
                    f"${entry.pnl:,.2f}" if entry.pnl is not None else "—",
                    str(entry.grade) if entry.grade else "—",
                    (entry.strategy.name if entry.strategy else "—")[:20],
                ],
            )
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                ],
            ),
        )
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
