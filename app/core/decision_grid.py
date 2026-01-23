import json
import os
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class DecisionGridLoader:
    """
    Service for loading and querying the deterministic Decision Grid.
    The grid maps a 5-bit binary state (representing audit findings)
    to a human-readable decision message.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv(
            "DECISION_GRID_PATH", "config/decision_grid.json"
        )
        self.grid: Dict[str, str] = {}
        self.load_rules()

    def load_rules(self):
        """Loads the truth table from a JSON configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.grid = json.load(f)
                logger.info(
                    f"Loaded {len(self.grid)} decision rules from {self.config_path}"
                )
            else:
                logger.warning(
                    f"Decision grid config not found at {self.config_path}. Using empty grid."
                )
        except Exception as e:
            logger.error(f"Error loading decision grid: {str(e)}")

    def get_decision_text(self, facts: Dict[str, bool]) -> Tuple[str, str]:
        """
        Translates a set of boolean facts into a 5-digit binary code and
        looks up the corresponding audit message.

        FACT BIT-MAPPING:
        1st bit: photo_category (Mismatch between Photo and Category)
        2nd bit: title_category (Mismatch between Title and Category)
        3rd bit: photo_title    (Mismatch between Photo and Title)
        4th bit: photo_specs    (Mismatch between Photo and Specs)
        5th bit: title_specs    (Mismatch between Title and Specs)

        Example: '10010' means Photo/Category mismatch AND Photo/Specs mismatch.
        """
        code_list = [
            "1" if facts.get("photo_category") else "0",
            "1" if facts.get("title_category") else "0",
            "1" if facts.get("photo_title") else "0",
            "1" if facts.get("photo_specs") else "0",
            "1" if facts.get("title_specs") else "0",
        ]
        code = "".join(code_list)

        # Lookup message from the truth table; default to 'Review Required' if code is unknown.
        message = self.grid.get(code, "Review Required")
        return message, code


# Singleton instance
decision_grid_loader = DecisionGridLoader()
