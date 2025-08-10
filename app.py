import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2
from branca.element import MacroElement
from jinja2 import Template

# ------------- CONFIG -----------------
st.set_page_config(
    page_title="Cabo Crime Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ THEME / CSS ============
st.markdown('''
<style>
:root {
  --bg: #0b0f14;
  --panel: #0f1520;
  --panel-2:#0c1118;
  --accent: #33a1fd;
  --accent2:#14f195;
  --muted: #8c9aa6;
  --text:#e7eef6;
  --border:#182233;
  --glass: rgba(255,255,255,0.04);
}
html, body, [class*="css"]  {
  background-color: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
}
section.main > div {padding-top: 0rem;}
.block-container {padding-top: .6rem; max-width: 1400px;}
a {color: var(--accent)}

.header {
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding: 6px 6px 2px 6px;
}
.badges { display:flex; gap:8px; flex-wrap:wrap; }
.badge {
  background: linear-gradient(180deg,#111826 0%, #0b121c 100%);
  border: 1px solid var(--border);
  border-radius: 999px; padding: 6px 10px; font-size: 12px; color:white;
}
.badge b { color: #d8e6f5 }

.kpis {display:grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 8px 0 10px 0;}
.kpi {
  position: relative;
  border-radius: 18px;
  padding: 18px 18px;
  background: radial-gradient(1200px circle at -20% -20%, rgba(51,161,253,.08), transparent 35%),
              linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
  border:1px solid var(--border);
  box-shadow: 0 10px 35px rgba(0,0,0,.35);
  overflow:hidden;
}
.kpi .icon {
  position:absolute; right:14px; top:14px;
  width:36px; height:36px; border-radius:12px;
  background: linear-gradient(140deg, rgba(51,161,253,.25), rgba(20,241,149,.2));
  display:flex; align-items:center; justify-content:center; font-size:18px; color:#eaf3ff;
  border:1px solid #1b2b44;
}
.kpi .label {font-size:.72rem; color:white; letter-spacing:.06em; text-transform:uppercase}
.kpi .value { color:white;font-size:2.1rem; font-weight:800; margin-top:6px; line-height:1.1}
.kpi .sub {font-size:.75rem; color:white; margin-top:2px}

hr {border: none; height: 1px; background: #162034; margin: .6rem 0 1rem 0;}
@media (max-width: 1100px) {.kpis{grid-template-columns: repeat(2, 1fr);}}
@media (max-width: 700px) {.kpis{grid-template-columns: 1fr;}}
</style>
''', unsafe_allow_html=True)

# ====== TÍTULO PRINCIPAL ======
st.markdown("""
# 📍 Mapa Inteligente de Segurança Pública – Cabo de Santo Agostinho
### Monitoramento ao vivo, alertas e análise de cobertura policial
""")


st.markdown("<div class='header'><div><h3>🛰️ Cabo Crime Intelligence — <span style='opacity:.85'>Protótipo</span></h3><div style='color:#9fb0bf'>Mapa interativo com heatmap, pinos, alertas por raio e cobertura policial simulada.</div></div><div class='badges' id='badges'></div></div>", unsafe_allow_html=True)

# ------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("## ⚙️ Controles")
    modo = st.selectbox("Modo de dados", ["Simulação (CSV sintético)", "Futuro: Conexão com base real"], index=0)
    qtd = st.slider("Quantidade de incidentes a exibir", 50, 1200, 600, 50)
    filtro_tipo = st.multiselect("Tipos de crime", [], help="Populado após carregar os dados")
    periodo = st.select_slider("Período (dias, retroativos)", options=[7, 15, 30, 60, 90, 180], value=60)
    st.markdown("---")
    st.markdown("### 🔔 Alertas (simulado)")
    lat_user = st.number_input("Sua latitude", value=-8.283, format="%.6f")
    lon_user = st.number_input("Sua longitude", value=-35.030, format="%.6f")
    raio_m = st.slider("Raio de alerta (metros)", 100, 3000, 800, 50)
    desenhar_circulo = st.checkbox("Desenhar círculo do seu raio no mapa", value=True)
    st.caption("Clique no mapa para ajustar a posição.")
    st.markdown("---")
    st.markdown("### 🧭 Camadas e Legenda")
    mostrar_raios = st.checkbox("Mostrar raios de cobertura policial", value=True)
    raio_patrulha_m = st.slider("Raio padrão de patrulha (m)", 500, 5000, 1500, 100)
    mostrar_minimap = st.checkbox("Mostrar mini-mapa", value=True)
    mostrar_legenda = st.checkbox("Mostrar legenda", value=True)

# ------------- DATA -----------------
@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv("data/crimes_sinteticos.csv", parse_dates=["data"])
    return df

df = carregar_dados()
df = df.sort_values("data", ascending=False)
df = df.head(qtd)
recorte = df[df["data"] >= (pd.Timestamp.today().normalize() - pd.Timedelta(days=int(periodo)))]

# Atualiza multiselect com tipos
with st.sidebar:
    tipos = sorted(df["tipo_crime"].unique().tolist())
    filtro_tipo = st.multiselect("Tipos de crime", tipos, default=tipos[:4])

if filtro_tipo:
    recorte = recorte[recorte["tipo_crime"].isin(filtro_tipo)]

# ------------- BADGES (dinâmicas) -------------
badges_html = f"<span class='badge'>Período: <b>últimos {periodo} dias</b></span>" \
              f"<span class='badge'>Incidentes exibidos: <b>{recorte.shape[0]}</b></span>" \
              f"<span class='badge'>Raio alerta: <b>{int(raio_m)} m</b></span>"
st.markdown(f"<script>document.getElementById('badges').innerHTML = `{badges_html}`;</script>", unsafe_allow_html=True)

# ------------- KPIs -----------------
tot_incidentes = int(recorte.shape[0])
ultimos7 = int((df["data"] >= (pd.Timestamp.today().normalize() - pd.Timedelta(days=7))).sum())
rua_top = recorte.groupby("rua").size().sort_values(ascending=False).head(1)
rua_top_nome = rua_top.index[0] if len(rua_top) else "-"
rua_top_qtd = int(rua_top.iloc[0]) if len(rua_top) else 0

col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    st.markdown(f"<div class='kpi'><div class='icon'>📊</div><div class='label'>Incidentes (período)</div><div class='value'>{tot_incidentes:,}</div><div class='sub'>Com filtros aplicados</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='kpi'><div class='icon'>⏱️</div><div class='label'>Últimos 7 dias</div><div class='value'>{ultimos7:,}</div><div class='sub'>Panorama geral</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi'><div class='icon'>📍</div><div class='label'>Rua mais incidente</div><div class='value'>{rua_top_nome}</div><div class='sub'>Top endereço</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='kpi'><div class='icon'>🔥</div><div class='label'>Ocorrências (rua top)</div><div class='value'>{rua_top_qtd:,}</div><div class='sub'>No período selecionado</div></div>", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ------------- MAPA -----------------
center_lat, center_lon = -8.283, -35.030
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="cartodb dark_matter", control_scale=True)
if mostrar_minimap:
    MiniMap(toggle_display=True, minimized=True).add_to(m)

# Heatmap (layer)
heat_group = folium.FeatureGroup(name="Heatmap", show=True).add_to(m)
heat_data = recorte[["latitude","longitude","severidade"]].values.tolist()
if len(heat_data) > 0:
    HeatMap(heat_data, radius=14, blur=18, min_opacity=0.2).add_to(heat_group)

# Pinos com cluster
pins_group = folium.FeatureGroup(name="Pinos (por tipo)", show=True).add_to(m)
cluster = MarkerCluster().add_to(pins_group)
for _, r in recorte.iterrows():
    color = "#33a1fd" if r["tipo_crime"] in ["Roubo","Assalto"] else "#14f195"
    folium.CircleMarker(
        location=[r["latitude"], r["longitude"]],
        radius=6,
        fill=True,
        fill_opacity=0.9,
        opacity=0.2,
        color=color,
        tooltip=f"{r['tipo_crime']} • {r['bairro']}",
        popup=folium.Popup(f"<b>{r['tipo_crime']}</b><br>Rua: {r['rua']}<br>Bairro: {r['bairro']}<br>Data: {r['data']}", max_width=260)
    ).add_to(cluster)

# Cobertura policial (simulada)
bases_group = folium.FeatureGroup(name="Cobertura Policial (simulada)", show=mostrar_raios).add_to(m)
bases = [
    {"nome":"Batalhão Centro", "lat":-8.285, "lon":-35.035},
    {"nome":"Base Pontezinha", "lat":-8.246, "lon":-35.063},
    {"nome":"Base Gaibu", "lat":-8.336, "lon":-34.944},
    {"nome":"Base Suape", "lat":-8.351, "lon":-34.956}
]
if mostrar_raios:
    for b in bases:
        folium.Circle(
            location=[b["lat"], b["lon"]],
            radius=float(raio_patrulha_m),
            color="#33a1fd",
            weight=1,
            fill=True,
            fill_opacity=0.05,
            tooltip=f"🚓 {b['nome']} (raio {raio_patrulha_m} m)"
        ).add_to(bases_group)
        folium.CircleMarker(location=[b["lat"], b["lon"]], radius=4, color="#33a1fd", fill=True).add_to(bases_group)

# Posição do usuário
user_group = folium.FeatureGroup(name="Seu ponto e raio", show=True).add_to(m)
folium.Marker(
    [lat_user, lon_user],
    tooltip="Seu ponto (simulado)",
    icon=folium.Icon(color="lightgray", icon="user", prefix="fa")
).add_to(user_group)
if desenhar_circulo:
    folium.Circle(
        location=[lat_user, lon_user],
        radius=float(raio_m),
        color="#ffcc00",
        weight=2,
        fill=True,
        fill_opacity=0.05,
        tooltip=f"Seu raio de alerta: {int(raio_m)} m"
    ).add_to(user_group)

# ------- Legenda custom (rica) -------
# Estatísticas para legenda
violent_types = ["Roubo","Assalto"]
n_violent = int(recorte[recorte["tipo_crime"].isin(violent_types)].shape[0])
n_outros = int(recorte[~recorte["tipo_crime"].isin(violent_types)].shape[0])

class FloatLegend(MacroElement):
    _template = Template(u'''
        {% macro script(this,kwargs) %}
        var legend = L.control({position: 'bottomright'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'legend');
            div.innerHTML = `
              <div style="background: rgba(10,15,20,.92); border:1px solid #182233; padding:12px 14px; border-radius:14px; color:#e7eef6; font-size:12px; min-width:220px;">
                <div style="font-weight:800; margin-bottom:8px; font-size:13px;">Legenda do Mapa</div>
                <div style="display:grid; gap:6px;">
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span style="width:14px;height:14px;border-radius:50%;background:#33a1fd;display:inline-block;"></span>
                    <span>Crimes violentos (Roubo/Assalto) — <b>''' + str(n_violent) + '''</b></span>
                  </div>
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span style="width:14px;height:14px;border-radius:50%;background:#14f195;display:inline-block;"></span>
                    <span>Demais crimes — <b>''' + str(n_outros) + '''</b></span>
                  </div>
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span style="width:40px;height:10px;background:linear-gradient(90deg,rgba(255,255,255,.15),rgba(255,255,255,.45));display:inline-block;border-radius:6px"></span>
                    <span>Heatmap (intensidade de ocorrências)</span>
                  </div>
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span style="width:14px;height:14px;border:2px solid #ffcc00;border-radius:50%;display:inline-block;"></span>
                    <span>Seu raio de alerta</span>
                  </div>
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span style="width:14px;height:14px;border:2px solid #33a1fd;border-radius:50%;display:inline-block;"></span>
                    <span>Raio de cobertura policial</span>
                  </div>
                </div>
              </div>`;
            return div;
        };
        legend.addTo({{this._parent.get_name()}});
        {% endmacro %}
    ''')
    def __init__(self):
        super().__init__()

if mostrar_legenda:
    m.add_child(FloatLegend())

# Layer control
folium.LayerControl(collapsed=True).add_to(m)

# Renderiza e captura interações
map_state = st_folium(m, height=620, width=None)

# Se usuário clicar no mapa, atualiza posição
if map_state and map_state.get("last_clicked"):
    lat_user = float(map_state["last_clicked"]["lat"])
    lon_user = float(map_state["last_clicked"]["lng"])
    st.info(f"📍 Posição ajustada pelo clique: {lat_user:.6f}, {lon_user:.6f}")

# ------------- ALERTAS POR RAIO -----------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

recorte = recorte.copy()
recorte["dist_m"] = recorte.apply(lambda r: haversine(lat_user, lon_user, r["latitude"], r["longitude"]), axis=1)
perto = recorte[recorte["dist_m"] <= float(raio_m)].sort_values("dist_m")

with st.container():
    st.markdown("#### 🔔 Alertas no raio definido")
    if len(perto) == 0:
        st.success("Nenhum incidente no raio configurado. ✅")
    else:
        st.error(f"⚠️ {len(perto)} incidentes no raio de {int(raio_m)} m do seu ponto.")
        st.dataframe(perto[["data","tipo_crime","rua","bairro","dist_m"]].assign(dist_m=lambda d: d["dist_m"].round(1)))

# ------------- RANKINGS -----------------
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("#### 🧭 Rankings rápidos")
colA, colB, colC = st.columns(3)

top_ruas = recorte.groupby("rua").size().sort_values(ascending=False).head(10).reset_index(name="ocorrencias")
top_tipos = recorte.groupby("tipo_crime").size().sort_values(ascending=False).head(10).reset_index(name="ocorrencias")
top_bairros = recorte.groupby("bairro").size().sort_values(ascending=False).head(10).reset_index(name="ocorrencias")

with colA: st.dataframe(top_ruas)
with colB: st.dataframe(top_tipos)
with colC: st.dataframe(top_bairros)

st.caption("Protótipo – dados sintéticos. Para dados reais, adapte a função `carregar_dados()` e o esquema de colunas.")
