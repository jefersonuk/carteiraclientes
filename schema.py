from dataclasses import dataclass
from typing import Dict, Optional, List
import pandas as pd

REQUIRED_CLIENT_FIELDS = [
    "client_id",
    "client_name",
    "birth_date",
    "income_value",
    "income_date",
    "employment_link",
    "last_movement_date",
    "account_type",
    "has_restrictive_flag",
    "is_in_loss_flag",
    "score_band",
    "final_stage",
    "max_delay_days",
    "has_valid_contact",
    "agency_is_main",
    "portfolio",
    "potential_pct",
    "avg_balance",
]

OPTIONAL_PRODUCT_FIELDS = [
    "product_name",
    "product_group",
    "contract_start_date",
    "present_value",
    "contract_value",
]

@dataclass
class ColumnMap:
    mapping: Dict[str, str]

    def get(self, key: str) -> Optional[str]:
        return self.mapping.get(key)

def available_columns(df: pd.DataFrame) -> List[str]:
    return [""] + list(df.columns)
