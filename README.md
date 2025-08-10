# Mapa de Criminalidade – Cabo de Santo Agostinho (Protótipo)

Este é um **protótipo estilo "Apple/Tesla/Microsoft"** para mapear criminalidade no Cabo de Santo Agostinho.
Ele roda com **Streamlit** e mostra:

- Heatmap de ocorrências
- Pinos por tipo de crime (com cluster)
- Ranking de ruas mais incidentes
- Raios de cobertura policial (simulados)
- **Alertas** quando há ocorrência no raio do usuário (simulado)
- Painel escuro e moderno

> **Fase 1: Simulação** – dados sintéticos já inclusos em `data/crimes_sinteticos.csv`  
> **Fase 2: Dados reais** – basta apontar a leitura para a base oficial (SDS-PE/BO etc.)

---

## Como rodar

```bash
# 1) Crie um ambiente (opcional, mas recomendado)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Instale as dependências
pip install -r requirements.txt

# 3) Rode o app
streamlit run app.py
```

O navegador abrirá automaticamente. Se não abrir, acesse o link mostrado no terminal (geralmente http://localhost:8501).

---

## Estrutura
```
crime_map_cabo/
├─ app.py
├─ requirements.txt
├─ README.md
└─ data/
   └─ crimes_sinteticos.csv
```

---

## Próximos passos (dados reais)
- Conectar na base oficial (SDS-PE) ou planilhas/CSV com colunas: data, tipo_crime, rua, bairro, latitude, longitude, turno, fonte.
- Substituir a função `carregar_dados()` para ler a base real.
- Habilitar ingestão de denúncias/relatos pelo app (com moderação).
- Integrar **Firebase Cloud Messaging** para push notifications no app mobile/web.
- Substituir polígonos de cobertura pela geografia real das companhias/viaturas (PostGIS).
- Adicionar modelos de predição de risco por horário/local (scikit-learn).

Boa demo! 🚀

---

## Publicar no Streamlit Cloud

1. Crie um repositório no GitHub (ex.: `crime-map-cabo`) e suba estes arquivos:
   - `app.py`
   - `requirements.txt`
   - `data/crimes_sinteticos.csv`
   - `.streamlit/config.toml`
   - `README.md`
   - `.gitignore`
2. Acesse https://share.streamlit.io → **New app** → selecione seu repositório.
3. Em **Main file path**, informe `app.py` e clique em **Deploy**.

### Comandos Git (opcional)
```bash
git init
git add .
git commit -m "Publicação inicial - Mapa Inteligente de Segurança Pública (Cabo)"
git branch -M main
git remote add origin https://github.com/<SEU_USUARIO>/crime-map-cabo.git
git push -u origin main
```
