from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.deps import require_admin
from app.core.db import get_session
from app.services.export_service import ExportService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/books/export.csv")
async def export_books_csv(
    session: AsyncSession = Depends(get_session),
    _admin=Depends(require_admin),
) -> StreamingResponse:
    service = ExportService()
    generator = service.stream_books_csv(session)

    headers = {
        "Content-Disposition": 'attachment; filename="books.csv"',
    }
    return StreamingResponse(generator, media_type="text/csv", headers=headers)
