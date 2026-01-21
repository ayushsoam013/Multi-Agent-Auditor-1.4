import json
import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DecisionRule(BaseModel):
    condition: Dict[str, Any]
    action: str # PASS, FAIL, REVIEW
    reason: str
    confidence: float = 1.0

class DecisionGrid(BaseModel):
    rules: List[DecisionRule] = []
    default_action: str = "REVIEW"

class DecisionGridLoader:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("DECISION_GRID_PATH", "config/decision_grid.json")
        self.grid = DecisionGrid()
        self.load_rules()

    def load_rules(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.grid = DecisionGrid(**data)
                logger.info(f"Loaded {len(self.grid.rules)} rules from {self.config_path}")
            else:
                logger.warning(f"Decision grid config not found at {self.config_path}. Using defaults.")
                # Basic default rules could be added here
        except Exception as e:
            logger.error(f"Error loading decision grid: {str(e)}")

    def get_decision(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate facts against rules and return the best match.
        """
        for rule in self.grid.rules:
            if self._matches(rule.condition, facts):
                return {
                    "action": rule.action,
                    "reason": rule.reason,
                    "confidence": rule.confidence
                }
        
        return {
            "action": self.grid.default_action,
            "reason": "No specific rules matched. Falling back to default.",
            "confidence": 0.5
        }

    def _matches(self, condition: Dict[str, Any], facts: Dict[str, Any]) -> bool:
        """
        Simple equality based matching. 
        Can be extended to support complex operators (GT, LT, IN, etc.)
        """
        for key, value in condition.items():
            if facts.get(key) != value:
                return False
        return True

# Singleton instance
decision_grid_loader = DecisionGridLoader()
