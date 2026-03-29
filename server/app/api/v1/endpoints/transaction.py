import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session as DBSession

from app.api.deps import current_user, require_csrf
from app.core.db import get_db
from app.models import User
from app.schemas import (
    TransactionBulkReclassifyRequest,
    TransactionBulkReclassifyResult,
    TransactionCSVRow,
    TransactionCreate,
    TransactionImportPreviewResult,
    TransactionImportRequest,
    TransactionImportResult,
    TransactionRead,
    TransactionReclassifyRequest,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService


router = APIRouter()


async def _parse_csv_rows(file: UploadFile) -> list[TransactionCSVRow]:
    try:
        contents = await file.read()
        text_stream = io.StringIO(contents.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded",
        ) from exc
    except csv.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file",
        ) from exc

    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is missing a header row",
        )

    rows: list[TransactionCSVRow] = []
    try:
        for row in reader:
            rows.append(
                TransactionCSVRow(
                    account_name=row.get("account_name"),
                    posted_at=row["posted_at"],
                    description=row["description"],
                    amount=row["amount"],
                    external_tx_id=row.get("external_tx_id"),
                    category_hint=row.get("category_hint"),
                )
            )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required column: {exc.args[0]}",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.errors(),
        ) from exc

    return rows


@router.post(
    "/",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    payload: TransactionCreate,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    return TransactionService.create_manual(
        db=db,
        user_id=user.id,
        data=payload,
    )


@router.get(
    "/",
    response_model=list[TransactionRead],
    status_code=status.HTTP_200_OK,
)
def list_transactions(
    account_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return TransactionService.list_for_user(
        db=db,
        user_id=user.id,
        account_id=account_id,
        category_id=category_id,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    status_code=status.HTTP_200_OK,
)
def get_transaction(
    transaction_id: UUID,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return TransactionService.get_one(
        db=db,
        user_id=user.id,
        transaction_id=transaction_id,
    )


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    status_code=status.HTTP_200_OK,
)
def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    return TransactionService.update_manual(
        db=db,
        user_id=user.id,
        transaction_id=transaction_id,
        data=payload,
    )


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_transaction(
    transaction_id: UUID,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    TransactionService.delete_manual(
        db=db,
        user_id=user.id,
        transaction_id=transaction_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/import/preview",
    response_model=TransactionImportPreviewResult,
    status_code=status.HTTP_200_OK,
)
async def preview_transaction_import(
    file: UploadFile = File(...),
    account_id: UUID = Form(...),
    import_source: str | None = Form(default=None),
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    rows = await _parse_csv_rows(file)
    payload = TransactionImportRequest(
        rows=rows,
        account_id=account_id,
        import_source=import_source,
        dry_run=True,
    )

    return TransactionService.preview_import(
        db=db,
        user_id=user.id,
        data=payload,
    )


@router.post(
    "/import/commit",
    response_model=TransactionImportResult,
    status_code=status.HTTP_200_OK,
)
async def commit_transaction_import(
    file: UploadFile = File(...),
    account_id: UUID = Form(...),
    import_source: str | None = Form(default=None),
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    rows = await _parse_csv_rows(file)
    payload = TransactionImportRequest(
        rows=rows,
        account_id=account_id,
        import_source=import_source,
        dry_run=False,
    )

    return TransactionService.import_rows(
        db=db,
        user_id=user.id,
        data=payload,
    )


@router.patch(
    "/{transaction_id}/reclassify",
    response_model=TransactionRead,
    status_code=status.HTTP_200_OK,
)
def reclassify_transaction(
    transaction_id: UUID,
    payload: TransactionReclassifyRequest,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    return TransactionService.reclassify(
        db=db,
        user_id=user.id,
        transaction_id=transaction_id,
        category_id=payload.category_id,
    )


@router.patch(
    "/reclassify/bulk",
    response_model=TransactionBulkReclassifyResult,
    status_code=status.HTTP_200_OK,
)
def bulk_reclassify_transactions(
    payload: TransactionBulkReclassifyRequest,
    db: DBSession = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_csrf),
):
    updated = TransactionService.bulk_reclassify(
        db=db,
        user_id=user.id,
        transaction_ids=payload.transaction_ids,
        category_id=payload.category_id,
    )
    return TransactionBulkReclassifyResult(updated=updated)
