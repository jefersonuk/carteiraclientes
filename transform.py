from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime
from .schema import ColumnMap

def _to_datetime(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

def _to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def months_since(date_series: pd.Series, ref: datetime) -> pd.Series:
    delta_days = (ref - date_series).dt.days
    return delta_days / 30.4375

def build_client_table(raw: pd.DataFrame, colmap: ColumnMap) -> pd.DataFrame:
    """Build 1-row-per-client table from raw (product-level) data."""
    df = raw.copy()
    now = datetime.now()

    def col(key: str):
        c = colmap.get(key)
        return df[c] if c else pd.Series([np.nan] * len(df))

    df["_client_id"] = col("client_id").astype(str)
    df["_client_name"] = col("client_name").astype(str)
    df["_birth_date"] = _to_datetime(col("birth_date"))
    df["_income_value"] = _to_numeric(col("income_value"))
    df["_income_date"] = _to_datetime(col("income_date"))
    df["_employment_link"] = col("employment_link").astype(str)
    df["_last_movement_date"] = _to_datetime(col("last_movement_date"))
    df["_account_type"] = col("account_type").astype(str)
    df["_has_restrictive"] = col("has_restrictive_flag").fillna(False).astype(bool)
    df["_is_in_loss"] = col("is_in_loss_flag").fillna(False).astype(bool)
    df["_score_band"] = col("score_band").astype(str)
    df["_final_stage"] = col("final_stage").astype(str)
    df["_max_delay_days"] = _to_numeric(col("max_delay_days")).fillna(0)
    df["_has_valid_contact"] = col("has_valid_contact").fillna(False).astype(bool)
    df["_agency_is_main"] = col("agency_is_main").fillna(False).astype(bool)
    df["_portfolio"] = col("portfolio").astype(str)
    df["_potential_pct"] = _to_numeric(col("potential_pct"))
    df["_avg_balance"] = _to_numeric(col("avg_balance"))

    age_years = (now - df["_birth_date"]).dt.days / 365.25
    df["_age"] = age_years

    df["_months_since_movement"] = months_since(df["_last_movement_date"], now)
    df["_months_since_income_update"] = months_since(df["_income_date"], now)

    prod_name_col = colmap.get("product_name")
    df["_product_name"] = df[prod_name_col].astype(str) if prod_name_col else ""

    agg = df.groupby("_client_id", as_index=False).agg(
        client_name=("_client_name", "first"),
        age=("_age", "first"),
        birth_date=("_birth_date", "first"),
        income_value=("_income_value", "first"),
        income_date=("_income_date", "first"),
        employment_link=("_employment_link", "first"),
        last_movement_date=("_last_movement_date", "max"),
        months_since_movement=("_months_since_movement", "min"),
        months_since_income_update=("_months_since_income_update", "min"),
        account_type=("_account_type", "first"),
        has_restrictive=("_has_restrictive", "max"),
        is_in_loss=("_is_in_loss", "max"),
        score_band=("_score_band", "first"),
        final_stage=("_final_stage", "first"),
        max_delay_days=("_max_delay_days", "max"),
        has_valid_contact=("_has_valid_contact", "max"),
        agency_is_main=("_agency_is_main", "max"),
        portfolio=("_portfolio", "first"),
        potential_pct=("_potential_pct", "first"),
        avg_balance=("_avg_balance", "first"),
        products_count=("_product_name", lambda x: x.replace("nan", "").nunique()),
        products_list=("_product_name", lambda x: sorted({p for p in x.tolist() if p and p.lower() != "nan"})),
    )

    return agg.rename(columns={"_client_id": "client_id"})
