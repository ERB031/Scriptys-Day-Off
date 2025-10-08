from __future__ import annotations

import csv
from io import StringIO
from typing import List

from fpdf import FPDF

from ..schemas.schedule import DayPlan


class DayPlanExporter:
    def __init__(self, plans: List[DayPlan]) -> None:
        self.plans = plans

    def to_csv(self) -> str:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["Day", "Locations", "Cast", "Pages", "Minutes", "Cost"]
        )
        for plan in self.plans:
            writer.writerow(
                [
                    plan.name,
                    "; ".join(plan.location_summary),
                    "; ".join(plan.cast_summary),
                    f"{plan.total_pages_decimal:.2f}",
                    f"{plan.total_minutes:.0f}",
                    f"{plan.total_cost:.2f}",
                ]
            )
            for scene in plan.scenes:
                writer.writerow(
                    [
                        f"  Scene {scene.sequence_index + 1}",
                        scene.location,
                        ", ".join(scene.cast),
                        f"{scene.page_decimal:.2f}",
                        f"{scene.estimated_minutes:.0f}",
                        f"{scene.estimated_cost:.2f}",
                    ]
                )
        return buffer.getvalue()

    def to_pdf(self) -> bytes:
        pdf = FPDF(unit="pt", format="A4")
        pdf.set_auto_page_break(auto=True, margin=40)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 24, "Scripty's Day Off – Day Budget", ln=True)

        for plan in self.plans:
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 18, plan.name, ln=True)
            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 16, f"Locations: {', '.join(plan.location_summary) or '—'}", ln=True)
            pdf.cell(0, 16, f"Cast: {', '.join(plan.cast_summary) or '—'}", ln=True)
            pdf.cell(
                0,
                16,
                f"Totals • Pages: {plan.total_pages_decimal:.2f} • Minutes: {plan.total_minutes:.0f} • Cost: ${plan.total_cost:.2f}",
                ln=True,
            )
            pdf.ln(4)
            for scene in plan.scenes:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(
                    0,
                    14,
                    f"Scene {scene.sequence_index + 1} · {scene.slugline} ({scene.page_decimal:.2f} pages)",
                    ln=True,
                )
                pdf.set_font("Helvetica", size=10)
                pdf.multi_cell(
                    0,
                    12,
                    f"Cast: {', '.join(scene.cast) or '—'} | Location: {scene.location} | Cost: ${scene.estimated_cost:.2f}",
                )
            pdf.ln(6)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        return pdf_bytes
