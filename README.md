# Nossa Organização — V2

Versão completa do app financeiro do casal.

## O que tem
- Resumo Lucas + Julia
- Contas do mês com FLAG pago
- Projeção de 6 meses
- Dívidas e parcelamentos
- Gastos extras
- Investimentos
- Metas
- Histórico
- PIN de acesso
- Foto do casal opcional (`foto.jpg`)

## Secrets no Streamlit Cloud
Em **Manage app > Settings > Secrets**:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA_SECRET_KEY"
APP_PIN = "UM-PIN-SO-DE-VOCES"
```

## Tabela Supabase
A tabela `gastos` precisa ter:
- id
- data
- pessoa
- descricao
- categoria
- tipo
- valor
- status
- observacao

## Foto do casal
Se quiser a foto fixa no topo, adicione um arquivo chamado `foto.jpg` na raiz do repositório.
