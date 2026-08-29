import csv
import io
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import Lead, Thesis
from .schemas import ImportResult, LeadRead, Metrics, StatusUpdate, ThesisBase, ThesisRead
from .scoring import apply_score
from .seed import row_to_lead, seed_database, validate_import_row


SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_csv_cell(value: object) -> object:
    """Prevent imported text from becoming a spreadsheet formula on export."""
    if isinstance(value, str) and value.lstrip(" \t\r").startswith(SPREADSHEET_FORMULA_PREFIXES):
        return "'" + value
    return value


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Explainable acquisition-fit scoring for sourced business leads.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/health")
def health():
    return {"status": "healthy", "ai_required": False}


@app.get("/api/thesis", response_model=ThesisRead)
def get_thesis(db: Session = Depends(get_db)):
    thesis = db.scalar(select(Thesis).limit(1))
    if not thesis:
        raise HTTPException(404, "Acquisition thesis not found")
    return thesis


@app.put("/api/thesis", response_model=ThesisRead)
def update_thesis(payload: ThesisBase, db: Session = Depends(get_db)):
    if payload.employee_min > payload.employee_max:
        raise HTTPException(422, "Minimum employees cannot exceed maximum employees")
    thesis = db.scalar(select(Thesis).limit(1))
    if not thesis:
        thesis = Thesis()
        db.add(thesis)
    for key, value in payload.model_dump().items():
        setattr(thesis, key, value)
    db.flush()
    for lead in db.scalars(select(Lead)).all():
        apply_score(lead, thesis)
    db.commit()
    db.refresh(thesis)
    return thesis


@app.get("/api/leads", response_model=list[LeadRead])
def list_leads(
    search: str | None = Query(None, max_length=200),
    status: Literal["all", "shortlisted", "review", "rejected"] | None = None,
    priority: Literal["all", "high", "medium", "low"] | None = None,
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|company)$"),
    db: Session = Depends(get_db),
):
    query = select(Lead)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Lead.company_name.ilike(pattern), Lead.industry.ilike(pattern), Lead.location.ilike(pattern)))
    if status and status != "all":
        query = query.where(Lead.status == status)
    if priority and priority != "all":
        query = query.where(Lead.priority == priority)
    if sort == "score_asc":
        query = query.order_by(Lead.score.asc(), Lead.company_name.asc())
    elif sort == "company":
        query = query.order_by(Lead.company_name.asc())
    else:
        query = query.order_by(Lead.score.desc(), Lead.company_name.asc())
    return db.scalars(query).all()


@app.get("/api/leads/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@app.patch("/api/leads/{lead_id}/status", response_model=LeadRead)
def update_status(lead_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/metrics", response_model=Metrics)
def metrics(db: Session = Depends(get_db)):
    leads = db.scalars(select(Lead)).all()
    total = len(leads)
    complete_cells = sum(
        sum(value not in (None, "") for value in (
            lead.domain, lead.industry, lead.location, lead.employee_count,
            lead.year_founded, lead.description,
        ))
        for lead in leads
    )
    return Metrics(
        total=total,
        high_priority=sum(lead.priority == "high" for lead in leads),
        shortlisted=sum(lead.status == "shortlisted" for lead in leads),
        needs_review=sum(bool(lead.missing_data or lead.red_flags) and lead.status != "rejected" for lead in leads),
        average_score=round(sum(lead.score for lead in leads) / total, 1) if total else 0,
        data_completeness=round(complete_cells / (total * 6) * 100, 1) if total else 0,
    )


@app.post("/api/leads/import", response_model=ImportResult)
async def import_leads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(413, "CSV must be smaller than 5 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must use UTF-8 encoding") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "company_name" not in reader.fieldnames:
        raise HTTPException(422, "CSV must include a company_name column")

    thesis = db.scalar(select(Thesis).limit(1))
    imported = duplicates = invalid = 0
    errors: list[str] = []
    seen_domains = set(db.scalars(select(Lead.domain).where(Lead.domain.is_not(None))).all())
    seen_names = {(name.lower(), (location or "").lower()) for name, location in db.execute(select(Lead.company_name, Lead.location)).all()}

    for line_number, row in enumerate(reader, start=2):
        if not (row.get("company_name") or "").strip():
            invalid += 1
            if len(errors) < 5:
                errors.append(f"Row {line_number}: company_name is required")
            continue
        row_errors = validate_import_row(row)
        if row_errors:
            invalid += 1
            if len(errors) < 5:
                errors.append(f"Row {line_number}: {'; '.join(row_errors)}")
            continue
        lead = row_to_lead(row)
        key = (lead.company_name.lower(), (lead.location or "").lower())
        if (lead.domain and lead.domain in seen_domains) or key in seen_names:
            duplicates += 1
            continue
        apply_score(lead, thesis)
        db.add(lead)
        if lead.domain:
            seen_domains.add(lead.domain)
        seen_names.add(key)
        imported += 1
    db.commit()
    return ImportResult(imported=imported, duplicates_skipped=duplicates, invalid_rows=invalid, errors=errors)


@app.get("/api/leads-export.csv")
def export_leads(
    status: Literal["all", "shortlisted", "review", "rejected"] = "shortlisted",
    db: Session = Depends(get_db),
):
    query = select(Lead).order_by(Lead.score.desc())
    if status != "all":
        query = query.where(Lead.status == status)
    leads = db.scalars(query).all()
    output = io.StringIO()
    fieldnames = [
        "company_name", "website", "industry", "location", "employee_count", "year_founded",
        "owner_name", "email", "phone", "source", "score", "priority", "status", "score_reasons",
        "red_flags", "acquisition_rationale", "outreach_angle",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for lead in leads:
        writer.writerow({key: safe_csv_cell(value) for key, value in {
            "company_name": lead.company_name,
            "website": lead.website or "",
            "industry": lead.industry or "",
            "location": lead.location or "",
            "employee_count": lead.employee_count or "",
            "year_founded": lead.year_founded or "",
            "owner_name": lead.owner_name or "",
            "email": lead.email or "",
            "phone": lead.phone or "",
            "source": lead.source,
            "score": lead.score,
            "priority": lead.priority,
            "status": lead.status,
            "score_reasons": " | ".join(lead.score_reasons or []),
            "red_flags": " | ".join(lead.red_flags or []),
            "acquisition_rationale": lead.acquisition_rationale,
            "outreach_angle": lead.outreach_angle,
        }.items()})
    filename = f"{status}-leads.csv" if status != "all" else "all-leads.csv"
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
