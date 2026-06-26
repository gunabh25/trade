"""Analytics export — CSV and PDF generation."""

from __future__ import annotations

import csv
import io

from tradeflow.features.analytics.schemas import AnalyticsOverviewResponse


def export_overview_csv(overview: AnalyticsOverviewResponse) -> bytes:
    """Generate CSV bytes for analytics overview."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    m = overview.metrics
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Trades", m.total_trades])
    writer.writerow(["Total P&L", m.total_pnl])
    writer.writerow(["Win Rate", f"{m.win_rate:.2f}%"])
    writer.writerow(["Loss Rate", f"{m.loss_rate:.2f}%"])
    writer.writerow(["Avg Win", m.avg_win])
    writer.writerow(["Avg Loss", m.avg_loss])
    writer.writerow(["Profit Factor", m.profit_factor or ""])
    writer.writerow(["Expectancy", m.expectancy])
    writer.writerow(["Sharpe Ratio", m.sharpe_ratio or ""])
    writer.writerow(["Sortino Ratio", m.sortino_ratio or ""])
    writer.writerow(["Max Drawdown %", f"{m.max_drawdown_pct:.2f}"])
    writer.writerow(["Recovery Factor", m.recovery_factor or ""])
    writer.writerow(["Max Consecutive Wins", m.max_consecutive_wins])
    writer.writerow(["Max Consecutive Losses", m.max_consecutive_losses])
    writer.writerow(["Starting Equity", m.starting_equity])
    writer.writerow(["Ending Equity", m.ending_equity])
    writer.writerow([])
    writer.writerow(["Date", "Equity"])
    for point in overview.equity_curve:
        writer.writerow([point.date.isoformat(), point.equity])
    return buffer.getvalue().encode("utf-8")


def export_overview_pdf(
    overview: AnalyticsOverviewResponse,
    *,
    title: str = "TradeFlow Analytics Report",
) -> bytes:
    """Generate a PDF analytics report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=title)
    styles = getSampleStyleSheet()
    story: list[object] = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    m = overview.metrics
    summary = [
        ["Metric", "Value"],
        ["Total Trades", str(m.total_trades)],
        ["Total P&L", f"${m.total_pnl:,.2f}"],
        ["Win Rate", f"{m.win_rate:.1f}%"],
        ["Loss Rate", f"{m.loss_rate:.1f}%"],
        ["Avg Win", f"${m.avg_win:,.2f}"],
        ["Avg Loss", f"${m.avg_loss:,.2f}"],
        ["Profit Factor", f"{m.profit_factor:.2f}" if m.profit_factor else "—"],
        ["Sharpe", f"{m.sharpe_ratio:.2f}" if m.sharpe_ratio else "—"],
        ["Sortino", f"{m.sortino_ratio:.2f}" if m.sortino_ratio else "—"],
        ["Max Drawdown", f"{m.max_drawdown_pct:.1f}%"],
        ["Recovery Factor", f"{m.recovery_factor:.2f}" if m.recovery_factor else "—"],
    ]
    table = Table(summary, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ],
        ),
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
