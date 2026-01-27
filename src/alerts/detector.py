"""Detector de palavras-chave para alertas."""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class AlertMatch:
    """Resultado de um match de alerta."""

    rule_id: uuid.UUID
    rule_name: str
    keywords_matched: List[str]
    phone_numbers: List[str]
    priority: str


@dataclass
class AlertRule:
    """Regra de alerta para detecção."""

    id: uuid.UUID
    name: str
    keywords: List[str]
    phone_numbers: List[str]
    camera_ids: Optional[List[str]] = None  # None = todas as câmeras
    enabled: bool = True
    priority: str = "normal"
    cooldown_seconds: int = 300


class KeywordDetector:
    """Detecta palavras-chave em descrições de eventos."""

    def __init__(self):
        self._rules: Dict[uuid.UUID, AlertRule] = {}
        self._last_alert_time: Dict[uuid.UUID, datetime] = {}
        self._keyword_patterns: Dict[uuid.UUID, List[re.Pattern]] = {}

    def add_rule(self, rule: AlertRule):
        """Adiciona uma regra de alerta."""
        self._rules[rule.id] = rule
        # Compila padrões regex para keywords
        self._keyword_patterns[rule.id] = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for kw in rule.keywords
        ]
        logger.info(f"Regra de alerta adicionada: {rule.name} ({rule.id})")

    def remove_rule(self, rule_id: uuid.UUID):
        """Remove uma regra de alerta."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            del self._keyword_patterns[rule_id]
            logger.info(f"Regra de alerta removida: {rule_id}")

    def update_rule(self, rule: AlertRule):
        """Atualiza uma regra existente."""
        self.add_rule(rule)  # add_rule sobrescreve se já existir

    def get_rules(self) -> List[AlertRule]:
        """Retorna todas as regras."""
        return list(self._rules.values())

    def clear_rules(self):
        """Remove todas as regras."""
        self._rules.clear()
        self._keyword_patterns.clear()
        self._last_alert_time.clear()

    def detect(
        self,
        description: str,
        keywords: Optional[List[str]] = None,
        camera_id: Optional[uuid.UUID] = None,
    ) -> List[AlertMatch]:
        """Detecta matches de alertas em uma descrição.

        Args:
            description: Descrição do evento
            keywords: Lista de keywords já extraídas (opcional)
            camera_id: ID da câmera de origem (opcional)

        Returns:
            Lista de AlertMatch para regras que deram match
        """
        matches: List[AlertMatch] = []
        text_to_search = description.lower()

        # Adiciona keywords ao texto de busca se fornecidas
        if keywords:
            text_to_search += " " + " ".join(keywords).lower()

        for rule_id, rule in self._rules.items():
            # Verifica se a regra está ativa
            if not rule.enabled:
                continue

            # Verifica se a regra se aplica a esta câmera
            if rule.camera_ids and camera_id:
                if str(camera_id) not in rule.camera_ids:
                    continue

            # Verifica cooldown
            if not self._check_cooldown(rule_id, rule.cooldown_seconds):
                continue

            # Busca matches de keywords
            matched_keywords = self._find_matches(rule_id, text_to_search)

            if matched_keywords:
                matches.append(
                    AlertMatch(
                        rule_id=rule_id,
                        rule_name=rule.name,
                        keywords_matched=matched_keywords,
                        phone_numbers=rule.phone_numbers,
                        priority=rule.priority,
                    )
                )
                # Atualiza timestamp do último alerta
                self._last_alert_time[rule_id] = datetime.utcnow()
                logger.info(
                    f"Alerta detectado: {rule.name} - Keywords: {matched_keywords}"
                )

        return matches

    def _find_matches(self, rule_id: uuid.UUID, text: str) -> List[str]:
        """Encontra keywords que dão match no texto."""
        patterns = self._keyword_patterns.get(rule_id, [])
        rule = self._rules[rule_id]
        matched = []

        for i, pattern in enumerate(patterns):
            if pattern.search(text):
                matched.append(rule.keywords[i])

        return matched

    def _check_cooldown(self, rule_id: uuid.UUID, cooldown_seconds: int) -> bool:
        """Verifica se o cooldown da regra já passou."""
        last_alert = self._last_alert_time.get(rule_id)

        if last_alert is None:
            return True

        elapsed = datetime.utcnow() - last_alert
        return elapsed >= timedelta(seconds=cooldown_seconds)

    def reset_cooldown(self, rule_id: uuid.UUID):
        """Reseta o cooldown de uma regra."""
        if rule_id in self._last_alert_time:
            del self._last_alert_time[rule_id]

    def get_rule_stats(self, rule_id: uuid.UUID) -> Optional[dict]:
        """Retorna estatísticas de uma regra."""
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        last_alert = self._last_alert_time.get(rule_id)
        return {
            "id": str(rule_id),
            "name": rule.name,
            "enabled": rule.enabled,
            "keywords_count": len(rule.keywords),
            "last_alert": last_alert.isoformat() if last_alert else None,
            "cooldown_seconds": rule.cooldown_seconds,
        }
