"""Reports API — compliance report generation endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.enforcement import require_plan
from app.db.session import get_db
from app.dependencies import get_current_user
from app.reports.generator import generate_report_data, render_csv, render_excel, render_pdf

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/generate", dependencies=[Depends(require_plan("business"))])
async def generate_report(
    format: str = Query("json", enum=["json", "csv", "pdf", "excel"]),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate a compliance report for the specified period.

    Formats:
      - json: Structured JSON data
      - csv: Tabular CSV file
      - pdf: Professional PDF document with tables
      - excel: Multi-sheet Excel workbook (OWASP, SOC2, GDPR, Japan)
    """
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=days)

    report_data = await generate_report_data(
        db=db,
        tenant_id=user.tenant_id,
        date_from=date_from,
        date_to=date_to,
    )

    if format == "csv":
        csv_content = render_csv(report_data)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.csv"
            },
        )

    if format == "pdf":
        pdf_bytes = render_pdf(report_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.pdf"
            },
        )

    if format == "excel":
        excel_bytes = render_excel(report_data)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.xlsx"
            },
        )

    return JSONResponse(content=report_data)
