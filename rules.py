from __future__ import annotations
import pandas as pd
import numpy as np

def _score_n_to_int(score_band: str) -> int | None:
    if not isinstance(score_band, str):
        return None
    s = score_band.strip().upper()
    if not s.startswith("N"):
        return None
    try:
        return int(s[1:])
    except Exception:
        return None

def classify_farol(clients: pd.DataFrame, salario_minimo: float) -> pd.DataFrame:
    """Apply farol rules (Verde / Vermelho / Cinza) with explicit reasons."""
    df = clients.copy()

    reasons = []
    farol = []

    for _, r in df.iterrows():
        motivo = []

        months_mov = r.get("months_since_movement", np.nan)
        has_loss = bool(r.get("is_in_loss", False))
        has_restr = bool(r.get("has_restrictive", False))
        age = r.get("age", np.nan)
        income = r.get("income_value", np.nan)
        avg_balance = r.get("avg_balance", np.nan)

        # CINZA (Impedido)
        is_lost = pd.notna(months_mov) and months_mov > 18
        if is_lost:
            motivo.append("Movimentação > 18m (Perdido)")
        if has_loss:
            motivo.append("Em prejuízo")
        if has_restr:
            motivo.append("Restrição impeditiva")

        is_elder_block = (
            pd.notna(age) and age > 75
            and pd.notna(income) and income < 10_000
            and pd.notna(avg_balance) and avg_balance < 50_000
        )
        if is_elder_block:
            motivo.append("PF > 75a com renda < 10k e aplicações < 50k")

        if motivo:
            farol.append("Cinza")
            reasons.append(motivo)
            continue

        # VERDE (Encarteirável)
        ok = True

        if not (pd.notna(months_mov) and months_mov <= 6):
            ok = False
            if pd.notna(months_mov) and 6 < months_mov <= 18:
                motivo.append("Movimentação 6-18m (Inativo)")
            else:
                motivo.append("Sem movimento recente (não ativo)")

        acct = str(r.get("account_type", "")).lower()
        is_correntista = ("corrente" in acct) and ("poup" not in acct or "corrente" in acct)
        if not is_correntista:
            ok = False
            motivo.append("Não correntista (ex: poupança)")

        months_income = r.get("months_since_income_update", np.nan)
        if not (pd.notna(months_income) and months_income <= 48):
            ok = False
            motivo.append("Renda desatualizada (> 4 anos)")

        if not (pd.notna(income) and income > salario_minimo):
            ok = False
            motivo.append("Renda <= 1 salário mínimo")

        score_n = _score_n_to_int(str(r.get("score_band", "")))
        if not (score_n is not None and 1 <= score_n <= 4):
            ok = False
            motivo.append("Escore fora de N01-N04")

        stage = str(r.get("final_stage", "")).strip()
        if stage not in {"01", "1", "02", "2"}:
            ok = False
            motivo.append("Estágio final fora 01-02")

        max_delay = r.get("max_delay_days", 0)
        if pd.notna(max_delay) and float(max_delay) >= 60:
            ok = False
            motivo.append("Atraso >= 60 dias")

        if not bool(r.get("has_valid_contact", False)):
            ok = False
            motivo.append("Sem contato válido")

        if not bool(r.get("agency_is_main", False)):
            ok = False
            motivo.append("Conta principal fora da agência")

        if ok:
            farol.append("Verde")
            reasons.append(["Encarteirável (cumpre premissas)"])
        else:
            farol.append("Vermelho")
            reasons.append(motivo if motivo else ["Não encarteirável"])

    df["farol"] = farol
    df["farol_motivos"] = reasons
    df["is_encarteiravel"] = df["farol"].eq("Verde")
    df["is_impedido"] = df["farol"].eq("Cinza")
    return df
