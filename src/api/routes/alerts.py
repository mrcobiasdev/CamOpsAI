"""Rotas da API para alertas."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage import get_db, AlertRepository
from src.api.schemas import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertLogResponse,
    AlertLogListResponse,
)

router = APIRouter(prefix="/alerts", tags=["Alertas"])


# ==================== Alert Rules ====================


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as regras de alerta."""
    repo = AlertRepository(db)
    rules = await repo.get_all_rules(enabled_only=enabled_only)
    return rules


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova regra de alerta."""
    repo = AlertRepository(db)
    new_rule = await repo.create_rule(
        name=rule.name,
        keywords=rule.keywords,
        phone_numbers=rule.phone_numbers,
        camera_ids=rule.camera_ids,
        enabled=rule.enabled,
        priority=rule.priority,
        cooldown_seconds=rule.cooldown_seconds,
    )

    # Atualiza o detector de keywords
    from src.main import alert_detector
    from src.alerts.detector import AlertRule as DetectorAlertRule

    alert_detector.add_rule(
        DetectorAlertRule(
            id=new_rule.id,
            name=new_rule.name,
            keywords=new_rule.keywords,
            phone_numbers=new_rule.phone_numbers,
            camera_ids=new_rule.camera_ids,
            enabled=new_rule.enabled,
            priority=new_rule.priority,
            cooldown_seconds=new_rule.cooldown_seconds,
        )
    )

    return new_rule


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma regra de alerta."""
    repo = AlertRepository(db)
    rule = await repo.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regra de alerta não encontrada",
        )
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: uuid.UUID,
    rule: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza uma regra de alerta."""
    repo = AlertRepository(db)
    updated = await repo.update_rule(
        rule_id=rule_id,
        name=rule.name,
        keywords=rule.keywords,
        phone_numbers=rule.phone_numbers,
        camera_ids=rule.camera_ids,
        enabled=rule.enabled,
        priority=rule.priority,
        cooldown_seconds=rule.cooldown_seconds,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regra de alerta não encontrada",
        )

    # Atualiza o detector de keywords
    from src.main import alert_detector
    from src.alerts.detector import AlertRule as DetectorAlertRule

    alert_detector.update_rule(
        DetectorAlertRule(
            id=updated.id,
            name=updated.name,
            keywords=updated.keywords,
            phone_numbers=updated.phone_numbers,
            camera_ids=updated.camera_ids,
            enabled=updated.enabled,
            priority=updated.priority,
            cooldown_seconds=updated.cooldown_seconds,
        )
    )

    return updated


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove uma regra de alerta."""
    repo = AlertRepository(db)
    deleted = await repo.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regra de alerta não encontrada",
        )

    # Remove do detector
    from src.main import alert_detector

    alert_detector.remove_rule(rule_id)


# ==================== Alert Logs ====================


@router.get("/logs", response_model=AlertLogListResponse)
async def list_alert_logs(
    rule_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista histórico de alertas enviados."""
    repo = AlertRepository(db)
    offset = (page - 1) * page_size

    logs = await repo.get_logs(
        rule_id=rule_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )

    return AlertLogListResponse(
        logs=logs,
        total=len(logs),  # TODO: implementar contagem real
        page=page,
        page_size=page_size,
    )


@router.get("/logs/{log_id}", response_model=AlertLogResponse)
async def get_alert_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um log de alerta."""
    repo = AlertRepository(db)
    logs = await repo.get_logs(limit=1)

    # Busca específica pelo ID
    for log in logs:
        if log.id == log_id:
            return log

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Log de alerta não encontrado",
    )


@router.post("/test/{rule_id}")
async def test_alert_rule(
    rule_id: uuid.UUID,
    test_description: str = "Teste de alerta: pessoa suspeita detectada na entrada",
    db: AsyncSession = Depends(get_db),
):
    """Testa uma regra de alerta com uma descrição de exemplo."""
    repo = AlertRepository(db)
    rule = await repo.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regra de alerta não encontrada",
        )

    from src.main import alert_detector

    # Testa detecção
    matches = alert_detector.detect(
        description=test_description,
        keywords=None,
        camera_id=None,
    )

    rule_matched = any(m.rule_id == rule_id for m in matches)

    return {
        "rule_id": str(rule_id),
        "rule_name": rule.name,
        "test_description": test_description,
        "would_trigger": rule_matched,
        "matches": [
            {
                "rule_name": m.rule_name,
                "keywords_matched": m.keywords_matched,
            }
            for m in matches
        ],
    }
