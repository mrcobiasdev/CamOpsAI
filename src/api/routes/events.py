"""Rotas da API para eventos."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage import get_db, EventRepository
from src.api.schemas import EventResponse, EventListResponse, TimelineResponse

router = APIRouter(prefix="/events", tags=["Eventos"])


@router.get("", response_model=EventListResponse)
async def list_events(
    camera_id: Optional[uuid.UUID] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista eventos com filtros."""
    repo = EventRepository(db)
    offset = (page - 1) * page_size

    if keyword:
        events = await repo.search_by_keyword(
            keyword=keyword,
            camera_id=camera_id,
            limit=page_size,
        )
    elif camera_id:
        events = await repo.get_by_camera(
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset,
        )
    else:
        events = await repo.get_timeline(
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset,
        )

    return EventListResponse(
        events=events,
        total=len(events),  # TODO: implementar contagem real
        page=page,
        page_size=page_size,
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    camera_ids: Optional[List[uuid.UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Retorna timeline de eventos."""
    repo = EventRepository(db)
    events = await repo.get_timeline(
        start_date=start_date,
        end_date=end_date,
        camera_ids=camera_ids,
        limit=limit,
    )

    return TimelineResponse(
        events=events,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um evento."""
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )
    return event


@router.get("/{event_id}/frame")
async def get_event_frame(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o frame associado a um evento."""
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )

    if not event.frame_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frame não disponível para este evento",
        )

    return FileResponse(
        event.frame_path,
        media_type="image/jpeg",
        filename=f"frame_{event_id}.jpg",
    )


@router.get("/{event_id}/annotated-frame")
async def get_event_annotated_frame(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o frame anotado associado a um evento."""
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )

    if not event.annotated_frame_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotated frame not found",
        )

    return FileResponse(
        event.annotated_frame_path,
        media_type="image/jpeg",
        filename=f"frame_{event_id}_annotated.jpg",
    )


@router.get("/search/keywords")
async def search_by_keywords(
    keywords: List[str] = Query(..., min_length=1),
    camera_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Busca eventos por múltiplas palavras-chave."""
    repo = EventRepository(db)
    all_events = []

    for keyword in keywords:
        events = await repo.search_by_keyword(
            keyword=keyword,
            camera_id=camera_id,
            limit=limit,
        )
        all_events.extend(events)

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_events = []
    for event in all_events:
        if event.id not in seen:
            seen.add(event.id)
            unique_events.append(event)

    # Ordena por timestamp
    unique_events.sort(key=lambda e: e.timestamp, reverse=True)

    return {"events": unique_events[:limit], "keywords_searched": keywords}
