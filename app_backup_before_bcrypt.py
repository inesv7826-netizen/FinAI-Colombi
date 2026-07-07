from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime, date
from collections import defaultdict

ICON_512_B64 = "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"
ICON_192_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAAEk0lEQVR4nO3dMW8cRRgG4L2TJURHRUmFLVJSEAqawA8gcUyHbVqggYIWCmqEsIOoKKEDhERLCYljCjociYiCBkRFCkBUpkAYByyC/M7OzGWeR1uf1/u9nvm+3bvz4qk3f53gvNam4+PW58AKW7Y+AVabABERICJri9ZnwEqzAhFZmwxhBKxARASIiCaaiBWIiAARESAixngimmgitjAiAkREgIgIEBFNNBFjPBFbGJG11ifwX756Z731KfTiiVe/bX0KZ1tceuOX1udwl0OhuZeLPYWplwDJzTn0kKTGAZKbIhomqWUTLT2lNLySi0uvN1iBDvdEZxYXX6m9FC0X01T5kJ75HO6t1y7o0xVXoJuiU8uTtZaiej2Q9NRU7WpXCpD01FfnmtcIkPS0UuHKz95ES09bN2duq5fT8TTfcSA9HTjYW5+vxDNuYQf70tOL+Wrh7RxE5gqQ5ac3M1VkuZiOix/S06eD/fXitbaFESkfoBv7G8Vfk1KKV6fwGC89/buxv7EaYzwj8LmwERUseskV6Po1+9dqKFgpWxgRASJS7Gm8/Wu1XL+2UaTuPhs/sBKlt4URESAiZQL05bsaoNVTpGpuJA4tr74tjIgpbGxx9a1ARASIiCZ6aJpoGhMgIl1/S+u5Pfjwhcd2P2t9Fnf58eC9H754u/VZlGeMH1tcfU300DTRNCZARASIiAAR0UQPLa++MX5snsbTlgAR0QMNzY1EGrs/H6aez+8/f//N+8+0PosVYwUiYowfW4mn8RI0rrz6tjAiAkREgIgIEBF3oofmaTwZT+NpS4CICBARTfTQSjTR/OWBhx55/LXbxV/2zu3Pv/v0xeIv2wlbGBFj/NiM8bSliR6a90TTmAARESAieqCheRpPxhhPWwJERICIaKL/NuBHm91IpDFT2NhMYbQlQEQ00UPTRNOYABERICLG+LH5f2EkNNE0JkBEBIiIABHxNb9Dy6tvjB+bp/G0JUBE3EgcmhuJNCZARASIiDF+bJ7Gk9BE05gAEREgIgJERBM9NN9Qdrbffjr6+q1HW5/FKvA0nrYEiIgAEdFED82daBoTICL35xjP/2WMpy1N9NB6aaKffeFWkdehpiJVs4URESAieqBxFSn9cjqeihyXd7VBq+Ty7q0idbeFEREgIiUDZBdbFQUrpYkeUcGi28KIFJvC/jyu7NjFendlp8z8NdcUJkM9K14dWxiR5WI6Ln5s7hy1/r04w+bOUfFaz7UCyVBvZqqILYzIjAGyCPVjvloUHuP/cWxuy1B7m9tH85V4uZimWY+rMtTU1e2jWetboweSoVYqXPlKTbQM1VfnmtebwmSopmpXe7H98p06P+nEJx9cqPwTh1L5D3X2Jvrfx5alaDZbM7fMZxw7L9VegU58/KGlqJit59v8Wba8E93qd77/NLySLVeg06xG59DDX+Bit48AnfhIku7luQ5yc6K7AJ0mTCe6Cs1pXQeI/nk7BxHfUEbE58KI2MKICBARASIiQEQ00USM8URsYUQEiIgAEdFEE7ECEREgIsZ4IlYgIppoIlYgIgJERICI/AHN91ChUPk65QAAAABJRU5ErkJggg=="

app = Flask(__name__)
app.secret_key = "finai_secret_key_2024"
DB_NAME = "finai.db"

# ─── UTILIDAD COP ────────────────────────────────────────────────────────────

def cop(valor):
    """Formatea un numero como pesos colombianos: $ 1.234.567"""
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        valor = 0
    return "$ {:,.0f}".format(valor).replace(",", ".")

# ─── DATABASE ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ingresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        monto REAL NOT NULL,
        categoria TEXT NOT NULL,
        descripcion TEXT,
        fecha TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        monto REAL NOT NULL,
        categoria TEXT NOT NULL,
        descripcion TEXT,
        fecha TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        monto_objetivo REAL NOT NULL,
        monto_actual REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── FINANCIAL ENGINE ────────────────────────────────────────────────────────

def get_financial_data(uid):
    conn = get_db()
    ingresos = conn.execute("SELECT * FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    gastos   = conn.execute("SELECT * FROM gastos   WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    metas    = conn.execute("SELECT * FROM metas    WHERE usuario_id=?", (uid,)).fetchall()
    conn.close()
    return ingresos, gastos, metas

def calcular_metricas(ingresos, gastos):
    total_ing = sum(i["monto"] for i in ingresos)
    total_gas = sum(g["monto"] for g in gastos)
    ahorro    = total_ing - total_gas
    pct_gasto  = (total_gas / total_ing * 100) if total_ing > 0 else 0
    pct_ahorro = (ahorro   / total_ing * 100) if total_ing > 0 else 0

    score = 100
    if total_ing > 0:
        ratio = total_gas / total_ing
        if ratio >= 1.0:   score = max(0,  10)
        elif ratio >= 0.9: score = max(0,  25)
        elif ratio >= 0.8: score = max(0,  40)
        elif ratio >= 0.7: score = max(0,  55)
        elif ratio >= 0.5: score = max(0,  70)
        elif ratio >= 0.3: score = max(0,  85)
        else:              score = 100
    else:
        score = 0

    if    score >= 80: clasificacion = "Excelente"
    elif  score >= 60: clasificacion = "Buena"
    elif  score >= 40: clasificacion = "Regular"
    else:              clasificacion = "Riesgosa"

    return {
        "total_ingresos": total_ing,
        "total_gastos":   total_gas,
        "ahorro":         ahorro,
        "pct_gasto":      round(pct_gasto, 1),
        "pct_ahorro":     round(pct_ahorro, 1),
        "score":          score,
        "clasificacion":  clasificacion,
    }

HORMIGA_CATEGORIAS = {"dulces","bebidas","snacks","comida rápida","entretenimiento","café","domicilios","otros"}
HORMIGA_MONTO_MAX  = 25000  # COP: compras pequeñas y frecuentes (tinto, snack, domicilio, etc.)

def detectar_hormiga(gastos):
    pequeños = [g for g in gastos if g["monto"] <= HORMIGA_MONTO_MAX and g["categoria"].lower() in HORMIGA_CATEGORIAS]
    total_hormiga = sum(g["monto"] for g in pequeños)
    return pequeños, total_hormiga

def generar_recomendaciones(metricas, gastos, metas):
    recs = []
    pct_gas = metricas["pct_gasto"]
    pct_aho = metricas["pct_ahorro"]

    if pct_gas > 90:
        recs.append("⚠️ Tus gastos superan el 90% de tus ingresos. Reduce gastos no esenciales de inmediato.")
    elif pct_gas > 70:
        recs.append("📉 Tus gastos son mayores al 70% de tus ingresos. Considera recortar gastos variables.")
    if pct_aho < 10 and metricas["total_ingresos"] > 0:
        recs.append("💰 Tu tasa de ahorro es menor al 10%. Intenta ahorrar al menos el 20% de tus ingresos (regla 50/30/20).")
    if metricas["ahorro"] < 0:
        recs.append("🚨 Estás gastando más de lo que ganas. Revisa tus finanzas urgentemente.")

    if gastos:
        cat_totales = defaultdict(float)
        for g in gastos:
            cat_totales[g["categoria"].lower()] += g["monto"]
        top_cat = max(cat_totales, key=cat_totales.get)
        if top_cat == "entretenimiento":
            recs.append(f"🎮 Entretenimiento es tu categoría de gasto más alta ({cop(cat_totales[top_cat])}). Evalúa reducirla.")

    for m in metas:
        faltante = m["monto_objetivo"] - m["monto_actual"]
        if faltante > 0:
            recs.append(f"🎯 Para tu meta '{m['nombre']}' te faltan {cop(faltante)}. ¡Sigue ahorrando!")

    if not recs:
        recs.append("✅ ¡Tu situación financiera es saludable! Mantén tus hábitos. Considera explorar un CDT para hacer crecer tu ahorro.")
    return recs

def gastos_por_categoria(gastos):
    cat = defaultdict(float)
    for g in gastos:
        cat[g["categoria"]] += g["monto"]
    return dict(cat)

# ─── CHATBOT ENGINE ──────────────────────────────────────────────────────────

def chatbot_responder(pregunta, uid):
    ingresos, gastos, metas = get_financial_data(uid)
    metricas  = calcular_metricas(ingresos, gastos)
    hormiga_g, total_hormiga = detectar_hormiga(gastos)
    recs      = generar_recomendaciones(metricas, gastos, metas)
    cat_dict  = gastos_por_categoria(gastos)
    p = pregunta.lower()

    if any(x in p for x in ["gastando mucho","gasto mucho","gasto","gastos"]):
        pct = metricas["pct_gasto"]
        if pct > 80:
            return f"Sí, estás gastando el {pct}% de tus ingresos. Eso es alto. Te recomiendo revisar categorías como {max(cat_dict, key=cat_dict.get) if cat_dict else 'ninguna aún'} que es donde más gastas."
        elif pct > 50:
            return f"Estás gastando el {pct}% de tus ingresos. Es manejable pero hay margen de mejora. Tu categoría principal de gasto es '{max(cat_dict, key=cat_dict.get) if cat_dict else 'ninguna'}' con {cop(max(cat_dict.values()) if cat_dict else 0)}."
        else:
            return f"No, estás gastando solo el {pct}% de tus ingresos. ¡Vas muy bien! Sigues ahorrando el {metricas['pct_ahorro']}%."

    if any(x in p for x in ["situación","situacion","financiera","finanzas","cómo estoy","como estoy"]):
        return (f"Tu salud financiera es {metricas['clasificacion']} (score {metricas['score']}/100). "
                f"Ingresos: {cop(metricas['total_ingresos'])} | Gastos: {cop(metricas['total_gastos'])} | "
                f"Ahorro: {cop(metricas['ahorro'])} ({metricas['pct_ahorro']}%). {recs[0]}")

    if any(x in p for x in ["gasto más alto","mayor gasto","categoría","categoria","donde gasto"]):
        if cat_dict:
            top = max(cat_dict, key=cat_dict.get)
            return f"Tu gasto más alto está en la categoría '{top}' con un total de {cop(cat_dict[top])}. Le siguen: " + ", ".join([f"{k} ({cop(v)})" for k, v in sorted(cat_dict.items(), key=lambda x: -x[1])[:3] if k != top]) + "."
        return "Aún no tienes gastos registrados. ¡Empieza a registrar para obtener análisis!"

    if any(x in p for x in ["hormiga","pequeños","pequeñas"]):
        if hormiga_g:
            return f"Sí, detecté {len(hormiga_g)} gastos hormiga por un total de {cop(total_hormiga)}. Son compras pequeñas frecuentes (≤{cop(HORMIGA_MONTO_MAX)}) en categorías como tinto/café, snacks, domicilios o entretenimiento. Suman más de lo que crees al mes."
        return "No detecté gastos hormiga significativos. Buen control de gastos pequeños."

    if any(x in p for x in ["ahorrar","ahorro","guardar","ahorrando"]):
        if metricas["pct_ahorro"] < 10:
            return f"Actualmente ahorras solo el {metricas['pct_ahorro']}%. La regla 50/30/20 sugiere: 50% necesidades, 30% deseos, 20% ahorro. Te recomiendo reducir gastos en '{max(cat_dict, key=cat_dict.get) if cat_dict else 'gastos variables'}' y automatizar tu ahorro, por ejemplo programando una transferencia el día de pago."
        return f"Estás ahorrando el {metricas['pct_ahorro']}% de tus ingresos ({cop(metricas['ahorro'])}). ¡Muy bien! Considera invertir parte de ese ahorro en un CDT o un fondo de inversión colectiva (FIC)."

    if any(x in p for x in ["recomiendas","recomendación","recomendacion","consejo","consejos","qué hago","que hago"]):
        return " | ".join(recs[:3])

    if any(x in p for x in ["meta","metas","objetivo","objetivos","propósito"]):
        if metas:
            resp = []
            for m in metas:
                pct = (m["monto_actual"] / m["monto_objetivo"] * 100) if m["monto_objetivo"] > 0 else 0
                resp.append(f"'{m['nombre']}': {cop(m['monto_actual'])} de {cop(m['monto_objetivo'])} ({pct:.0f}%)")
            return "Progreso de tus metas: " + " | ".join(resp)
        return "Aún no tienes metas de ahorro. ¡Crea una desde el menú Metas para empezar a enfocarte!"

    if any(x in p for x in ["cdt","fondo de emergencia","emergencia","invertir","inversion","inversión"]):
        return "En Colombia, un buen punto de partida es tener un fondo de emergencia de 3 a 6 meses de gastos fijos en un producto líquido. Para hacer crecer tus ahorros con bajo riesgo, los CDT y los Fondos de Inversión Colectiva (FIC) son opciones comunes en entidades vigiladas por la Superintendencia Financiera."

    if any(x in p for x in ["hola","buenas","hey","saludo"]):
        return f"¡Hola! Soy FinAI, tu asistente financiero. Tu score actual es {metricas['score']}/100 ({metricas['clasificacion']}). Puedes preguntarme sobre tus gastos, ahorro, metas, CDT o pedir recomendaciones."

    if any(x in p for x in ["score","puntuación","puntuacion","calificación","calificacion"]):
        return f"Tu score financiero es {metricas['score']}/100, clasificado como '{metricas['clasificacion']}'. Gastas el {metricas['pct_gasto']}% de tus ingresos y ahorras el {metricas['pct_ahorro']}%."

    return (f"Entiendo tu pregunta. Basado en tus datos: ingresos {cop(metricas['total_ingresos'])}, "
            f"gastos {cop(metricas['total_gastos'])}, ahorro {cop(metricas['ahorro'])}. "
            f"Score: {metricas['score']}/100 ({metricas['clasificacion']}). "
            f"Puedes preguntarme sobre gastos, ahorro, metas, gastos hormiga, CDT o pedir recomendaciones.")

# ─── TEMPLATES ───────────────────────────────────────────────────────────────

PWA_HEAD_TAGS = """
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0a0e1a">
<link rel="icon" type="image/png" href="/icon-192.png">
<link rel="apple-touch-icon" href="/icon-192.png">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js');
  });
}
</script>
"""

BASE_STYLE = PWA_HEAD_TAGS + """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  :root {
    --bg:       #0a0e1a;
    --bg2:      #111827;
    --bg3:      #1a2234;
    --card:     #161d2e;
    --border:   #1e2d45;
    --accent:   #3b82f6;
    --accent2:  #6366f1;
    --green:    #10b981;
    --red:      #ef4444;
    --yellow:   #f59e0b;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --radius:   14px;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
  .layout { display:flex; min-height:100vh; }

  .sidebar {
    width:240px; background:var(--card); border-right:1px solid var(--border);
    display:flex; flex-direction:column; padding:24px 0; position:fixed;
    top:0; left:0; height:100vh; z-index:100;
  }
  .sidebar-logo {
    padding:0 24px 28px; border-bottom:1px solid var(--border);
    display:flex; align-items:center; gap:10px;
  }
  .logo-icon {
    width:38px; height:38px; background:linear-gradient(135deg,var(--accent),var(--accent2));
    border-radius:10px; display:flex; align-items:center; justify-content:center;
    font-size:18px; font-weight:800; color:#fff; flex-shrink:0;
  }
  .logo-text { font-size:20px; font-weight:800; letter-spacing:-0.5px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .nav { padding:20px 12px; flex:1; display:flex; flex-direction:column; gap:4px; }
  .nav a {
    display:flex; align-items:center; gap:10px; padding:10px 14px;
    border-radius:10px; color:var(--muted); text-decoration:none;
    font-size:14px; font-weight:500; transition:all .2s;
  }
  .nav a:hover, .nav a.active {
    background:rgba(59,130,246,.12); color:var(--text);
  }
  .nav a.active { color:var(--accent); }
  .nav-icon { font-size:17px; width:20px; text-align:center; }
  .sidebar-footer { padding:16px 12px; border-top:1px solid var(--border); }
  .sidebar-footer a {
    display:flex; align-items:center; gap:10px; padding:10px 14px;
    border-radius:10px; color:var(--red); text-decoration:none; font-size:14px; font-weight:500;
    transition:all .2s;
  }
  .sidebar-footer a:hover { background:rgba(239,68,68,.1); }

  .main { margin-left:240px; flex:1; padding:32px; min-height:100vh; }
  .page-title { font-size:26px; font-weight:800; margin-bottom:6px; letter-spacing:-0.5px; }
  .page-sub  { color:var(--muted); font-size:14px; margin-bottom:28px; }

  .card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:24px;
  }
  .cards-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }
  .stat-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:20px; }
  .stat-label { font-size:12px; color:var(--muted); font-weight:500; text-transform:uppercase; letter-spacing:.6px; margin-bottom:8px; }
  .stat-value { font-size:26px; font-weight:800; letter-spacing:-1px; }
  .stat-value.green  { color:var(--green); }
  .stat-value.red    { color:var(--red); }
  .stat-value.yellow { color:var(--yellow); }
  .stat-value.blue   { color:var(--accent); }
  .stat-sub  { font-size:12px; color:var(--muted); margin-top:4px; }

  .score-ring { position:relative; width:100px; height:100px; margin:0 auto 12px; }
  .score-ring svg { transform:rotate(-90deg); }
  .score-text { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    text-align:center; }
  .score-num { font-size:22px; font-weight:800; }
  .score-cls { font-size:10px; color:var(--muted); }

  .form-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; }
  .form-group { display:flex; flex-direction:column; gap:6px; }
  label { font-size:13px; color:var(--muted); font-weight:500; }
  input, select, textarea {
    background:var(--bg3); border:1px solid var(--border); color:var(--text);
    border-radius:8px; padding:10px 14px; font-size:14px; font-family:inherit;
    transition:border .2s; outline:none;
  }
  input:focus, select:focus, textarea:focus { border-color:var(--accent); }
  textarea { resize:vertical; min-height:80px; }
  select option { background:var(--bg3); }
  .btn {
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    color:#fff; border:none; border-radius:8px; padding:10px 22px;
    font-size:14px; font-weight:600; cursor:pointer; transition:opacity .2s; font-family:inherit;
  }
  .btn:hover { opacity:.85; }
  .btn-sm { padding:7px 16px; font-size:13px; }
  .btn-outline {
    background:transparent; border:1px solid var(--border); color:var(--text);
    border-radius:8px; padding:9px 20px; font-size:14px; font-weight:600;
    cursor:pointer; transition:all .2s; font-family:inherit;
  }
  .btn-outline:hover { border-color:var(--accent); color:var(--accent); }

  .alert { border-radius:10px; padding:14px 18px; font-size:14px; margin-bottom:16px; }
  .alert-warning { background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.3); color:var(--yellow); }
  .alert-danger  { background:rgba(239,68,68,.1);  border:1px solid rgba(239,68,68,.3);  color:var(--red); }
  .alert-success { background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3); color:var(--green); }
  .alert-info    { background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,.3); color:var(--accent); }

  .table-wrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th { text-align:left; padding:10px 14px; color:var(--muted); font-weight:500;
       font-size:12px; text-transform:uppercase; letter-spacing:.5px;
       border-bottom:1px solid var(--border); }
  td { padding:12px 14px; border-bottom:1px solid rgba(255,255,255,.04); }
  tr:last-child td { border-bottom:none; }
  tr:hover td { background:rgba(255,255,255,.02); }
  .badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:11px; font-weight:600; text-transform:capitalize;
  }
  .badge-green  { background:rgba(16,185,129,.15); color:var(--green); }
  .badge-red    { background:rgba(239,68,68,.15);  color:var(--red); }
  .badge-blue   { background:rgba(59,130,246,.15); color:var(--accent); }
  .badge-yellow { background:rgba(245,158,11,.15); color:var(--yellow); }

  .progress-bar { height:6px; background:var(--bg3); border-radius:10px; overflow:hidden; margin-top:8px; }
  .progress-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); border-radius:10px; transition:width .6s; }

  .chat-box { display:flex; flex-direction:column; height:420px; }
  .chat-messages { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px; }
  .chat-messages::-webkit-scrollbar { width:4px; }
  .chat-messages::-webkit-scrollbar-thumb { background:var(--border); border-radius:4px; }
  .msg { max-width:80%; padding:11px 16px; border-radius:12px; font-size:14px; line-height:1.5; }
  .msg-user { background:linear-gradient(135deg,var(--accent),var(--accent2)); color:#fff;
              align-self:flex-end; border-bottom-right-radius:3px; }
  .msg-bot  { background:var(--bg3); color:var(--text); align-self:flex-start;
              border-bottom-left-radius:3px; border:1px solid var(--border); }
  .chat-input-row { display:flex; gap:10px; padding:16px; border-top:1px solid var(--border); }
  .chat-input-row input { flex:1; }

  .auth-wrap { min-height:100vh; display:flex; align-items:center; justify-content:center;
               background:radial-gradient(ellipse at top left,rgba(59,130,246,.15) 0%,var(--bg) 60%); }
  .auth-card { width:420px; background:var(--card); border:1px solid var(--border);
               border-radius:20px; padding:40px; }
  .auth-logo { text-align:center; margin-bottom:32px; }
  .auth-logo .logo-icon { width:52px; height:52px; font-size:24px; margin:0 auto 12px; }
  .auth-logo h1 { font-size:28px; font-weight:800; letter-spacing:-1px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .auth-logo p { color:var(--muted); font-size:14px; margin-top:4px; }
  .auth-form { display:flex; flex-direction:column; gap:16px; }
  .auth-form .btn { width:100%; padding:13px; font-size:15px; }
  .auth-link { text-align:center; font-size:13px; color:var(--muted); }
  .auth-link a { color:var(--accent); text-decoration:none; font-weight:600; }
  .error-msg { background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.3);
               color:var(--red); border-radius:8px; padding:10px 14px; font-size:13px; }

  .charts-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:24px; }
  .chart-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:20px; }
  .chart-title { font-size:14px; font-weight:600; margin-bottom:16px; color:var(--text); }

  @media(max-width:768px){
    .sidebar { width:60px; }
    .sidebar-logo .logo-text, .nav a span, .sidebar-footer a span { display:none; }
    .main { margin-left:60px; padding:16px; }
    .charts-grid { grid-template-columns:1fr; }
    .cards-grid  { grid-template-columns:1fr 1fr; }
  }
  .two-col { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
  @media(max-width:900px){ .two-col { grid-template-columns:1fr; } }
  .mt16 { margin-top:16px; }
  .mt24 { margin-top:24px; }
  .flex-between { display:flex; justify-content:space-between; align-items:center; }
  .section-title { font-size:16px; font-weight:700; margin-bottom:16px; }
</style>
"""

SIDEBAR = """
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">F</div>
    <div class="logo-text">FinAI</div>
  </div>
  <nav class="nav">
    <a href="/dashboard" class="{a_dash}"><span class="nav-icon">📊</span><span>Dashboard</span></a>
    <a href="/ingresos" class="{a_ing}"><span class="nav-icon">💵</span><span>Ingresos</span></a>
    <a href="/gastos"   class="{a_gas}"><span class="nav-icon">💳</span><span>Gastos</span></a>
    <a href="/historial" class="{a_his}"><span class="nav-icon">📋</span><span>Historial</span></a>
    <a href="/metas"    class="{a_met}"><span class="nav-icon">🎯</span><span>Metas</span></a>
    <a href="/diagnostico" class="{a_dia}"><span class="nav-icon">🩺</span><span>Diagnóstico</span></a>
    <a href="/chatbot"  class="{a_cha}"><span class="nav-icon">🤖</span><span>Chatbot IA</span></a>
    <a href="/graficas" class="{a_gra}"><span class="nav-icon">📈</span><span>Gráficas</span></a>
  </nav>
  <div class="sidebar-footer">
    <a href="/logout"><span class="nav-icon">🚪</span><span>Cerrar sesión</span></a>
  </div>
</div>
"""

def sidebar(active=""):
    keys = ["dash","ing","gas","his","met","dia","cha","gra"]
    d = {f"a_{k}": ("active" if k == active else "") for k in keys}
    return SIDEBAR.format(**d)

# Se crea la base de datos apenas se importa el modulo (necesario para gunicorn,
# que NO ejecuta el bloque "if __name__ == '__main__':")
init_db()

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "uid" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email","").strip()
        pw    = request.form.get("password","")
        conn  = get_db()
        user  = conn.execute("SELECT * FROM usuarios WHERE email=? AND password=?",
                             (email, hash_password(pw))).fetchone()
        conn.close()
        if user:
            session["uid"]    = user["id"]
            session["nombre"] = user["nombre"]
            return redirect(url_for("dashboard"))
        error = "Email o contraseña incorrectos."
    html = BASE_STYLE + """
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-logo">
          <div class="logo-icon">F</div>
          <h1>FinAI</h1>
          <p>Tu asistente de inteligencia financiera</p>
        </div>
        """ + (f'<div class="error-msg">{error}</div>' if error else "") + """
        <form class="auth-form" method="POST">
          <div class="form-group">
            <label>Email</label>
            <input type="email" name="email" placeholder="tu@email.com" required>
          </div>
          <div class="form-group">
            <label>Contraseña</label>
            <input type="password" name="password" placeholder="••••••••" required>
          </div>
          <button class="btn">Iniciar sesión</button>
        </form>
        <div class="auth-link" style="margin-top:20px">
          ¿No tienes cuenta? <a href="/registro">Crear cuenta</a>
        </div>
      </div>
    </div>
    """
    return render_template_string(html)

@app.route("/registro", methods=["GET","POST"])
def registro():
    error = ""
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        email  = request.form.get("email","").strip()
        pw     = request.form.get("password","")
        if not nombre or not email or not pw:
            error = "Todos los campos son obligatorios."
        elif len(pw) < 6:
            error = "La contraseña debe tener al menos 6 caracteres."
        else:
            try:
                conn = get_db()
                conn.execute("INSERT INTO usuarios (nombre,email,password) VALUES (?,?,?)",
                             (nombre, email, hash_password(pw)))
                conn.commit()
                conn.close()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Ese email ya está registrado."
    html = BASE_STYLE + """
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-logo">
          <div class="logo-icon">F</div>
          <h1>FinAI</h1>
          <p>Crea tu cuenta gratuita</p>
        </div>
        """ + (f'<div class="error-msg">{error}</div>' if error else "") + """
        <form class="auth-form" method="POST">
          <div class="form-group">
            <label>Nombre completo</label>
            <input type="text" name="nombre" placeholder="Tu nombre" required>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" name="email" placeholder="tu@email.com" required>
          </div>
          <div class="form-group">
            <label>Contraseña</label>
            <input type="password" name="password" placeholder="Mínimo 6 caracteres" required>
          </div>
          <button class="btn">Crear cuenta</button>
        </form>
        <div class="auth-link" style="margin-top:20px">
          ¿Ya tienes cuenta? <a href="/login">Iniciar sesión</a>
        </div>
      </div>
    </div>
    """
    return render_template_string(html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    ingresos, gastos, metas = get_financial_data(uid)
    m = calcular_metricas(ingresos, gastos)
    hormiga_g, total_hormiga = detectar_hormiga(gastos)
    recs = generar_recomendaciones(m, gastos, metas)

    score      = m["score"]
    circum     = 2 * 3.14159 * 40
    dash_offset = circum * (1 - score / 100)
    score_color = "#10b981" if score >= 80 else "#3b82f6" if score >= 60 else "#f59e0b" if score >= 40 else "#ef4444"

    metas_html = ""
    for mt in metas:
        pct = min(100, (mt["monto_actual"] / mt["monto_objetivo"] * 100)) if mt["monto_objetivo"] > 0 else 0
        metas_html += f"""
        <div style="margin-bottom:16px">
          <div class="flex-between">
            <span style="font-size:14px;font-weight:600">{mt['nombre']}</span>
            <span style="font-size:13px;color:var(--muted)">{cop(mt['monto_actual'])} / {cop(mt['monto_objetivo'])}</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%"></div></div>
          <div style="font-size:11px;color:var(--muted);margin-top:4px">{pct:.0f}% completado</div>
        </div>"""

    recs_html = "".join([f'<div class="alert alert-info" style="margin-bottom:8px;padding:10px 14px">{r}</div>' for r in recs])
    hormiga_alert = f'<div class="alert alert-warning">🐜 Se detectaron <strong>{len(hormiga_g)} gastos hormiga</strong> por un total de <strong>{cop(total_hormiga)}</strong>. ¡Cuidado con los pequeños gastos frecuentes!</div>' if hormiga_g else ""

    ahorro_cls = "green" if m["ahorro"] >= 0 else "red"

    html = BASE_STYLE + """
    <div class="layout">
    """ + sidebar("dash") + f"""
    <div class="main">
      <div class="page-title">Dashboard Financiero</div>
      <div class="page-sub">Bienvenido, {session['nombre']} · {date.today().strftime('%d %b %Y')}</div>

      {hormiga_alert}

      <div class="cards-grid">
        <div class="stat-card">
          <div class="stat-label">Ingresos Totales</div>
          <div class="stat-value green">{cop(m['total_ingresos'])}</div>
          <div class="stat-sub">{len(ingresos)} transacciones</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Gastos Totales</div>
          <div class="stat-value red">{cop(m['total_gastos'])}</div>
          <div class="stat-sub">{len(gastos)} transacciones</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Ahorro Neto</div>
          <div class="stat-value {ahorro_cls}">{cop(m['ahorro'])}</div>
          <div class="stat-sub">{m['pct_ahorro']}% de ingresos</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Gasto / Ingreso</div>
          <div class="stat-value yellow">{m['pct_gasto']}%</div>
          <div class="stat-sub">Ratio actual</div>
        </div>
      </div>

      <div class="two-col">
        <div class="card" style="text-align:center">
          <div class="section-title" style="text-align:left">Salud Financiera</div>
          <div class="score-ring">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" stroke-width="8"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="{score_color}" stroke-width="8"
                stroke-dasharray="{circum:.2f}" stroke-dashoffset="{dash_offset:.2f}"
                stroke-linecap="round"/>
            </svg>
            <div class="score-text">
              <div class="score-num" style="color:{score_color}">{score}</div>
              <div class="score-cls">/ 100</div>
            </div>
          </div>
          <div style="font-size:18px;font-weight:700;margin-bottom:4px">{m['clasificacion']}</div>
          <div style="font-size:13px;color:var(--muted)">Puntuación financiera</div>
        </div>
        <div class="card">
          <div class="section-title">Recomendaciones IA</div>
          {recs_html}
        </div>
      </div>

      <div class="card mt24">
        <div class="section-title">Progreso de Metas</div>
        {metas_html if metas_html else '<div style="color:var(--muted);font-size:14px">No tienes metas registradas. <a href="/metas" style="color:var(--accent)">Crear meta →</a></div>'}
      </div>
    </div>
    </div>
    """
    return render_template_string(html)

CATEGORIAS_ING = ["Salario","Freelance","Negocio propio","Inversiones","Arriendo recibido","Regalo","Otro"]
CATEGORIAS_GAS = ["Vivienda","Alimentación","Transporte","Servicios públicos","Salud","Educación","Entretenimiento","Ropa","Deudas/Créditos","Suscripciones","Café","Domicilios","Dulces","Bebidas","Snacks","Comida rápida","Otros"]

@app.route("/ingresos", methods=["GET","POST"])
def ingresos():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    msg = ""
    if request.method == "POST":
        monto = request.form.get("monto","")
        cat   = request.form.get("categoria","")
        desc  = request.form.get("descripcion","")
        fecha = request.form.get("fecha", str(date.today()))
        if monto and cat:
            conn = get_db()
            conn.execute("INSERT INTO ingresos (usuario_id,monto,categoria,descripcion,fecha) VALUES (?,?,?,?,?)",
                         (uid, float(monto), cat, desc, fecha))
            conn.commit()
            conn.close()
            msg = "✅ Ingreso registrado correctamente."
        else:
            msg = "⚠️ Completa todos los campos requeridos."

    conn = get_db()
    lista_ing = conn.execute("SELECT * FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    conn.close()
    filas = "".join([f"""<tr>
        <td>{r['fecha']}</td><td>{r['categoria']}</td><td>{r['descripcion'] or '—'}</td>
        <td style="color:var(--green);font-weight:600">+{cop(r['monto'])}</td>
      </tr>""" for r in lista_ing])

    opts = "".join([f'<option value="{c}">{c}</option>' for c in CATEGORIAS_ING])
    html = BASE_STYLE + """<div class="layout">""" + sidebar("ing") + f"""
    <div class="main">
      <div class="page-title">Registrar Ingreso</div>
      <div class="page-sub">Agrega una nueva fuente de ingreso (en pesos colombianos COP)</div>
      {"<div class='alert alert-success'>" + msg + "</div>" if "✅" in msg else ""}
      {"<div class='alert alert-warning'>" + msg + "</div>" if "⚠️" in msg else ""}
      <div class="card" style="max-width:600px;margin-bottom:24px">
        <form method="POST">
          <div class="form-grid">
            <div class="form-group">
              <label>Monto (COP) *</label>
              <input type="number" name="monto" step="1" min="1" placeholder="Ej: 2500000" required>
            </div>
            <div class="form-group">
              <label>Categoría *</label>
              <select name="categoria" required><option value="">Seleccionar...</option>{opts}</select>
            </div>
            <div class="form-group">
              <label>Descripción</label>
              <input type="text" name="descripcion" placeholder="Descripción opcional">
            </div>
            <div class="form-group">
              <label>Fecha</label>
              <input type="date" name="fecha" value="{date.today()}">
            </div>
          </div>
          <button class="btn mt16" type="submit">Registrar Ingreso</button>
        </form>
      </div>
      <div class="card">
        <div class="section-title">Mis Ingresos</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Fecha</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
            <tbody>
              {filas if filas else "<tr><td colspan='4' style='text-align:center;color:var(--muted);padding:24px'>No hay ingresos registrados aún.</td></tr>"}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

@app.route("/gastos", methods=["GET","POST"])
def gastos():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    msg = ""
    if request.method == "POST":
        monto = request.form.get("monto","")
        cat   = request.form.get("categoria","")
        desc  = request.form.get("descripcion","")
        fecha = request.form.get("fecha", str(date.today()))
        if monto and cat:
            conn = get_db()
            conn.execute("INSERT INTO gastos (usuario_id,monto,categoria,descripcion,fecha) VALUES (?,?,?,?,?)",
                         (uid, float(monto), cat, desc, fecha))
            conn.commit()
            conn.close()
            msg = "✅ Gasto registrado correctamente."
        else:
            msg = "⚠️ Completa todos los campos requeridos."

    conn = get_db()
    lista_gas = conn.execute("SELECT * FROM gastos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    conn.close()
    filas = "".join([f"""<tr>
        <td>{r['fecha']}</td><td>{r['categoria']}</td><td>{r['descripcion'] or '—'}</td>
        <td style="color:var(--red);font-weight:600">-{cop(r['monto'])}</td>
      </tr>""" for r in lista_gas])

    opts = "".join([f'<option value="{c}">{c}</option>' for c in CATEGORIAS_GAS])
    html = BASE_STYLE + """<div class="layout">""" + sidebar("gas") + f"""
    <div class="main">
      <div class="page-title">Registrar Gasto</div>
      <div class="page-sub">Controla tus egresos en pesos colombianos y evita fugas financieras</div>
      {"<div class='alert alert-success'>" + msg + "</div>" if "✅" in msg else ""}
      {"<div class='alert alert-warning'>" + msg + "</div>" if "⚠️" in msg else ""}
      <div class="card" style="max-width:600px;margin-bottom:24px">
        <form method="POST">
          <div class="form-grid">
            <div class="form-group">
              <label>Monto (COP) *</label>
              <input type="number" name="monto" step="1" min="1" placeholder="Ej: 150000" required>
            </div>
            <div class="form-group">
              <label>Categoría *</label>
              <select name="categoria" required><option value="">Seleccionar...</option>{opts}</select>
            </div>
            <div class="form-group">
              <label>Descripción</label>
              <input type="text" name="descripcion" placeholder="Descripción opcional">
            </div>
            <div class="form-group">
              <label>Fecha</label>
              <input type="date" name="fecha" value="{date.today()}">
            </div>
          </div>
          <button class="btn mt16" type="submit">Registrar Gasto</button>
        </form>
      </div>
      <div class="card">
        <div class="section-title">Mis Gastos</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Fecha</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
            <tbody>
              {filas if filas else "<tr><td colspan='4' style='text-align:center;color:var(--muted);padding:24px'>No hay gastos registrados aún.</td></tr>"}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

@app.route("/historial")
def historial():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    conn = get_db()
    ingresos = conn.execute("SELECT *,'ingreso' as tipo FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    gastos   = conn.execute("SELECT *,'gasto'   as tipo FROM gastos   WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
    conn.close()

    rows_ing = ""
    for r in ingresos:
        rows_ing += f"""<tr>
          <td>{r['fecha']}</td>
          <td><span class="badge badge-green">Ingreso</span></td>
          <td>{r['categoria']}</td>
          <td>{r['descripcion'] or '—'}</td>
          <td style="color:var(--green);font-weight:600">+{cop(r['monto'])}</td>
        </tr>"""
    rows_gas = ""
    for r in gastos:
        rows_gas += f"""<tr>
          <td>{r['fecha']}</td>
          <td><span class="badge badge-red">Gasto</span></td>
          <td>{r['categoria']}</td>
          <td>{r['descripcion'] or '—'}</td>
          <td style="color:var(--red);font-weight:600">-{cop(r['monto'])}</td>
        </tr>"""

    html = BASE_STYLE + """<div class="layout">""" + sidebar("his") + f"""
    <div class="main">
      <div class="page-title">Historial Financiero</div>
      <div class="page-sub">Registro completo de movimientos en COP</div>
      <div class="card">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Fecha</th><th>Tipo</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
            <tbody>
              {rows_ing}
              {rows_gas}
              {"<tr><td colspan='5' style='text-align:center;color:var(--muted);padding:24px'>No hay transacciones registradas aún.</td></tr>" if not ingresos and not gastos else ""}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

@app.route("/metas", methods=["GET","POST"])
def metas():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    msg = ""
    if request.method == "POST":
        accion = request.form.get("accion","")
        if accion == "crear":
            nombre  = request.form.get("nombre","").strip()
            obj     = request.form.get("monto_objetivo","")
            actual  = request.form.get("monto_actual","0") or "0"
            if nombre and obj:
                conn = get_db()
                conn.execute("INSERT INTO metas (usuario_id,nombre,monto_objetivo,monto_actual) VALUES (?,?,?,?)",
                             (uid, nombre, float(obj), float(actual)))
                conn.commit()
                conn.close()
                msg = "✅ Meta creada exitosamente."
        elif accion == "abonar":
            meta_id = request.form.get("meta_id","")
            abono   = request.form.get("abono","")
            if meta_id and abono:
                conn = get_db()
                conn.execute("UPDATE metas SET monto_actual = monto_actual + ? WHERE id=? AND usuario_id=?",
                             (float(abono), int(meta_id), uid))
                conn.commit()
                conn.close()
                msg = "✅ Abono registrado correctamente."

    conn = get_db()
    lista = conn.execute("SELECT * FROM metas WHERE usuario_id=?", (uid,)).fetchall()
    conn.close()

    metas_cards = ""
    for mt in lista:
        pct = min(100, (mt["monto_actual"] / mt["monto_objetivo"] * 100)) if mt["monto_objetivo"] > 0 else 0
        faltante = max(0, mt["monto_objetivo"] - mt["monto_actual"])
        bar_color = "var(--green)" if pct >= 100 else "linear-gradient(90deg,var(--accent),var(--accent2))"
        metas_cards += f"""
        <div class="card" style="margin-bottom:16px">
          <div class="flex-between" style="margin-bottom:12px">
            <div>
              <div style="font-size:16px;font-weight:700">{mt['nombre']}</div>
              <div style="font-size:13px;color:var(--muted)">Objetivo: {cop(mt['monto_objetivo'])}</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:20px;font-weight:800;color:var(--accent)">{cop(mt['monto_actual'])}</div>
              <div style="font-size:12px;color:var(--muted)">ahorrado</div>
            </div>
          </div>
          <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
          <div class="flex-between" style="margin-top:8px">
            <span style="font-size:12px;color:var(--muted)">{pct:.0f}% completado</span>
            <span style="font-size:12px;color:var(--muted)">Falta: {cop(faltante)}</span>
          </div>
          <form method="POST" style="display:flex;gap:10px;margin-top:14px">
            <input type="hidden" name="accion" value="abonar">
            <input type="hidden" name="meta_id" value="{mt['id']}">
            <input type="number" name="abono" step="1" min="1" placeholder="Abonar monto (COP)" style="flex:1">
            <button class="btn btn-sm" type="submit">Abonar</button>
          </form>
        </div>"""

    html = BASE_STYLE + """<div class="layout">""" + sidebar("met") + f"""
    <div class="main">
      <div class="page-title">Metas de Ahorro</div>
      <div class="page-sub">Define y alcanza tus objetivos financieros en pesos colombianos</div>
      {"<div class='alert alert-success'>" + msg + "</div>" if msg else ""}
      <div class="two-col">
        <div>
          <div class="card" style="margin-bottom:20px">
            <div class="section-title">Nueva Meta</div>
            <form method="POST">
              <input type="hidden" name="accion" value="crear">
              <div class="form-group" style="margin-bottom:12px">
                <label>Nombre de la meta</label>
                <input type="text" name="nombre" placeholder="Ej: Viaje, Laptop, Fondo de emergencia">
              </div>
              <div class="form-group" style="margin-bottom:12px">
                <label>Monto objetivo (COP)</label>
                <input type="number" name="monto_objetivo" step="1" min="1" placeholder="Ej: 5000000">
              </div>
              <div class="form-group" style="margin-bottom:16px">
                <label>Ahorro inicial (COP)</label>
                <input type="number" name="monto_actual" step="1" min="0" placeholder="Ej: 0">
              </div>
              <button class="btn" type="submit">Crear Meta</button>
            </form>
          </div>
        </div>
        <div>
          {metas_cards if metas_cards else '<div class="card"><div style="color:var(--muted);text-align:center;padding:24px">Aún no tienes metas. ¡Crea la primera!</div></div>'}
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

@app.route("/diagnostico")
def diagnostico():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    ingresos, gastos, metas = get_financial_data(uid)
    m = calcular_metricas(ingresos, gastos)
    hormiga_g, total_hormiga = detectar_hormiga(gastos)
    recs = generar_recomendaciones(m, gastos, metas)
    cat_dict = gastos_por_categoria(gastos)

    score_color = "#10b981" if m["score"] >= 80 else "#3b82f6" if m["score"] >= 60 else "#f59e0b" if m["score"] >= 40 else "#ef4444"
    circum      = 2 * 3.14159 * 40
    dash_offset = circum * (1 - m["score"] / 100)

    cat_html = ""
    if cat_dict:
        total = sum(cat_dict.values()) or 1
        sorted_cat = sorted(cat_dict.items(), key=lambda x: -x[1])
        for cat_n, val in sorted_cat:
            pct = val / total * 100
            cat_html += f"""
            <div style="margin-bottom:14px">
              <div class="flex-between">
                <span style="font-size:14px">{cat_n}</span>
                <span style="font-size:14px;font-weight:600;color:var(--red)">{cop(val)} ({pct:.0f}%)</span>
              </div>
              <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:var(--red)"></div></div>
            </div>"""

    recs_html = "".join([f'<div class="alert alert-info" style="margin-bottom:8px">{r}</div>' for r in recs])
    hormiga_block = ""
    if hormiga_g:
        h_rows = "".join([f"<tr><td>{g['fecha']}</td><td>{g['categoria']}</td><td>{g['descripcion'] or '—'}</td><td style='color:var(--red)'>-{cop(g['monto'])}</td></tr>" for g in hormiga_g[:10]])
        hormiga_block = f"""
        <div class="card mt24">
          <div class="section-title">🐜 Gastos Hormiga Detectados</div>
          <div class="alert alert-warning" style="margin-bottom:16px">Se detectaron <strong>{len(hormiga_g)} gastos hormiga</strong> por un total de <strong>{cop(total_hormiga)}</strong>. Pequeñas compras frecuentes (tinto, snacks, domicilios) que sumadas representan una fuga importante.</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Fecha</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
              <tbody>{h_rows}</tbody>
            </table>
          </div>
        </div>"""

    html = BASE_STYLE + """<div class="layout">""" + sidebar("dia") + f"""
    <div class="main">
      <div class="page-title">Diagnóstico Financiero</div>
      <div class="page-sub">Análisis completo de tu situación económica en Colombia</div>

      <div class="two-col">
        <div class="card" style="text-align:center">
          <div class="section-title" style="text-align:left">Score Financiero</div>
          <div class="score-ring">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" stroke-width="8"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="{score_color}" stroke-width="8"
                stroke-dasharray="{circum:.2f}" stroke-dashoffset="{dash_offset:.2f}" stroke-linecap="round"/>
            </svg>
            <div class="score-text">
              <div class="score-num" style="color:{score_color}">{m['score']}</div>
              <div class="score-cls">/ 100</div>
            </div>
          </div>
          <div style="font-size:22px;font-weight:800;margin-bottom:4px">{m['clasificacion']}</div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:20px">Clasificación financiera</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:left">
            <div style="background:var(--bg3);border-radius:10px;padding:12px">
              <div style="font-size:11px;color:var(--muted)">INGRESOS</div>
              <div style="font-size:18px;font-weight:700;color:var(--green)">{cop(m['total_ingresos'])}</div>
            </div>
            <div style="background:var(--bg3);border-radius:10px;padding:12px">
              <div style="font-size:11px;color:var(--muted)">GASTOS</div>
              <div style="font-size:18px;font-weight:700;color:var(--red)">{cop(m['total_gastos'])}</div>
            </div>
            <div style="background:var(--bg3);border-radius:10px;padding:12px">
              <div style="font-size:11px;color:var(--muted)">AHORRO</div>
              <div style="font-size:18px;font-weight:700;color:{'var(--green)' if m['ahorro']>=0 else 'var(--red)'}">{cop(m['ahorro'])}</div>
            </div>
            <div style="background:var(--bg3);border-radius:10px;padding:12px">
              <div style="font-size:11px;color:var(--muted)">% GASTO</div>
              <div style="font-size:18px;font-weight:700;color:var(--yellow)">{m['pct_gasto']}%</div>
            </div>
          </div>
        </div>

        <div>
          <div class="card" style="margin-bottom:16px">
            <div class="section-title">Recomendaciones Personalizadas</div>
            {recs_html}
          </div>
          <div class="card">
            <div class="section-title">Gastos por Categoría</div>
            {cat_html if cat_html else '<div style="color:var(--muted);font-size:14px">Sin gastos registrados aún.</div>'}
          </div>
        </div>
      </div>

      {hormiga_block}
    </div></div>"""
    return render_template_string(html)

@app.route("/chatbot")
def chatbot():
    if "uid" not in session:
        return redirect(url_for("login"))
    html = BASE_STYLE + """<div class="layout">""" + sidebar("cha") + """
    <div class="main">
      <div class="page-title">Chatbot FinAI 🤖</div>
      <div class="page-sub">Asistente de inteligencia financiera colombiana — consulta sobre tus finanzas en tiempo real</div>
      <div class="card" style="max-width:700px">
        <div class="chat-box">
          <div class="chat-messages" id="chat-messages">
            <div class="msg msg-bot">¡Hola! Soy FinAI, tu asistente financiero inteligente para Colombia 🇨🇴. Puedes preguntarme sobre tus gastos, ingresos, metas de ahorro, CDT o pedir recomendaciones. ¿En qué te ayudo?</div>
          </div>
          <div class="chat-input-row">
            <input type="text" id="chat-input" placeholder="Escribe tu pregunta... Ej: ¿Estoy gastando mucho?" onkeydown="if(event.key==='Enter')sendMsg()">
            <button class="btn" onclick="sendMsg()">Enviar</button>
          </div>
        </div>
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border)">
          <div style="font-size:12px;color:var(--muted);margin-bottom:8px">Preguntas rápidas:</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Estoy gastando mucho?')">¿Estoy gastando mucho?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Cómo está mi situación financiera?')">Mi situación financiera</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Cuál es mi gasto más alto?')">Mayor gasto</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Tengo gastos hormiga?')">Gastos hormiga</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Cómo puedo ahorrar más?')">¿Cómo ahorrar más?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Qué es un CDT?')">¿Qué es un CDT?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 12px" onclick="ask('¿Cómo van mis metas?')">Mis metas</button>
          </div>
        </div>
      </div>
    </div></div>
    <script>
    function ask(q){ document.getElementById('chat-input').value=q; sendMsg(); }
    async function sendMsg(){
      const input = document.getElementById('chat-input');
      const q = input.value.trim();
      if(!q) return;
      const box = document.getElementById('chat-messages');
      box.innerHTML += `<div class="msg msg-user">${q}</div>`;
      input.value = '';
      box.scrollTop = box.scrollHeight;
      const typingId = 'typing-' + Date.now();
      box.innerHTML += `<div class="msg msg-bot" id="${typingId}">...</div>`;
      box.scrollTop = box.scrollHeight;
      try {
        const res = await fetch('/chatbot/ask', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({pregunta: q})
        });
        const data = await res.json();
        document.getElementById(typingId).textContent = data.respuesta;
      } catch(e) {
        document.getElementById(typingId).textContent = 'Error al conectar con el servidor.';
      }
      box.scrollTop = box.scrollHeight;
    }
    </script>
    """
    return render_template_string(html)

@app.route("/chatbot/ask", methods=["POST"])
def chatbot_ask():
    if "uid" not in session:
        return jsonify({"respuesta": "Sesión expirada. Por favor inicia sesión."}), 401
    data = request.get_json()
    pregunta = data.get("pregunta","")
    respuesta = chatbot_responder(pregunta, session["uid"])
    return jsonify({"respuesta": respuesta})

@app.route("/graficas")
def graficas():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    ingresos, gastos, metas = get_financial_data(uid)
    m = calcular_metricas(ingresos, gastos)
    cat_dict = gastos_por_categoria(gastos)

    ing_mes = defaultdict(float)
    gas_mes = defaultdict(float)
    for i in ingresos:
        mes = i["fecha"][:7]
        ing_mes[mes] += i["monto"]
    for g in gastos:
        mes = g["fecha"][:7]
        gas_mes[mes] += g["monto"]
    meses = sorted(set(list(ing_mes.keys()) + list(gas_mes.keys())))
    ing_vals = [ing_mes.get(m2, 0) for m2 in meses]
    gas_vals = [gas_mes.get(m2, 0) for m2 in meses]

    cat_labels = list(cat_dict.keys())
    cat_vals   = list(cat_dict.values())

    meta_nombres  = [mt["nombre"] for mt in metas]
    meta_actuales = [mt["monto_actual"] for mt in metas]
    meta_faltantes = [max(0, mt["monto_objetivo"] - mt["monto_actual"]) for mt in metas]

    import json
    meses_j      = json.dumps(meses)
    ing_vals_j   = json.dumps(ing_vals)
    gas_vals_j   = json.dumps(gas_vals)
    cat_labels_j = json.dumps(cat_labels)
    cat_vals_j   = json.dumps(cat_vals)
    meta_nomb_j  = json.dumps(meta_nombres)
    meta_act_j   = json.dumps(meta_actuales)
    meta_fal_j   = json.dumps(meta_faltantes)

    html = BASE_STYLE + """<div class="layout">""" + sidebar("gra") + f"""
    <div class="main">
      <div class="page-title">Gráficas Financieras</div>
      <div class="page-sub">Visualiza tus finanzas en pesos colombianos de manera intuitiva</div>

      <div class="cards-grid" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-label">Total Ingresos</div>
          <div class="stat-value green">{cop(m['total_ingresos'])}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Gastos</div>
          <div class="stat-value red">{cop(m['total_gastos'])}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Ahorro</div>
          <div class="stat-value {'green' if m['ahorro']>=0 else 'red'}">{cop(m['ahorro'])}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Score</div>
          <div class="stat-value blue">{m['score']}/100</div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card" style="grid-column:1/-1">
          <div class="chart-title">📊 Ingresos vs Gastos por Mes (COP)</div>
          <canvas id="barChart" height="90"></canvas>
        </div>
        <div class="chart-card">
          <div class="chart-title">🍩 Gastos por Categoría</div>
          <canvas id="doughnutChart"></canvas>
        </div>
        <div class="chart-card">
          <div class="chart-title">🎯 Progreso de Metas</div>
          <canvas id="metasChart"></canvas>
        </div>
      </div>
    </div></div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    Chart.defaults.color = '#64748b';
    Chart.defaults.borderColor = '#1e2d45';

    function formatCOP(valor) {{
      return '$ ' + Math.round(valor).toLocaleString('es-CO');
    }}

    new Chart(document.getElementById('barChart'), {{
      type:'bar',
      data:{{
        labels: {meses_j},
        datasets:[
          {{ label:'Ingresos', data:{ing_vals_j}, backgroundColor:'rgba(16,185,129,.7)', borderRadius:6 }},
          {{ label:'Gastos',   data:{gas_vals_j}, backgroundColor:'rgba(239,68,68,.7)',  borderRadius:6 }}
        ]
      }},
      options:{{ responsive:true,
        plugins:{{
          legend:{{ labels:{{ color:'#e2e8f0' }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.dataset.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }},
        scales:{{
          x:{{ ticks:{{ color:'#64748b' }} }},
          y:{{ ticks:{{ color:'#64748b', callback: function(v) {{ return formatCOP(v); }} }} }}
        }} }}
    }});

    new Chart(document.getElementById('doughnutChart'), {{
      type:'doughnut',
      data:{{
        labels: {cat_labels_j},
        datasets:[{{ data:{cat_vals_j},
          backgroundColor:['#3b82f6','#ef4444','#10b981','#f59e0b','#6366f1','#ec4899','#14b8a6','#f97316','#8b5cf6','#06b6d4'],
          borderWidth:0, hoverOffset:8
        }}]
      }},
      options:{{ responsive:true,
        plugins:{{
          legend:{{ position:'bottom', labels:{{ color:'#e2e8f0', padding:12 }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }} }}
    }});

    new Chart(document.getElementById('metasChart'), {{
      type:'bar',
      data:{{
        labels: {meta_nomb_j},
        datasets:[
          {{ label:'Ahorrado',  data:{meta_act_j}, backgroundColor:'rgba(59,130,246,.7)', borderRadius:6 }},
          {{ label:'Faltante',  data:{meta_fal_j}, backgroundColor:'rgba(100,116,139,.3)', borderRadius:6 }}
        ]
      }},
      options:{{
        indexAxis:'y', responsive:true,
        plugins:{{
          legend:{{ labels:{{ color:'#e2e8f0' }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.dataset.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }},
        scales:{{
          x:{{ stacked:true, ticks:{{ color:'#64748b', callback: function(v) {{ return formatCOP(v); }} }} }},
          y:{{ stacked:true, ticks:{{ color:'#64748b' }} }}
        }}
      }}
    }});
    </script>
    """
    return render_template_string(html)

# ─── PWA: MANIFEST, SERVICE WORKER E ICONOS ─────────────────────────────────
import base64
from flask import Response

@app.route("/manifest.json")
def manifest():
    data = {
        "name": "FinAI - Educación Financiera",
        "short_name": "FinAI",
        "description": "Plataforma de educación financiera para Colombia",
        "start_url": "/dashboard",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0a0e1a",
        "theme_color": "#0a0e1a",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }
    import json
    return Response(json.dumps(data), mimetype="application/manifest+json")

@app.route("/icon-192.png")
def icon_192():
    return Response(base64.b64decode(ICON_192_B64), mimetype="image/png")

@app.route("/icon-512.png")
def icon_512():
    return Response(base64.b64decode(ICON_512_B64), mimetype="image/png")

@app.route("/service-worker.js")
def service_worker():
    sw = """
const CACHE_NAME = 'finai-cache-v1';
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { self.clients.claim(); });
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
"""
    return Response(sw, mimetype="application/javascript")

if __name__ == "__main__":
    print("\n" + "═"*50)
    print("  🚀  FinAI  —  Plataforma de Educación Financiera (COP)")
    print("  🌐  http://127.0.0.1:5000")
    print("═"*50 + "\n")
    app.run(debug=True, port=5000)

