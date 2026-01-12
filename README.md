# Dashboard PF Carteira (Encarteiramento + Crédito Gerencial)

Este app lê dados **apenas via upload de arquivo (CSV)** na sessão do usuário.
Nenhum dado é versionado no GitHub e nada é salvo em disco pelo app.

## Rodar local
1) Python 3.10+
2) `pip install -r requirements.txt`
3) `streamlit run app.py`

## Privacidade e proteção
- Não suba dados no repositório.
- O CSV deve ser enviado via upload no app.
- O app não escreve arquivos localmente.
- Telemetria do Streamlit desabilitada via `.streamlit/config.toml`.

## Gate por senha (opcional)
Crie `.streamlit/secrets.toml` localmente (não commitar):

```
APP_PASSWORD="sua_senha_forte"
```

No Streamlit Cloud, configure o mesmo em Secrets.


## Estrutura
Os módulos Python ficam na raiz do projeto (ex: `privacy.py`, `rules.py`) para evitar problemas de import no Streamlit Cloud.
