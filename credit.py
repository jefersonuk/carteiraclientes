from __future__ import annotations
import pandas as pd
import numpy as np

def credit_eligibility(df: pd.DataFrame) -> pd.Series:
    return (
        df["farol"].eq("Verde")
        & (~df["has_restrictive"].fillna(False))
        & (~df["is_in_loss"].fillna(False))
        & (df["max_delay_days"].fillna(0) < 60)
        & (df["months_since_income_update"].fillna(10_000) <= 48)
        & (df["months_since_movement"].fillna(10_000) <= 6)
        & (df["has_valid_contact"].fillna(False))
    )

def score_priority_credit(df: pd.DataFrame, salario_minimo: float) -> pd.Series:
    score_band = df["score_band"].astype(str).str.upper().str.strip()
    score_n = pd.to_numeric(score_band.str.replace("N", "", regex=False), errors="coerce")

    risk = np.select(
        [score_n.isin([1, 2]), score_n.isin([3, 4]), score_n.isin([5, 6]), score_n.isin([7, 8, 9])],
        [30, 22, 12, 5],
        default=8,
    )

    stage = df["final_stage"].astype(str).str.strip()
    stage_pts = np.where(stage.isin(["01", "1"]), 15, np.where(stage.isin(["02", "2"]), 10, 3))

    income = df["income_value"].fillna(0)
    income_pts = np.clip((income / (salario_minimo * 10)) * 20, 0, 20)

    vínculo = df["employment_link"].astype(str).str.lower()
    link_pts = np.where(vínculo.str.contains("ativo|clt|servidor|aposent"), 10, 6)

    rec = df["months_since_movement"].fillna(999)
    rec_pts = np.clip(20 - (rec * 3), 0, 20)

    delay = df["max_delay_days"].fillna(0)
    delay_pts = np.select(
        [delay == 0, (delay > 0) & (delay <= 15), (delay > 15) & (delay <= 30), (delay > 30) & (delay < 60)],
        [15, 10, 6, 2],
        default=0,
    )

    pot = df["potential_pct"].fillna(0)
    pot_pts = np.clip((pot / 100) * 10, 0, 10)

    products = df["products_count"].fillna(0)
    gap_pts = np.clip(8 - products, 0, 8)

    total = risk + stage_pts + income_pts + link_pts + rec_pts + delay_pts + pot_pts + gap_pts

    total = np.where(df["has_restrictive"].fillna(False), total * 0.3, total)
    total = np.where(df["is_in_loss"].fillna(False), total * 0.1, total)

    return np.clip(total, 0, 100)
