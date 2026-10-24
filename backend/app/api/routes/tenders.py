"""Tenders, conditions, evaluations, and amendment routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.clock import system_clock
from app.core.errors import AppError, NotFoundError, PayloadTooLargeError
from app.database import get_db
from app.documents.extract_pages import extract_pages_from_pdf
from app.documents.hashing import compute_sha256
from app.domain.readiness import evaluate_tender
from app.integrations.storage import get_storage
from app.models.models import (
    Document,
    DocumentVersion,
    ParseArtifact,
)
from app.repositories.bookmarks import get_bookmarked_tender_ids
from app.repositories.profiles import get_profile_by_workspace
from app.repositories.tenders import (
    get_tender_amendments,
    get_tender_by_id,
    get_tender_conditions,
    get_tenders,
)
from app.schemas.amendments import AmendmentChangeSchema, AmendmentHistoryResponse
from app.schemas.tenders import (
    ConditionSchema,
    EvaluationSchema,
    FindingSchema,
    TenderListResponse,
    TenderSchema,
)

router = APIRouter(prefix="/tenders", tags=["Tenders"])


@router.get("", response_model=TenderListResponse)
async def list_tenders(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    readiness: str | None = Query(default=None),
    saved: bool = Query(default=False),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> TenderListResponse:
    tenders, total = await get_tenders(
        db,
        workspace_id=ctx.workspace_id,
        category=category,
        search=search,
        saved_only=saved,
        limit=limit,
        offset=offset,
    )

    bookmarked_ids = await get_bookmarked_tender_ids(db, ctx.workspace_id)
    profile_pair = await get_profile_by_workspace(db, ctx.workspace_id)
    profile_facts = profile_pair[1].facts if profile_pair else {}
    now = system_clock.now()

    items: list[TenderSchema] = []
    for t in tenders:
        # Get conditions from current snapshot if present
        curr_snap = next((s for s in t.snapshots if s.is_current), None)
        conditions_list = curr_snap.conditions if curr_snap else []

        cond_schemas = [
            ConditionSchema(
                id=c.id,
                type=c.type,  # type: ignore[arg-type]
                label=c.label,
                requirement=c.requirement,
                quote=c.exact_quote,
                page=c.page_number,
                clause=c.clause_reference,
                threshold=float(c.threshold_amount) if c.threshold_amount else None,
                years=c.years,
                certificate=c.certificate_type,
                deadline=c.deadline_timestamp.isoformat() if c.deadline_timestamp else None,
                mandatory=c.mandatory,
            )
            for c in conditions_list
        ]

        # Evaluate against workspace profile
        eval_result = evaluate_tender(
            [c.model_dump() for c in cond_schemas],
            profile_facts,
            now=now,
        )

        findings_schemas = [
            FindingSchema(
                condition=ConditionSchema.model_validate(f["condition"]),
                status=f["status"],
                reason=f["reason"],
                supplier_value=f["supplier_value"],
            )
            for f in eval_result["findings"]
        ]

        eval_schema = EvaluationSchema(
            status=eval_result["status"],
            findings=findings_schemas,
            coverage_complete=eval_result["coverage_complete"],
            evaluated_at=now,
            snapshot_id=curr_snap.id if curr_snap else None,
        )

        # Filter by readiness query if requested
        if readiness and readiness.lower() != "all" and eval_schema.status != readiness.lower():
            continue

        pdf_urls = [d.source_url for d in t.documents if d.role == "main_notice"]
        amendment_urls = [d.source_url for d in t.documents if d.role == "corrigendum"]

        items.append(
            TenderSchema(
                id=t.id,
                reference=t.external_reference,
                title=t.title,
                description=t.description,
                issuer=t.issuer,
                category=t.category,
                value=t.estimated_value,
                deadline_text=t.deadline_text,
                deadline=t.deadline_at.isoformat() if t.deadline_at else None,
                relevance=t.relevance_score,
                source_url=t.source_url,
                pdf_urls=pdf_urls,
                amendment_urls=amendment_urls,
                provenance="live" if t.provenance == "live" else "sample",
                retrieved_at=t.created_at,
                amended=t.amended,
                conditions=cond_schemas,
                evaluation=eval_schema,
                saved=(t.id in bookmarked_ids),
            )
        )

    return TenderListResponse(items=items, total=total)


@router.get("/{tender_id}", response_model=TenderSchema)
async def get_tender_detail(
    tender_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> TenderSchema:
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        raise NotFoundError("Tender not found.")

    bookmarked_ids = await get_bookmarked_tender_ids(db, ctx.workspace_id)
    curr_snap = next((s for s in tender.snapshots if s.is_current), None)
    conditions_list = curr_snap.conditions if curr_snap else []

    cond_schemas = [
        ConditionSchema(
            id=c.id,
            type=c.type,  # type: ignore[arg-type]
            label=c.label,
            requirement=c.requirement,
            quote=c.exact_quote,
            page=c.page_number,
            clause=c.clause_reference,
            threshold=float(c.threshold_amount) if c.threshold_amount else None,
            years=c.years,
            certificate=c.certificate_type,
            deadline=c.deadline_timestamp.isoformat() if c.deadline_timestamp else None,
            mandatory=c.mandatory,
        )
        for c in conditions_list
    ]

    profile_pair = await get_profile_by_workspace(db, ctx.workspace_id)
    profile_facts = profile_pair[1].facts if profile_pair else {}
    now = system_clock.now()

    eval_result = evaluate_tender(
        [c.model_dump() for c in cond_schemas],
        profile_facts,
        now=now,
    )

    findings_schemas = [
        FindingSchema(
            condition=ConditionSchema.model_validate(f["condition"]),
            status=f["status"],
            reason=f["reason"],
            supplier_value=f["supplier_value"],
        )
        for f in eval_result["findings"]
    ]

    eval_schema = EvaluationSchema(
        status=eval_result["status"],
        findings=findings_schemas,
        coverage_complete=eval_result["coverage_complete"],
        evaluated_at=now,
        snapshot_id=curr_snap.id if curr_snap else None,
    )

    pdf_urls = [d.source_url for d in tender.documents if d.role == "main_notice"]
    amendment_urls = [d.source_url for d in tender.documents if d.role == "corrigendum"]

    return TenderSchema(
        id=tender.id,
        reference=tender.external_reference,
        title=tender.title,
        description=tender.description,
        issuer=tender.issuer,
        category=tender.category,
        value=tender.estimated_value,
        deadline_text=tender.deadline_text,
        deadline=tender.deadline_at.isoformat() if tender.deadline_at else None,
        relevance=tender.relevance_score,
        source_url=tender.source_url,
        pdf_urls=pdf_urls,
        amendment_urls=amendment_urls,
        provenance="live" if tender.provenance == "live" else "sample",
        retrieved_at=tender.created_at,
        amended=tender.amended,
        conditions=cond_schemas,
        evaluation=eval_schema,
        saved=(tender.id in bookmarked_ids),
    )


@router.get("/{tender_id}/conditions", response_model=list[ConditionSchema])
async def get_conditions_route(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ConditionSchema]:
    conditions = await get_tender_conditions(db, tender_id)
    return [
        ConditionSchema(
            id=c.id,
            type=c.type,  # type: ignore[arg-type]
            label=c.label,
            requirement=c.requirement,
            quote=c.exact_quote,
            page=c.page_number,
            clause=c.clause_reference,
            threshold=float(c.threshold_amount) if c.threshold_amount else None,
            years=c.years,
            certificate=c.certificate_type,
            deadline=c.deadline_timestamp.isoformat() if c.deadline_timestamp else None,
            mandatory=c.mandatory,
        )
        for c in conditions
    ]


@router.get("/{tender_id}/amendments", response_model=AmendmentHistoryResponse)
async def get_amendments_route(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AmendmentHistoryResponse:
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        raise NotFoundError("Tender not found.")

    changes = await get_tender_amendments(db, tender_id)
    change_schemas = [
        AmendmentChangeSchema(
            id=c.id,
            clause_identity=c.clause_identity,
            change_type=c.change_type,  # type: ignore[arg-type]
            before_text=c.before_text,
            after_text=c.after_text,
            material_change=c.material_change,
        )
        for c in changes
    ]

    return AmendmentHistoryResponse(
        tender_id=tender_id,
        snapshots_count=len(tender.snapshots),
        changes=change_schemas,
    )


@router.post("/{tender_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_tender_document(
    tender_id: UUID,
    file: UploadFile = File(...),
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        raise NotFoundError("Tender not found.")

    data = await file.read()
    if len(data) > 20971520:  # 20 MiB
        raise PayloadTooLargeError("File exceeds 20 MiB upload limit.")

    if not data.startswith(b"%PDF-"):
        raise AppError("INVALID_PDF_FILE", "Uploaded file must be a valid PDF.")

    sha256 = compute_sha256(data)
    storage = get_storage()
    storage_key = f"pdf/{sha256}.pdf"
    await storage.save_file(storage_key, data)

    # Extract pages
    pages = extract_pages_from_pdf(data)
    now = datetime.now(UTC)

    # Private manual upload document
    doc = Document(
        tender_id=tender_id,
        workspace_id=ctx.workspace_id,
        source_url=f"upload://{file.filename}",
        role="manual_upload",
        visibility="private",
        created_at=now,
    )
    db.add(doc)
    await db.flush()

    doc_version = DocumentVersion(
        document_id=doc.id,
        sha256=sha256,
        storage_key=storage_key,
        byte_size=len(data),
        page_count=len(pages),
        observed_at=now,
    )
    db.add(doc_version)
    await db.flush()

    parse_art = ParseArtifact(
        document_version_id=doc_version.id,
        parser_version="pymupdf-v1",
        page_data=pages,
        status="extracted",
        created_at=now,
    )
    db.add(parse_art)
    await db.commit()

    return {"status": "uploaded", "document_version_id": str(doc_version.id), "sha256": sha256}
