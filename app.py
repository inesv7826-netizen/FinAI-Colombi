from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_file, Response
import sqlite3
import hashlib
import os
import pandas as pd
from io import BytesIO
from datetime import datetime, date
from collections import defaultdict
import json
import base64

# ─── GEMINI IA ──────────────────────────────────────────────────────────────
try:
    from google import genai as genai_client
    from dotenv import load_dotenv

    load_dotenv(override=True)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if GEMINI_API_KEY and GEMINI_API_KEY != "tu_api_key_aqui" and GEMINI_API_KEY.strip():
        gemini_client = genai_client.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini configurado correctamente")
    else:
        print("⚠️ No se encontró API Key de Gemini - usando chatbot simple")
        GEMINI_API_KEY = None
        gemini_client = None
except ImportError:
    print("⚠️ google-genai no instalado - usando chatbot simple")
    GEMINI_API_KEY = None
    gemini_client = None

# ─── ICONOS ──────────────────────────────────────────────────────────────────
ICON_512_B64 = "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"
ICON_192_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAAEk0lEQVR4nO3dMW8cRRgG4L2TJURHRUmFLVJSEAqawA8gcUyHbVqggYIWCmqEsIOoKKEDhERLCYljCjociYiCBkRFCkBUpkAYByyC/M7OzGWeR1uf1/u9nvm+3bvz4qk3f53gvNam4+PW58AKW7Y+AVabABERICJri9ZnwEqzAhFZmwxhBKxARASIiCaaiBWIiAARESAixngimnwitjAiAkREgIgIEBFNNBFjPBFbGJG11ifwX756Z731KfTiiVe/bX0KZ1tceuOX1udwl0OhuZeLPYWplwDJzTn0kKTGAZKbIhomqWUTLT2lNLySi0uvN1iBDvdEZxYXX6m9FC0X01T5kJ75HO6t1y7o0xVXoJuiU8uTtZaiej2Q9NRU7WpXCpD01FfnmtcIkPS0UuHKz95ES09bN2duq5fT8TTfcSA9HTjYW5+vxDNuYQf70tOL+Wrh7RxE5gqQ5ac3M1VkuZiOix/S06eD/fXitbaFESkfoBv7G8Vfk1KKV6fwGC89/buxv7EaYzwj8LmwERUseskV6Po1+9dqKFgpWxgRASJS7Gm8/Wu1XL+2UaTuPhs/sBKlt4URESAiZQL05bsaoNVTpGpuJA4tr74tjIgpbGxx9a1ARASIiCZ6aJpoGhMgIl1/S+u5Pfjwhcd2P2t9Fnf58eC9H754u/VZlGeMH1tcfU300DTRNCZARASIiAAR0UQPLae+XJ8Hk9bSlgAR0QMNzY1EGrs/H6aez+8/f//N+8+0PosVYwUiYowfW4mn8RI0rrz6tjAiAkREgIgIEBF3oofmaTwZT+NpS4CICBARTfTQSjTR/OWBhx55/LXbxV/2zu3Pv/v0xeIv2wlbGBFj/NiM8bSliR6a90TTmAARESAieqCheRpPxhhPWwJERICIaKL/NuBHm91IpDFT2NhMYbQlQEQ00UPTRNOYABERICLG+LH5f2EkNNE0JkBEBIiIABHxNb9Dy6tvjB+bp/G0JUBE3EgcmhuJNCZARASIiDF+bJ7Gk9BE05gAEREgIgJERBM9NN9Qdrbffjr6+q1HW5/FKvA0nrYEiIgAEdFED82daBoTICL35xjP/2WMpy1N9NB6aaKffeFWkdehpiJVs4URESAieqBxFSn9cjqeihyXd7VBq+Ty7q0idbeFEREgIiUDZBdbFQUrpYkeUcGi28KIFJvC/jyu7NjFendlp8z8NdcUJkM9K14dWxiR5WI6Ln5s7hy1/r04w+bOUfFaz7UCyVBvZqqILYzIjAGyCPVjvloUHuP/cWxuy1B7m9tH85V4uZimWY+rMtTU1e2jWetboweSoVYqXPlKTbQM1VfnmtebwmSopmpXe7H98p06P+nEJx9cqPwTh1L5D3X2Jvrfx5alaDZbM7fMZxw7L9VegU58/KGlqJit59v8Wba8E93qd77/NLySLVeg06xG59DDX+Bit48AnfhIku7luQ5yc6K7AJ0mTCe6Cs1pXQeI/nk7BxHfUEbE58KI2MKICBARASIiQEQ00USM8URsYUQEiIgAEdFEE7ECEREgIsZ4IlYgIppoIlYgIgJERICI/AHN91ChUPk65QAAAABJRU5ErkJggg=="

app = Flask(__name__)
app.secret_key = "finai_secret_key_2024"
DB_NAME = "finai.db"

# ─── UTILIDADES ─────────────────────────────────────────────────────────────

def cop(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        valor = 0
    return "$ {:,.0f}".format(valor).replace(",", ".")

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
HORMIGA_MONTO_MAX  = 25000

def detectar_hormiga(gastos):
    pequeños = [g for g in gastos if g["monto"] <= HORMIGA_MONTO_MAX and g["categoria"].lower() in HORMIGA_CATEGORIAS]
    total_hormiga = sum(g["monto"] for g in pequeños)
    return pequeños, total_hormiga

def generar_recomendaciones(metricas, gastos, metas):
    recs = []
    pct_gas = metricas["pct_gasto"]
    pct_aho = metricas["pct_ahorro"]

    if pct_gas > 90:
        recs.append("⚠️ Tus gastos superan el 90% de tus ingresos. Reduce gastos no esenciales.")
    elif pct_gas > 70:
        recs.append("📉 Tus gastos son mayores al 70% de tus ingresos. Considera recortar gastos variables.")
    if pct_aho < 10 and metricas["total_ingresos"] > 0:
        recs.append("💰 Tu tasa de ahorro es menor al 10%. Intenta ahorrar al menos el 20%.")
    if metricas["ahorro"] < 0:
        recs.append("🚨 Estás gastando más de lo que ganas. Revisa tus finanzas urgentemente.")
    if not recs:
        recs.append("✅ ¡Tu situación financiera es saludable! Mantén tus hábitos.")
    return recs

def gastos_por_categoria(gastos):
    cat = defaultdict(float)
    for g in gastos:
        cat[g["categoria"]] += g["monto"]
    return dict(cat)

# ─── CHATBOT ─────────────────────────────────────────────────────────────────

def chatbot_simple(pregunta, uid):
    ingresos, gastos, metas = get_financial_data(uid)
    metricas = calcular_metricas(ingresos, gastos)
    recs = generar_recomendaciones(metricas, gastos, metas)
    p = pregunta.lower()

    if "gasto" in p:
        return f"Tus gastos son {cop(metricas['total_gastos'])} ({metricas['pct_gasto']}% de ingresos)."
    if "ahorro" in p:
        return f"Tu ahorro es {cop(metricas['ahorro'])} ({metricas['pct_ahorro']}% de ingresos)."
    if "situación" in p or "financiera" in p:
        return f"Tu salud financiera es {metricas['clasificacion']} (score {metricas['score']}/100)."
    return f"Tu score es {metricas['score']}/100. " + recs[0]

def chatbot_gemini(pregunta, uid):
    if not GEMINI_API_KEY or gemini_client is None:
        return chatbot_simple(pregunta, uid)
    try:
        ingresos, gastos, metas = get_financial_data(uid)
        metricas = calcular_metricas(ingresos, gastos)
        contexto = f"Ingresos: {cop(metricas['total_ingresos'])}, Gastos: {cop(metricas['total_gastos'])}, Ahorro: {cop(metricas['ahorro'])}, Score: {metricas['score']}/100"
        prompt = f"Eres asesor financiero en Colombia. Contexto: {contexto}. Pregunta: {pregunta}"
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return chatbot_simple(pregunta, uid)

def chatbot_responder(pregunta, uid):
    if GEMINI_API_KEY and gemini_client is not None:
        try:
            return chatbot_gemini(pregunta, uid)
        except:
            return chatbot_simple(pregunta, uid)
    return chatbot_simple(pregunta, uid)

# ─── EXPORTACIÓN ──────────────────────────────────────────────────────────────

@app.route("/exportar/excel")
def exportar_excel():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    
    try:
        conn = get_db()
        ingresos = conn.execute("SELECT * FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
        gastos = conn.execute("SELECT * FROM gastos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
        metas = conn.execute("SELECT * FROM metas WHERE usuario_id=?", (uid,)).fetchall()
        conn.close()
        
        df_ingresos = pd.DataFrame(ingresos) if ingresos else pd.DataFrame(columns=['id', 'usuario_id', 'monto', 'categoria', 'descripcion', 'fecha'])
        df_gastos = pd.DataFrame(gastos) if gastos else pd.DataFrame(columns=['id', 'usuario_id', 'monto', 'categoria', 'descripcion', 'fecha'])
        df_metas = pd.DataFrame(metas) if metas else pd.DataFrame(columns=['id', 'usuario_id', 'nombre', 'monto_objetivo', 'monto_actual'])
        
        for df in [df_ingresos, df_gastos, df_metas]:
            if 'id' in df.columns:
                df.drop('id', axis=1, inplace=True)
            if 'usuario_id' in df.columns:
                df.drop('usuario_id', axis=1, inplace=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_ingresos.to_excel(writer, sheet_name='Ingresos', index=False)
            df_gastos.to_excel(writer, sheet_name='Gastos', index=False)
            df_metas.to_excel(writer, sheet_name='Metas', index=False)
            
            total_ing = sum(i["monto"] for i in ingresos)
            total_gas = sum(g["monto"] for g in gastos)
            resumen = pd.DataFrame({
                'Metrica': ['Total Ingresos', 'Total Gastos', 'Ahorro Neto', 'Fecha Exportación'],
                'Valor': [
                    f"${total_ing:,.0f}",
                    f"${total_gas:,.0f}",
                    f"${total_ing - total_gas:,.0f}",
                    date.today().strftime('%Y-%m-%d')
                ]
            })
            resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'financiero_{date.today()}.xlsx'
        )
    except Exception as e:
        return f"<h1>Error al exportar Excel: {str(e)}</h1>", 500

@app.route("/exportar/pdf")
def exportar_pdf():
    if "uid" not in session:
        return redirect(url_for("login"))
    uid = session["uid"]
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        conn = get_db()
        ingresos = conn.execute("SELECT * FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
        gastos = conn.execute("SELECT * FROM gastos WHERE usuario_id=? ORDER BY fecha DESC", (uid,)).fetchall()
        metas = conn.execute("SELECT * FROM metas WHERE usuario_id=?", (uid,)).fetchall()
        conn.close()
        
        total_ing = sum(i["monto"] for i in ingresos)
        total_gas = sum(g["monto"] for g in gastos)
        ahorro = total_ing - total_gas
        pct_gasto = (total_gas / total_ing * 100) if total_ing > 0 else 0
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            spaceAfter=30
        )
        
        elements = []
        elements.append(Paragraph("✦ Resumen Financiero - FinAI", title_style))
        elements.append(Paragraph(f"Fecha: {date.today().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Paragraph(f"Usuario: {session.get('nombre', '')}", styles['Heading2']))
        elements.append(Spacer(1, 0.3*inch))
        
        data = [
            ['Métrica', 'Valor'],
            ['Total Ingresos', f"${total_ing:,.0f}"],
            ['Total Gastos', f"${total_gas:,.0f}"],
            ['Ahorro Neto', f"${ahorro:,.0f}"],
            ['% Gasto / Ingreso', f"{pct_gasto:.1f}%"],
            ['Total Transacciones', f"{len(ingresos) + len(gastos)}"],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        if gastos:
            elements.append(Paragraph("Top Gastos por Categoría:", styles['Heading2']))
            cat_dict = {}
            for g in gastos:
                cat_dict[g["categoria"]] = cat_dict.get(g["categoria"], 0) + g["monto"]
            
            data_cat = [['Categoría', 'Monto']]
            for cat, monto in sorted(cat_dict.items(), key=lambda x: -x[1])[:5]:
                data_cat.append([cat, f"${monto:,.0f}"])
            
            table_cat = Table(data_cat, colWidths=[3*inch, 2*inch])
            table_cat.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34d399')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table_cat)
            elements.append(Spacer(1, 0.3*inch))
        
        if metas:
            elements.append(Paragraph("Progreso de Metas:", styles['Heading2']))
            data_metas = [['Meta', 'Objetivo', 'Ahorrado', 'Progreso']]
            for m in metas:
                pct = (m["monto_actual"] / m["monto_objetivo"] * 100) if m["monto_objetivo"] > 0 else 0
                data_metas.append([
                    m['nombre'],
                    f"${m['monto_objetivo']:,.0f}",
                    f"${m['monto_actual']:,.0f}",
                    f"{pct:.0f}%"
                ])
            
            table_metas = Table(data_metas, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table_metas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbbf24')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table_metas)
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Reporte generado por FinAI - Tu asistente financiero en Colombia", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'financiero_{date.today()}.pdf'
        )
    except Exception as e:
        return f"<h1>Error al exportar PDF: {str(e)}</h1>", 500

# ─── TEMPLATES ───────────────────────────────────────────────────────────────

PWA_HEAD_TAGS = """
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0f1724">
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap');

:root {
    --bg-primary: #0f1724;
    --bg-secondary: #161f32;
    --bg-card: #1a2538;
    --bg-card-hover: #1f2d44;
    --bg-input: #0d1520;
    
    --border-light: rgba(255, 255, 255, 0.06);
    --border-glow: rgba(99, 102, 241, 0.15);
    
    --text-primary: #edf2f7;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --accent-1: #6366f1;
    --accent-2: #8b5cf6;
    --accent-3: #3b82f6;
    --gradient-primary: linear-gradient(135deg, #6366f1, #8b5cf6);
    --gradient-secondary: linear-gradient(135deg, #3b82f6, #6366f1);
    
    --green: #34d399;
    --green-dark: #059669;
    --red: #f87171;
    --red-dark: #dc2626;
    --yellow: #fbbf24;
    --orange: #fb923c;
    
    --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
    --shadow-glow: 0 0 40px rgba(99, 102, 241, 0.1);
    
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 28px;
    
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}
::-webkit-scrollbar-thumb {
    background: var(--accent-1);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--accent-2);
}

.layout {
    display: flex;
    min-height: 100vh;
}

/* ─── SIDEBAR ─────────────────────────────────────────────────── */
.sidebar {
    width: 260px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-light);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 100;
    backdrop-filter: blur(20px);
    transition: var(--transition);
}

.sidebar-logo {
    padding: 28px 24px 20px;
    border-bottom: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    gap: 14px;
}

.logo-icon {
    width: 44px;
    height: 44px;
    background: var(--gradient-primary);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 800;
    color: #fff;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 26px;
    font-weight: 900;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

.logo-sub {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: -4px;
}

.nav {
    padding: 20px 14px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.nav-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    padding: 12px 14px 6px;
    font-weight: 600;
}

.nav a {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 12px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: var(--transition);
    position: relative;
}

.nav a:hover {
    background: rgba(99, 102, 241, 0.08);
    color: var(--text-primary);
}

.nav a.active {
    background: rgba(99, 102, 241, 0.12);
    color: #fff;
    box-shadow: inset 3px 0 0 var(--accent-1);
}

.nav a.active .nav-icon {
    color: var(--accent-1);
}

.nav-icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
    flex-shrink: 0;
}

.nav-badge {
    margin-left: auto;
    background: var(--accent-1);
    color: #fff;
    font-size: 10px;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 600;
}

.sidebar-footer {
    padding: 16px 14px;
    border-top: 1px solid var(--border-light);
}

.sidebar-footer a {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 12px;
    color: var(--red);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: var(--transition);
}

.sidebar-footer a:hover {
    background: rgba(248, 113, 113, 0.1);
}

/* ─── MAIN CONTENT ────────────────────────────────────────────────────── */
.main {
    margin-left: 260px;
    flex: 1;
    padding: 32px 40px;
    min-height: 100vh;
}

.page-header {
    margin-bottom: 32px;
}

.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: var(--gradient-secondary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.page-title-light {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
}

.page-sub {
    color: var(--text-secondary);
    font-size: 15px;
    margin-top: 4px;
    font-weight: 400;
}

/* ─── CARDS ────────────────────────────────────────────────────────────── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 24px;
    transition: var(--transition);
    box-shadow: var(--shadow-card);
}

.card:hover {
    border-color: var(--border-glow);
    box-shadow: var(--shadow-glow), var(--shadow-card);
}

/* ─── STAT CARDS ──────────────────────────────────────────────────────── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 22px 24px;
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: var(--transition);
}

.stat-card:hover::before {
    opacity: 1;
}

.stat-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-2px);
}

.stat-label {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

.stat-value.green { color: var(--green); }
.stat-value.red { color: var(--red); }
.stat-value.yellow { color: var(--yellow); }
.stat-value.blue { color: var(--accent-3); }
.stat-value.purple { color: var(--accent-2); }

.stat-sub {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 6px;
}

/* ─── SCORE RING ──────────────────────────────────────────────────────── */
.score-ring {
    position: relative;
    width: 120px;
    height: 120px;
    margin: 0 auto 16px;
}

.score-ring svg {
    transform: rotate(-90deg);
}

.score-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
}

.score-num {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}

.score-cls {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ─── FORMULARIOS ────────────────────────────────────────────────────── */
.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.form-group label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
}

.form-group .required {
    color: var(--red);
    margin-left: 2px;
}

input, select, textarea {
    background: var(--bg-input);
    border: 1px solid var(--border-light);
    color: var(--text-primary);
    border-radius: var(--radius-sm);
    padding: 11px 16px;
    font-size: 14px;
    font-family: inherit;
    transition: var(--transition);
    outline: none;
}

input:focus, select:focus, textarea:focus {
    border-color: var(--accent-1);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

input::placeholder, textarea::placeholder {
    color: var(--text-muted);
}

select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;
    cursor: pointer;
}

select option {
    background: var(--bg-secondary);
}

textarea {
    resize: vertical;
    min-height: 80px;
}

/* ─── BOTONES ──────────────────────────────────────────────────────────── */
.btn {
    background: var(--gradient-primary);
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    padding: 11px 28px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition);
    font-family: inherit;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
}

.btn:active {
    transform: scale(0.97);
}

.btn-sm {
    padding: 8px 18px;
    font-size: 13px;
}

.btn-outline {
    background: transparent;
    border: 1px solid var(--border-light);
    color: var(--text-secondary);
    border-radius: var(--radius-sm);
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
    font-family: inherit;
}

.btn-outline:hover {
    border-color: var(--accent-1);
    color: var(--text-primary);
    background: rgba(99, 102, 241, 0.05);
}

.btn-success {
    background: linear-gradient(135deg, var(--green-dark), #10b981);
}
.btn-success:hover {
    box-shadow: 0 8px 30px rgba(16, 185, 129, 0.3);
}

.btn-danger {
    background: linear-gradient(135deg, var(--red-dark), #ef4444);
}
.btn-danger:hover {
    box-shadow: 0 8px 30px rgba(239, 68, 68, 0.3);
}

/* ─── ALERTAS ──────────────────────────────────────────────────────────── */
.alert {
    border-radius: var(--radius-sm);
    padding: 14px 20px;
    font-size: 14px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.alert-warning {
    background: rgba(251, 191, 36, 0.08);
    border: 1px solid rgba(251, 191, 36, 0.2);
    color: var(--yellow);
}

.alert-danger {
    background: rgba(248, 113, 113, 0.08);
    border: 1px solid rgba(248, 113, 113, 0.2);
    color: var(--red);
}

.alert-success {
    background: rgba(52, 211, 153, 0.08);
    border: 1px solid rgba(52, 211, 153, 0.2);
    color: var(--green);
}

.alert-info {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: var(--accent-3);
}

/* ─── TABLAS ───────────────────────────────────────────────────────────── */
.table-wrap {
    overflow-x: auto;
    border-radius: var(--radius-sm);
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

thead {
    background: rgba(255, 255, 255, 0.02);
}

th {
    text-align: left;
    padding: 12px 16px;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid var(--border-light);
}

td {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    color: var(--text-secondary);
}

tr:last-child td {
    border-bottom: none;
}

tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

/* ─── BADGES ───────────────────────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: capitalize;
}

.badge-green {
    background: rgba(52, 211, 153, 0.12);
    color: var(--green);
}
.badge-red {
    background: rgba(248, 113, 113, 0.12);
    color: var(--red);
}
.badge-blue {
    background: rgba(99, 102, 241, 0.12);
    color: var(--accent-3);
}
.badge-yellow {
    background: rgba(251, 191, 36, 0.12);
    color: var(--yellow);
}
.badge-purple {
    background: rgba(139, 92, 246, 0.12);
    color: var(--accent-2);
}

/* ─── PROGRESS BAR ────────────────────────────────────────────────────── */
.progress-bar {
    height: 6px;
    background: var(--bg-input);
    border-radius: 10px;
    overflow: hidden;
    margin-top: 8px;
}

.progress-fill {
    height: 100%;
    background: var(--gradient-primary);
    border-radius: 10px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ─── CHAT ────────────────────────────────────────────────────────────── */
.chat-box {
    display: flex;
    flex-direction: column;
    height: 420px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.msg {
    max-width: 80%;
    padding: 12px 18px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.6;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.msg-user {
    background: var(--gradient-primary);
    color: #fff;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}

.msg-bot {
    background: var(--bg-input);
    color: var(--text-primary);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    border: 1px solid var(--border-light);
}

.chat-input-row {
    display: flex;
    gap: 10px;
    padding: 16px;
    border-top: 1px solid var(--border-light);
}

.chat-input-row input {
    flex: 1;
}

/* ─── LAYOUT UTILITIES ────────────────────────────────────────────────── */
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}

.mt16 { margin-top: 16px; }
.mt24 { margin-top: 24px; }
.mb16 { margin-bottom: 16px; }
.mb24 { margin-bottom: 24px; }

.section-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 16px;
    color: var(--text-primary);
}

.section-title .highlight {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ─── AUTH ────────────────────────────────────────────────────────────── */
.auth-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.08) 0%, var(--bg-primary) 70%);
    padding: 20px;
}

.auth-card {
    width: 420px;
    max-width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 44px 40px;
    box-shadow: var(--shadow-card), var(--shadow-glow);
    backdrop-filter: blur(10px);
}

.auth-logo {
    text-align: center;
    margin-bottom: 32px;
}

.auth-logo .logo-icon {
    width: 56px;
    height: 56px;
    font-size: 26px;
    margin: 0 auto 12px;
}

.auth-logo h1 {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 900;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.auth-logo p {
    color: var(--text-secondary);
    font-size: 14px;
    margin-top: 4px;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.auth-form .btn {
    width: 100%;
    padding: 13px;
    font-size: 15px;
    justify-content: center;
}

.auth-link {
    text-align: center;
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 20px;
}

.auth-link a {
    color: var(--accent-1);
    text-decoration: none;
    font-weight: 600;
    transition: var(--transition);
}

.auth-link a:hover {
    color: var(--accent-2);
}

.error-msg {
    background: rgba(248, 113, 113, 0.08);
    border: 1px solid rgba(248, 113, 113, 0.2);
    color: var(--red);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    font-size: 13px;
    margin-bottom: 16px;
}

/* ─── CHARTS ───────────────────────────────────────────────────────────── */
.charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 24px;
}

.chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 20px;
    transition: var(--transition);
}

.chart-card:hover {
    border-color: var(--border-glow);
}

.chart-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
}

/* ─── RESPONSIVE ───────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
    .two-col {
        grid-template-columns: 1fr;
    }
    .charts-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .sidebar {
        width: 72px;
    }
    .sidebar-logo .logo-text,
    .sidebar-logo .logo-sub,
    .nav a span,
    .nav-label,
    .sidebar-footer a span,
    .nav-badge {
        display: none;
    }
    .sidebar-logo {
        padding: 16px 12px;
        justify-content: center;
    }
    .logo-icon {
        width: 40px;
        height: 40px;
        font-size: 18px;
    }
    .nav {
        padding: 12px 8px;
    }
    .nav a {
        justify-content: center;
        padding: 12px;
        border-radius: 12px;
    }
    .nav-icon {
        font-size: 20px;
        width: auto;
    }
    .sidebar-footer a {
        justify-content: center;
        padding: 12px;
    }
    .sidebar-footer a span {
        display: none;
    }
    .main {
        margin-left: 72px;
        padding: 20px 16px;
    }
    .cards-grid {
        grid-template-columns: 1fr 1fr;
    }
    .page-title {
        font-size: 24px;
    }
    .auth-card {
        padding: 32px 24px;
    }
}

@media (max-width: 480px) {
    .cards-grid {
        grid-template-columns: 1fr;
    }
    .stat-value {
        font-size: 22px;
    }
    .main {
        padding: 16px 12px;
    }
    .form-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""

# ─── SIDEBAR ────────────────────────────────────────────────────────────────

SIDEBAR_TEMPLATE = """
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">✦</div>
    <div>
      <div class="logo-text">FinAI</div>
      <div class="logo-sub">Inteligencia Financiera</div>
    </div>
  </div>
  <nav class="nav">
    <div class="nav-label">Principal</div>
    <a href="/dashboard" class="{a_dash}"><span class="nav-icon">📊</span><span>Dashboard</span></a>
    <a href="/ingresos" class="{a_ing}"><span class="nav-icon">💵</span><span>Ingresos</span></a>
    <a href="/gastos" class="{a_gas}"><span class="nav-icon">💳</span><span>Gastos</span></a>
    <a href="/historial" class="{a_his}"><span class="nav-icon">📋</span><span>Historial</span></a>
    
    <div class="nav-label" style="margin-top:12px;">Planificación</div>
    <a href="/metas" class="{a_met}"><span class="nav-icon">🎯</span><span>Metas</span></a>
    <a href="/diagnostico" class="{a_dia}"><span class="nav-icon">🩺</span><span>Diagnóstico</span></a>
    
    <div class="nav-label" style="margin-top:12px;">Herramientas</div>
    <a href="/chatbot" class="{a_cha}"><span class="nav-icon">🤖</span><span>Chatbot IA</span><span class="nav-badge">Gemini</span></a>
    <a href="/graficas" class="{a_gra}"><span class="nav-icon">📈</span><span>Gráficas</span></a>
    <a href="/scroll-animation" class="{a_scroll}"><span class="nav-icon">✨</span><span>Scroll Animado</span></a>
    <a href="/scroll-demo" class="{a_scroll_demo}"><span class="nav-icon">🎬</span><span>Scroll Demo</span></a>
  </nav>
  <div class="sidebar-footer">
    <a href="/logout"><span class="nav-icon">🚪</span><span>Cerrar sesión</span></a>
  </div>
</div>
"""

def sidebar(active=""):
    keys = ["dash","ing","gas","his","met","dia","cha","gra","scroll","scroll_demo"]
    d = {f"a_{k}": ("active" if k == active else "") for k in keys}
    return SIDEBAR_TEMPLATE.format(**d)

# ─── RUTAS PRINCIPALES ──────────────────────────────────────────────────────

@app.route("/")
def index():
    if "uid" in session:
        return redirect(url_for("dashboard"))
    
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinAI - Inteligencia Financiera</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0f1724;
            color: #edf2f7;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .landing {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 20px;
            background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.06) 0%, #0f1724 70%);
            position: relative;
        }
        
        .landing::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.03) 0%, transparent 70%);
            animation: pulse 8s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.2); opacity: 1; }
        }
        
        .landing-content {
            position: relative;
            z-index: 1;
            max-width: 900px;
        }
        
        .badge-top {
            display: inline-block;
            background: rgba(99, 102, 241, 0.12);
            color: #a5b4fc;
            padding: 6px 20px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 24px;
            border: 1px solid rgba(99, 102, 241, 0.15);
            letter-spacing: 0.5px;
        }
        
        .logo-large {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 42px;
            font-weight: 900;
            color: white;
            margin: 0 auto 24px;
            box-shadow: 0 20px 60px rgba(99, 102, 241, 0.25);
            animation: float 4s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-12px); }
        }
        
        .landing-title {
            font-family: 'Playfair Display', serif;
            font-size: clamp(3rem, 10vw, 6rem);
            font-weight: 900;
            letter-spacing: -2px;
            line-height: 1.05;
            margin-bottom: 16px;
        }
        
        .landing-title .gradient {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% 200%;
            animation: gradientShift 5s ease-in-out infinite;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .landing-sub {
            color: #94a3b8;
            font-size: 1.15rem;
            max-width: 560px;
            margin: 0 auto 32px;
            line-height: 1.8;
        }
        
        .landing-buttons {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .btn-primary {
            padding: 15px 38px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 14px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.25);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.35);
        }
        
        .btn-secondary {
            padding: 15px 38px;
            background: rgba(255,255,255,0.04);
            color: #e2e8f0;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.15);
            transform: translateY(-3px);
        }
        
        .features-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            max-width: 800px;
            margin: 56px auto 0;
            width: 100%;
        }
        
        .feature-mini {
            background: rgba(26, 37, 56, 0.6);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px 20px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .feature-mini:hover {
            border-color: rgba(99, 102, 241, 0.15);
            transform: translateY(-4px);
            background: rgba(26, 37, 56, 0.8);
        }
        
        .feature-mini .icon {
            font-size: 2rem;
            margin-bottom: 12px;
        }
        
        .feature-mini h4 {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .feature-mini p {
            color: #94a3b8;
            font-size: 0.85rem;
            line-height: 1.5;
        }
        
        @media (max-width: 768px) {
            .features-row {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        @media (max-width: 480px) {
            .features-row {
                grid-template-columns: 1fr;
            }
            .landing-buttons {
                flex-direction: column;
                align-items: center;
            }
            .btn-primary, .btn-secondary {
                width: 100%;
                max-width: 280px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="landing">
        <div class="landing-content">
            <div class="badge-top">✦ Potenciado por Google Gemini</div>
            <div class="logo-large">✦</div>
            <h1 class="landing-title">
                Fin<span class="gradient">AI</span>
            </h1>
            <p class="landing-sub">
                Tu asistente financiero con inteligencia artificial avanzada.<br>
                Controla tus finanzas, establece metas y recibe asesoría personalizada.
            </p>
            <div class="landing-buttons">
                <a href="/login" class="btn-primary">Iniciar sesión</a>
                <a href="/registro" class="btn-secondary">Crear cuenta</a>
            </div>
            
            <div class="features-row">
                <div class="feature-mini">
                    <div class="icon">📊</div>
                    <h4>Dashboard</h4>
                    <p>Visualiza tus finanzas al instante</p>
                </div>
                <div class="feature-mini">
                    <div class="icon">🤖</div>
                    <h4>IA Gemini</h4>
                    <p>Asesoramiento inteligente</p>
                </div>
                <div class="feature-mini">
                    <div class="icon">🎯</div>
                    <h4>Metas</h4>
                    <p>Alcanza tus objetivos</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(html)

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
          <div class="logo-icon">✦</div>
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
        <div class="auth-link">
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
          <div class="logo-icon">✦</div>
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
        <div class="auth-link">
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

# ─── RUTAS PRINCIPALES DEL DASHBOARD ──────────────────────────────────────

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
    circum     = 2 * 3.14159 * 45
    dash_offset = circum * (1 - score / 100)
    score_color = "#34d399" if score >= 80 else "#6366f1" if score >= 60 else "#fbbf24" if score >= 40 else "#f87171"

    metas_html = ""
    for mt in metas:
        pct = min(100, (mt["monto_actual"] / mt["monto_objetivo"] * 100)) if mt["monto_objetivo"] > 0 else 0
        metas_html += f"""
        <div style="margin-bottom:16px">
          <div class="flex-between">
            <span style="font-size:14px;font-weight:600">{mt['nombre']}</span>
            <span style="font-size:13px;color:var(--text-muted)">{cop(mt['monto_actual'])} / {cop(mt['monto_objetivo'])}</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%"></div></div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px">{pct:.0f}% completado</div>
        </div>"""

    recs_html = "".join([f'<div class="alert alert-info" style="margin-bottom:8px;padding:10px 14px">{r}</div>' for r in recs])
    hormiga_alert = f'<div class="alert alert-warning">🐜 Se detectaron <strong>{len(hormiga_g)} gastos hormiga</strong> por un total de <strong>{cop(total_hormiga)}</strong>. ¡Cuidado con los pequeños gastos frecuentes!</div>' if hormiga_g else ""

    ahorro_cls = "green" if m["ahorro"] >= 0 else "red"

    html = BASE_STYLE + """
    <div class="layout">
    """ + sidebar("dash") + f"""
    <div class="main">
      <div class="flex-between" style="margin-bottom:8px">
        <div class="page-header">
          <div class="page-title">Dashboard</div>
          <div class="page-sub">Bienvenido, {session['nombre']} · {date.today().strftime('%d %b %Y')}</div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <a href="/exportar/excel" class="btn btn-success btn-sm" style="text-decoration:none;">
            📊 Exportar Excel
          </a>
          <a href="/exportar/pdf" class="btn btn-danger btn-sm" style="text-decoration:none;">
            📄 Exportar PDF
          </a>
        </div>
      </div>

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
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
              <circle cx="60" cy="60" r="45" fill="none" stroke="{score_color}" stroke-width="8"
                stroke-dasharray="{circum:.2f}" stroke-dashoffset="{dash_offset:.2f}"
                stroke-linecap="round"/>
            </svg>
            <div class="score-text">
              <div class="score-num" style="color:{score_color}">{score}</div>
              <div class="score-cls">/ 100</div>
            </div>
          </div>
          <div style="font-size:20px;font-weight:700;margin-bottom:4px">{m['clasificacion']}</div>
          <div style="font-size:13px;color:var(--text-muted)">Puntuación financiera</div>
        </div>
        <div class="card">
          <div class="section-title">Recomendaciones IA</div>
          {recs_html}
        </div>
      </div>

      <div class="card mt24">
        <div class="section-title">Progreso de Metas</div>
        {metas_html if metas_html else '<div style="color:var(--text-muted);font-size:14px">No tienes metas registradas. <a href="/metas" style="color:var(--accent-1)">Crear meta →</a></div>'}
      </div>
    </div>
    </div>
    """
    return render_template_string(html)

# ─── RUTAS DE INGRESOS ─────────────────────────────────────────────────────

CATEGORIAS_ING = ["Salario","Freelance","Negocio propio","Inversiones","Arriendo recibido","Regalo","Otro"]

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
        <td>{r['fecha']}</td><td><span class="badge badge-green">{r['categoria']}</span></td><td>{r['descripcion'] or '—'}</td>
        <td style="color:var(--green);font-weight:600">+{cop(r['monto'])}</td>
      </tr>""" for r in lista_ing])

    opts = "".join([f'<option value="{c}">{c}</option>' for c in CATEGORIAS_ING])
    html = BASE_STYLE + """<div class="layout">""" + sidebar("ing") + f"""
    <div class="main">
      <div class="page-header">
        <div class="page-title">Registrar Ingreso</div>
        <div class="page-sub">Agrega una nueva fuente de ingreso (COP)</div>
      </div>
      {"<div class='alert alert-success'>" + msg + "</div>" if "✅" in msg else ""}
      {"<div class='alert alert-warning'>" + msg + "</div>" if "⚠️" in msg else ""}
      <div class="card" style="max-width:600px;margin-bottom:24px">
        <form method="POST">
          <div class="form-grid">
            <div class="form-group">
              <label>Monto <span class="required">*</span></label>
              <input type="number" name="monto" step="1" min="1" placeholder="Ej: 2500000" required>
            </div>
            <div class="form-group">
              <label>Categoría <span class="required">*</span></label>
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
              {filas if filas else "<tr><td colspan='4' style='text-align:center;color:var(--text-muted);padding:32px'>No hay ingresos registrados aún.</td></tr>"}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

# ─── RUTAS DE GASTOS ──────────────────────────────────────────────────────

CATEGORIAS_GAS = ["Vivienda","Alimentación","Transporte","Servicios públicos","Salud","Educación","Entretenimiento","Ropa","Deudas/Créditos","Suscripciones","Café","Domicilios","Dulces","Bebidas","Snacks","Comida rápida","Otros"]

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
        <td>{r['fecha']}</td><td><span class="badge badge-red">{r['categoria']}</span></td><td>{r['descripcion'] or '—'}</td>
        <td style="color:var(--red);font-weight:600">-{cop(r['monto'])}</td>
      </tr>""" for r in lista_gas])

    opts = "".join([f'<option value="{c}">{c}</option>' for c in CATEGORIAS_GAS])
    html = BASE_STYLE + """<div class="layout">""" + sidebar("gas") + f"""
    <div class="main">
      <div class="page-header">
        <div class="page-title">Registrar Gasto</div>
        <div class="page-sub">Controla tus egresos y evita fugas financieras</div>
      </div>
      {"<div class='alert alert-success'>" + msg + "</div>" if "✅" in msg else ""}
      {"<div class='alert alert-warning'>" + msg + "</div>" if "⚠️" in msg else ""}
      <div class="card" style="max-width:600px;margin-bottom:24px">
        <form method="POST">
          <div class="form-grid">
            <div class="form-group">
              <label>Monto <span class="required">*</span></label>
              <input type="number" name="monto" step="1" min="1" placeholder="Ej: 150000" required>
            </div>
            <div class="form-group">
              <label>Categoría <span class="required">*</span></label>
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
              {filas if filas else "<tr><td colspan='4' style='text-align:center;color:var(--text-muted);padding:32px'>No hay gastos registrados aún.</td></tr>"}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

# ─── RUTA HISTORIAL ────────────────────────────────────────────────────────

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
      <div class="flex-between" style="margin-bottom:8px">
        <div class="page-header">
          <div class="page-title">Historial Financiero</div>
          <div class="page-sub">Registro completo de movimientos en COP</div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <a href="/exportar/excel" class="btn btn-success btn-sm" style="text-decoration:none;">📊 Excel</a>
          <a href="/exportar/pdf" class="btn btn-danger btn-sm" style="text-decoration:none;">📄 PDF</a>
        </div>
      </div>
      <div class="card">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Fecha</th><th>Tipo</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
            <tbody>
              {rows_ing}
              {rows_gas}
              {"<tr><td colspan='5' style='text-align:center;color:var(--text-muted);padding:32px'>No hay transacciones registradas aún.</td></tr>" if not ingresos and not gastos else ""}
            </tbody>
          </table>
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

# ─── RUTA METAS ────────────────────────────────────────────────────────────

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
        bar_color = "var(--green)" if pct >= 100 else "var(--gradient-primary)"
        metas_cards += f"""
        <div class="card" style="margin-bottom:16px">
          <div class="flex-between" style="margin-bottom:12px">
            <div>
              <div style="font-size:16px;font-weight:700">{mt['nombre']}</div>
              <div style="font-size:13px;color:var(--text-muted)">Objetivo: {cop(mt['monto_objetivo'])}</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:20px;font-weight:800;color:var(--accent-3)">{cop(mt['monto_actual'])}</div>
              <div style="font-size:12px;color:var(--text-muted)">ahorrado</div>
            </div>
          </div>
          <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
          <div class="flex-between" style="margin-top:8px">
            <span style="font-size:12px;color:var(--text-muted)">{pct:.0f}% completado</span>
            <span style="font-size:12px;color:var(--text-muted)">Falta: {cop(faltante)}</span>
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
      <div class="page-header">
        <div class="page-title">Metas de Ahorro</div>
        <div class="page-sub">Define y alcanza tus objetivos financieros en COP</div>
      </div>
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
          {metas_cards if metas_cards else '<div class="card"><div style="color:var(--text-muted);text-align:center;padding:32px">Aún no tienes metas. ¡Crea la primera!</div></div>'}
        </div>
      </div>
    </div></div>"""
    return render_template_string(html)

# ─── RUTA DIAGNÓSTICO ─────────────────────────────────────────────────────

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

    score_color = "#34d399" if m["score"] >= 80 else "#6366f1" if m["score"] >= 60 else "#fbbf24" if m["score"] >= 40 else "#f87171"
    circum      = 2 * 3.14159 * 45
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
          <div class="alert alert-warning" style="margin-bottom:16px">Se detectaron <strong>{len(hormiga_g)} gastos hormiga</strong> por un total de <strong>{cop(total_hormiga)}</strong>. Pequeñas compras frecuentes que sumadas representan una fuga importante.</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Fecha</th><th>Categoría</th><th>Descripción</th><th>Monto</th></tr></thead>
              <tbody>{h_rows}</tbody>
            </table>
          </div>
        </div>"""

    html = BASE_STYLE + """<div class="layout">""" + sidebar("dia") + f"""
    <div class="main">
      <div class="page-header">
        <div class="page-title">Diagnóstico Financiero</div>
        <div class="page-sub">Análisis completo de tu situación económica</div>
      </div>

      <div class="two-col">
        <div class="card" style="text-align:center">
          <div class="section-title" style="text-align:left">Score Financiero</div>
          <div class="score-ring">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
              <circle cx="60" cy="60" r="45" fill="none" stroke="{score_color}" stroke-width="8"
                stroke-dasharray="{circum:.2f}" stroke-dashoffset="{dash_offset:.2f}" stroke-linecap="round"/>
            </svg>
            <div class="score-text">
              <div class="score-num" style="color:{score_color}">{m['score']}</div>
              <div class="score-cls">/ 100</div>
            </div>
          </div>
          <div style="font-size:22px;font-weight:800;margin-bottom:4px">{m['clasificacion']}</div>
          <div style="font-size:13px;color:var(--text-muted);margin-bottom:20px">Clasificación financiera</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:left">
            <div style="background:var(--bg-input);border-radius:10px;padding:14px">
              <div style="font-size:11px;color:var(--text-muted)">INGRESOS</div>
              <div style="font-size:18px;font-weight:700;color:var(--green)">{cop(m['total_ingresos'])}</div>
            </div>
            <div style="background:var(--bg-input);border-radius:10px;padding:14px">
              <div style="font-size:11px;color:var(--text-muted)">GASTOS</div>
              <div style="font-size:18px;font-weight:700;color:var(--red)">{cop(m['total_gastos'])}</div>
            </div>
            <div style="background:var(--bg-input);border-radius:10px;padding:14px">
              <div style="font-size:11px;color:var(--text-muted)">AHORRO</div>
              <div style="font-size:18px;font-weight:700;color:{'var(--green)' if m['ahorro']>=0 else 'var(--red)'}">{cop(m['ahorro'])}</div>
            </div>
            <div style="background:var(--bg-input);border-radius:10px;padding:14px">
              <div style="font-size:11px;color:var(--text-muted)">% GASTO</div>
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
            {cat_html if cat_html else '<div style="color:var(--text-muted);font-size:14px">Sin gastos registrados aún.</div>'}
          </div>
        </div>
      </div>

      {hormiga_block}
    </div></div>"""
    return render_template_string(html)

# ─── RUTA CHATBOT ─────────────────────────────────────────────────────────

@app.route("/chatbot")
def chatbot():
    if "uid" not in session:
        return redirect(url_for("login"))
    html = BASE_STYLE + """<div class="layout">""" + sidebar("cha") + """
    <div class="main">
      <div class="page-header">
        <div class="page-title">Chatbot <span style="background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">FinAI</span></div>
        <div class="page-sub">Asistente financiero impulsado por IA de Google (Gemini)</div>
      </div>
      <div class="card" style="max-width:720px">
        <div class="chat-box">
          <div class="chat-messages" id="chat-messages">
            <div class="msg msg-bot">✨ ¡Hola! Soy <strong>FinAI</strong>, tu asistente financiero impulsado por IA de Google. Puedes preguntarme sobre tus finanzas, ahorro, inversiones y más. ¿En qué te ayudo?</div>
          </div>
          <div class="chat-input-row">
            <input type="text" id="chat-input" placeholder="Escribe tu pregunta..." onkeydown="if(event.key==='Enter')sendMsg()">
            <button class="btn" onclick="sendMsg()">Enviar</button>
          </div>
        </div>
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-light)">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">Preguntas rápidas:</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Estoy gastando mucho?')">¿Estoy gastando mucho?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Cómo está mi situación financiera?')">Mi situación</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Cuál es mi gasto más alto?')">Mayor gasto</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Tengo gastos hormiga?')">Gastos hormiga</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Cómo puedo ahorrar más?')">¿Cómo ahorrar más?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Qué es un CDT?')">¿Qué es un CDT?</button>
            <button class="btn-outline" style="font-size:12px;padding:6px 14px" onclick="ask('¿Cómo van mis metas?')">Mis metas</button>
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
      box.innerHTML += `<div class="msg msg-bot" id="${typingId}">...🤔</div>`;
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

# ─── RUTA GRÁFICAS ────────────────────────────────────────────────────────

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
      <div class="page-header">
        <div class="page-title">Gráficas Financieras</div>
        <div class="page-sub">Visualiza tus finanzas de manera intuitiva</div>
      </div>

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
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';

    function formatCOP(valor) {{
      return '$ ' + Math.round(valor).toLocaleString('es-CO');
    }}

    new Chart(document.getElementById('barChart'), {{
      type:'bar',
      data:{{
        labels: {meses_j},
        datasets:[
          {{ label:'Ingresos', data:{ing_vals_j}, backgroundColor:'rgba(52,211,153,.7)', borderRadius:6 }},
          {{ label:'Gastos',   data:{gas_vals_j}, backgroundColor:'rgba(248,113,113,.7)',  borderRadius:6 }}
        ]
      }},
      options:{{ responsive:true,
        plugins:{{
          legend:{{ labels:{{ color:'#edf2f7' }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.dataset.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }},
        scales:{{
          x:{{ ticks:{{ color:'#94a3b8' }} }},
          y:{{ ticks:{{ color:'#94a3b8', callback: function(v) {{ return formatCOP(v); }} }} }}
        }} }}
    }});

    new Chart(document.getElementById('doughnutChart'), {{
      type:'doughnut',
      data:{{
        labels: {cat_labels_j},
        datasets:[{{ data:{cat_vals_j},
          backgroundColor:['#6366f1','#f87171','#34d399','#fbbf24','#a78bfa','#f472b6','#34d399','#fb923c','#8b5cf6','#22d3ee'],
          borderWidth:0, hoverOffset:8
        }}]
      }},
      options:{{ responsive:true,
        plugins:{{
          legend:{{ position:'bottom', labels:{{ color:'#edf2f7', padding:12 }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }} }}
    }});

    new Chart(document.getElementById('metasChart'), {{
      type:'bar',
      data:{{
        labels: {meta_nomb_j},
        datasets:[
          {{ label:'Ahorrado',  data:{meta_act_j}, backgroundColor:'rgba(99,102,241,.7)', borderRadius:6 }},
          {{ label:'Faltante',  data:{meta_fal_j}, backgroundColor:'rgba(148,163,184,.2)', borderRadius:6 }}
        ]
      }},
      options:{{
        indexAxis:'y', responsive:true,
        plugins:{{
          legend:{{ labels:{{ color:'#edf2f7' }} }},
          tooltip:{{ callbacks:{{ label: function(ctx) {{ return ctx.dataset.label + ': ' + formatCOP(ctx.raw); }} }} }}
        }},
        scales:{{
          x:{{ stacked:true, ticks:{{ color:'#94a3b8', callback: function(v) {{ return formatCOP(v); }} }} }},
          y:{{ stacked:true, ticks:{{ color:'#94a3b8' }} }}
        }}
      }}
    }});
    </script>
    """
    return render_template_string(html)

# ─── RUTA SCROLL ANIMADO (NUEVA) ──────────────────────────────────────────

@app.route("/scroll-animation")
def scroll_animation():
    """Página con animación de scroll estilo ContainerScroll"""
    if "uid" not in session:
        return redirect(url_for("login"))
    
    # Obtener datos financieros reales del usuario
    uid = session["uid"]
    ingresos, gastos, metas = get_financial_data(uid)
    m = calcular_metricas(ingresos, gastos)
    
    html = BASE_STYLE + """
<div class="layout">
""" + sidebar("scroll") + """
<div class="main" style="padding: 0; overflow: hidden;">
    <!-- SECCIÓN HERO -->
    <section class="scroll-hero">
        <div class="scroll-hero-content">
            <span class="badge-top">✦ FinAI Premium</span>
            <h1 class="scroll-hero-title">
                Visualiza tu <br>
                <span class="gradient-text">Progreso Financiero</span>
            </h1>
            <p class="scroll-hero-sub">
                Desplázate hacia abajo para ver cómo tus finanzas cobran vida
                con animaciones inmersivas.
            </p>
            <div class="scroll-indicator">
                <span>↓</span>
            </div>
        </div>
    </section>

    <!-- SECCIÓN DE ANIMACIÓN SCROLL -->
    <section class="scroll-section" id="scrollSection">
        <div class="scroll-container" id="scrollContainer">
            <!-- Header animado -->
            <div class="scroll-header" id="scrollHeader">
                <span class="badge-top" style="margin-bottom: 16px;">🎯 Tu Progreso</span>
                <h2 class="scroll-header-title">
                    <span class="gradient-text">Metas</span> en Movimiento
                </h2>
                <p class="scroll-header-sub">Cada paso te acerca a tus objetivos financieros</p>
            </div>

            <!-- Tarjeta animada -->
            <div class="scroll-card-wrapper" id="scrollCardWrapper">
                <div class="scroll-card">
                    <div class="scroll-card-inner">
                        <div class="scroll-stats">
                            <div class="scroll-stat">
                                <div class="scroll-stat-icon">💰</div>
                                <div class="scroll-stat-number green" id="scrollIngresos">""" + f"{cop(m['total_ingresos'])}" + """</div>
                                <div class="scroll-stat-label">Ingresos Totales</div>
                            </div>
                            <div class="scroll-stat">
                                <div class="scroll-stat-icon">💳</div>
                                <div class="scroll-stat-number red" id="scrollGastos">""" + f"{cop(m['total_gastos'])}" + """</div>
                                <div class="scroll-stat-label">Gastos Totales</div>
                            </div>
                            <div class="scroll-stat">
                                <div class="scroll-stat-icon">🎯</div>
                                <div class="scroll-stat-number blue" id="scrollAhorro">""" + f"{cop(m['ahorro'])}" + """</div>
                                <div class="scroll-stat-label">Ahorro Neto</div>
                            </div>
                            <div class="scroll-stat">
                                <div class="scroll-stat-icon">📊</div>
                                <div class="scroll-stat-number purple" id="scrollScore">""" + f"{m['score']}/100" + """</div>
                                <div class="scroll-stat-label">Score Financiero</div>
                            </div>
                        </div>
                        
                        <!-- Barra de progreso -->
                        <div class="scroll-progress-container">
                            <div class="scroll-progress-header">
                                <span>Progreso de Meta Principal</span>
                                <span id="scrollProgressPercent">0%</span>
                            </div>
                            <div class="scroll-progress-track">
                                <div class="scroll-progress-fill" id="scrollProgressBar"></div>
                            </div>
                        </div>

                        <!-- Features que aparecen al final -->
                        <div class="scroll-features" id="scrollFeatures">
                            <div class="scroll-feature">
                                <div class="scroll-feature-icon">📈</div>
                                <h3>Dashboard en Vivo</h3>
                                <p>Visualiza tus finanzas en tiempo real</p>
                            </div>
                            <div class="scroll-feature">
                                <div class="scroll-feature-icon">🤖</div>
                                <h3>IA con Gemini</h3>
                                <p>Asesoramiento financiero inteligente</p>
                            </div>
                            <div class="scroll-feature">
                                <div class="scroll-feature-icon">🎯</div>
                                <h3>Metas Personalizadas</h3>
                                <p>Alcanza tus objetivos financieros</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <style>
        /* ─── HERO ──────────────────────────────────────────────────── */
        .scroll-hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            position: relative;
            background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.06) 0%, var(--bg-primary) 70%);
            padding: 40px 20px;
        }

        .scroll-hero-content {
            max-width: 800px;
            position: relative;
            z-index: 1;
        }

        .scroll-hero-title {
            font-family: 'Playfair Display', serif;
            font-size: clamp(2.5rem, 8vw, 5rem);
            font-weight: 900;
            line-height: 1.05;
            letter-spacing: -2px;
            margin-bottom: 20px;
        }

        .scroll-hero-sub {
            color: var(--text-secondary);
            font-size: 1.1rem;
            max-width: 500px;
            margin: 0 auto 40px;
            line-height: 1.7;
        }

        .scroll-indicator {
            animation: bounce 2s ease-in-out infinite;
            font-size: 2rem;
            color: var(--accent-1);
            opacity: 0.5;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(12px); }
        }

        /* ─── SCROLL SECTION ────────────────────────────────────────── */
        .scroll-section {
            min-height: 300vh;
            position: relative;
            background: var(--bg-primary);
            overflow: hidden;
        }

        .scroll-container {
            position: sticky;
            top: 60px;
            perspective: 1200px;
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
            z-index: 10;
        }

        /* ─── HEADER ──────────────────────────────────────────────────── */
        .scroll-header {
            text-align: center;
            margin-bottom: 40px;
            transform: translateY(0);
            opacity: 1;
            transition: none;
        }

        .scroll-header-title {
            font-family: 'Playfair Display', serif;
            font-size: clamp(1.8rem, 4vw, 3rem);
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 8px;
        }

        .scroll-header-sub {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        /* ─── CARD ────────────────────────────────────────────────────── */
        .scroll-card-wrapper {
            transform-style: preserve-3d;
            transition: transform 0.05s linear;
            will-change: transform;
        }

        .scroll-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-xl);
            padding: 20px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            backdrop-filter: blur(20px);
            transform-style: preserve-3d;
            transition: transform 0.05s linear;
            will-change: transform;
        }

        .scroll-card-inner {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 36px 32px;
            min-height: 380px;
        }

        /* ─── STATS ──────────────────────────────────────────────────── */
        .scroll-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .scroll-stat {
            background: rgba(255,255,255,0.03);
            padding: 20px 16px;
            border-radius: var(--radius-md);
            text-align: center;
            border: 1px solid var(--border-light);
            transition: all 0.3s ease;
        }

        .scroll-stat:hover {
            background: rgba(255,255,255,0.06);
            border-color: var(--border-glow);
            transform: translateY(-4px);
        }

        .scroll-stat-icon {
            font-size: 2rem;
            margin-bottom: 6px;
        }

        .scroll-stat-number {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .scroll-stat-number.green { color: var(--green); }
        .scroll-stat-number.red { color: var(--red); }
        .scroll-stat-number.blue { color: var(--accent-3); }
        .scroll-stat-number.purple { color: var(--accent-2); }

        .scroll-stat-label {
            color: var(--text-muted);
            font-size: 0.8rem;
            margin-top: 2px;
        }

        /* ─── PROGRESS BAR ───────────────────────────────────────────── */
        .scroll-progress-container {
            padding: 18px 20px;
            background: rgba(255,255,255,0.02);
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-light);
            margin-bottom: 28px;
        }

        .scroll-progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        .scroll-progress-header span:last-child {
            color: var(--accent-1);
            font-weight: 600;
        }

        .scroll-progress-track {
            width: 100%;
            height: 8px;
            background: var(--bg-input);
            border-radius: 10px;
            overflow: hidden;
        }

        .scroll-progress-fill {
            width: 0%;
            height: 100%;
            background: var(--gradient-primary);
            border-radius: 10px;
            transition: width 0.2s ease;
        }

        /* ─── FEATURES ────────────────────────────────────────────────── */
        .scroll-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }
        .scroll-features.visible {
            opacity: 1;
            transform: translateY(0);
        }

        .scroll-feature {
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-md);
            padding: 20px 16px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .scroll-feature:hover {
            background: rgba(99, 102, 241, 0.04);
            border-color: var(--border-glow);
            transform: translateY(-4px);
        }

        .scroll-feature-icon {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        .scroll-feature h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .scroll-feature p {
            color: var(--text-muted);
            font-size: 0.85rem;
            line-height: 1.5;
        }

        /* ─── RESPONSIVE ─────────────────────────────────────────────── */
        @media (max-width: 768px) {
            .scroll-container {
                top: 40px;
                padding: 10px;
            }
            .scroll-card {
                border-radius: var(--radius-lg);
                padding: 12px;
            }
            .scroll-card-inner {
                padding: 20px 16px;
                min-height: 320px;
            }
            .scroll-stats {
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            .scroll-stat {
                padding: 14px 10px;
            }
            .scroll-stat-number {
                font-size: 1.2rem;
            }
            .scroll-features {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            .scroll-section {
                min-height: 250vh;
            }
        }

        @media (max-width: 480px) {
            .scroll-stats {
                grid-template-columns: 1fr;
            }
            .scroll-card-inner {
                padding: 16px 12px;
                min-height: 280px;
            }
            .scroll-header {
                margin-bottom: 24px;
            }
        }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // ─── ANIMACIÓN DE SCROLL ────────────────────────────────────
        const cardWrapper = document.getElementById('scrollCardWrapper');
        const header = document.getElementById('scrollHeader');
        const progressBar = document.getElementById('scrollProgressBar');
        const progressPercent = document.getElementById('scrollProgressPercent');
        const features = document.getElementById('scrollFeatures');

        const section = document.getElementById('scrollSection');
        const sectionHeight = section.scrollHeight - window.innerHeight;

        function updateScrollAnimation() {
            const scrollTop = window.scrollY;
            const sectionTop = section.offsetTop;
            
            // Calcular el progreso (0 = inicio, 1 = final)
            let progress = (scrollTop - sectionTop) / sectionHeight;
            progress = Math.max(0, Math.min(1, progress));

            // Efecto 3D en la tarjeta
            const rotateX = 20 - (progress * 20);
            const scale = 0.85 + (progress * 0.15);
            const translateY = -80 + (progress * 120);

            cardWrapper.style.transform = 
                `rotateX(${rotateX}deg) scale(${scale})`;

            // Efecto en el header
            header.style.transform = `translateY(${translateY * 0.5}px)`;
            header.style.opacity = 1 - (progress * 0.6);

            // Actualizar barra de progreso
            const pct = Math.round(progress * 100);
            progressBar.style.width = `${pct}%`;
            progressPercent.textContent = `${pct}%`;

            // Mostrar features cuando el progreso es mayor a 25%
            if (progress > 0.25) {
                const featureProgress = (progress - 0.25) / 0.25;
                const opacity = Math.min(1, featureProgress);
                features.style.opacity = opacity;
                features.style.transform = `translateY(${30 - (opacity * 30)}px)`;
                features.classList.add('visible');
            } else {
                features.style.opacity = 0;
                features.style.transform = 'translateY(30px)';
                features.classList.remove('visible');
            }
        }

        // Ejecutar la animación al hacer scroll
        window.addEventListener('scroll', updateScrollAnimation);
        
        // Ejecutar una vez al cargar
        setTimeout(updateScrollAnimation, 100);
    });
    </script>
</div>
</div>
"""
    return render_template_string(html)

# ─── RUTA SCROLL DEMO ──────────────────────────────────────────────────────

@app.route("/scroll-demo")
def scroll_demo():
    """Página de demostración con animación de scroll estilo React"""
    if "uid" not in session:
        return redirect(url_for("login"))
    
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinAI - Scroll Animation</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', sans-serif; 
            background: #0f1724; 
            color: #edf2f7;
            overflow-x: hidden;
        }
        
        .hero-section {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            position: relative;
            background: radial-gradient(ellipse at center, #1a2538 0%, #0f1724 100%);
            padding: 40px 20px;
        }
        
        .hero-content {
            max-width: 900px;
        }
        
        .badge {
            display: inline-block;
            background: rgba(99, 102, 241, 0.12);
            color: #a5b4fc;
            padding: 6px 20px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 24px;
            border: 1px solid rgba(99, 102, 241, 0.15);
        }
        
        .hero-title {
            font-family: 'Playfair Display', serif;
            font-size: clamp(3rem, 10vw, 6.5rem);
            font-weight: 900;
            line-height: 1.05;
            letter-spacing: -2px;
            margin-bottom: 24px;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.2rem;
            max-width: 600px;
            margin: 0 auto 32px;
            line-height: 1.7;
        }
        
        .btn-primary {
            display: inline-block;
            padding: 15px 38px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 14px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.25);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.35);
        }
        
        .scroll-section {
            min-height: 250vh;
            position: relative;
            padding: 80px 20px;
        }
        
        .scroll-container {
            position: sticky;
            top: 80px;
            perspective: 1200px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header-content {
            text-align: center;
            margin-bottom: 40px;
            transform: translateY(0);
            transition: transform 0.1s ease-out;
        }
        
        .header-content h2 {
            font-family: 'Playfair Display', serif;
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 800;
            margin-bottom: 16px;
            letter-spacing: -1px;
        }
        
        .header-content p {
            color: #94a3b8;
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .scroll-card {
            background: rgba(26, 37, 56, 0.95);
            border: 2px solid rgba(255,255,255,0.06);
            border-radius: 30px;
            padding: 20px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.5);
            transform-style: preserve-3d;
            transition: transform 0.05s linear;
            backdrop-filter: blur(20px);
        }
        
        .scroll-card-inner {
            background: #161f32;
            border-radius: 20px;
            padding: 40px;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            width: 100%;
        }
        
        .stat-item {
            background: rgba(255,255,255,0.03);
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            background: rgba(255,255,255,0.06);
            border-color: rgba(99, 102, 241, 0.15);
            transform: translateY(-4px);
        }
        
        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 8px;
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: -1px;
        }
        .stat-number.green { color: #34d399; }
        .stat-number.red { color: #f87171; }
        .stat-number.blue { color: #6366f1; }
        
        .stat-label {
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 4px;
        }
        
        .progress-container {
            margin-top: 32px;
            padding: 20px 24px;
            background: rgba(255,255,255,0.03);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }
        .progress-header span:last-child {
            color: #6366f1;
            font-weight: 600;
        }
        
        .progress-track {
            width: 100%;
            height: 8px;
            background: #0f1724;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 24px;
            margin-top: 48px;
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }
        .features-grid.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .feature-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 28px 24px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            background: rgba(99, 102, 241, 0.04);
            border-color: rgba(99, 102, 241, 0.12);
            transform: translateY(-6px);
        }
        
        .feature-icon {
            font-size: 2.8rem;
            margin-bottom: 16px;
        }
        .feature-card h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .feature-card p {
            color: #94a3b8;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        
        @media (max-width: 768px) {
            .scroll-card {
                border-radius: 20px;
                padding: 12px;
            }
            .scroll-card-inner {
                padding: 20px;
                min-height: 300px;
            }
            .stats-grid {
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }
            .stat-item {
                padding: 16px;
            }
            .stat-number {
                font-size: 1.4rem;
            }
            .features-grid {
                grid-template-columns: 1fr;
            }
            .scroll-section {
                min-height: 200vh;
                padding: 40px 16px;
            }
            .scroll-container {
                top: 40px;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <section class="hero-section">
        <div class="hero-content">
            <div class="badge">✦ FinAI Premium</div>
            <h1 class="hero-title">
                Finanzas <br>
                <span class="gradient-text">Inteligentes</span>
            </h1>
            <p class="hero-subtitle">
                Controla tus finanzas con IA, visualiza tu progreso y alcanza tus metas financieras
                con el poder de Google Gemini.
            </p>
            <a href="/dashboard" class="btn-primary">Comenzar ahora →</a>
        </div>
    </section>

    <section class="scroll-section" id="scrollSection">
        <div class="scroll-container" id="scrollContainer">
            <div class="header-content" id="headerContent">
                <span class="badge">🎯 Progreso Financiero</span>
                <h2>Visualiza tus <span class="gradient-text">Logros</span></h2>
                <p>Desplázate para ver cómo tus finanzas crecen con cada paso</p>
            </div>
            
            <div class="scroll-card" id="scrollCard">
                <div class="scroll-card-inner" id="cardInner">
                    <div style="width: 100%;">
                        <div class="stats-grid">
                            <div class="stat-item">
                                <div class="stat-icon">💰</div>
                                <div class="stat-number green">$2.5M</div>
                                <div class="stat-label">Ingresos Totales</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon">💳</div>
                                <div class="stat-number red">$1.8M</div>
                                <div class="stat-label">Gastos Totales</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon">🎯</div>
                                <div class="stat-number blue">$700K</div>
                                <div class="stat-label">Ahorro Neto</div>
                            </div>
                        </div>
                        
                        <div class="progress-container">
                            <div class="progress-header">
                                <span>Progreso de Meta: Viaje a Europa</span>
                                <span id="progressPercent">0%</span>
                            </div>
                            <div class="progress-track">
                                <div class="progress-fill" id="progressBar"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="features-grid" id="featuresGrid">
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Dashboard en Vivo</h3>
                    <p>Visualiza tus finanzas en tiempo real con gráficos interactivos</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>IA con Gemini</h3>
                    <p>Asesoramiento financiero inteligente de Google</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3>Metas Personalizadas</h3>
                    <p>Define y alcanza tus objetivos financieros</p>
                </div>
            </div>
        </div>
    </section>

    <script>
        gsap.registerPlugin(ScrollTrigger);
        
        gsap.to("#scrollCard", {
            scrollTrigger: {
                trigger: ".scroll-section",
                start: "top top",
                end: "bottom bottom",
                scrub: 1,
                onUpdate: (self) => {
                    const progress = self.progress;
                    const rotateX = 20 - (progress * 20);
                    const scale = 0.85 + (progress * 0.15);
                    const translateY = -50 + (progress * 100);
                    
                    const card = document.getElementById("scrollCard");
                    card.style.transform = `rotateX(${rotateX}deg) scale(${scale})`;
                    
                    const header = document.getElementById("headerContent");
                    header.style.transform = `translateY(${translateY}px)`;
                    header.style.opacity = 0.3 + (progress * 0.7);
                    
                    const progressBar = document.getElementById("progressBar");
                    const progressPercent = document.getElementById("progressPercent");
                    const pct = Math.round(progress * 100);
                    progressBar.style.width = `${pct}%`;
                    progressPercent.textContent = `${pct}%`;
                    
                    const grid = document.getElementById("featuresGrid");
                    if (progress > 0.3) {
                        const opacity = Math.min(1, (progress - 0.3) * 3);
                        grid.style.opacity = opacity;
                        grid.style.transform = `translateY(${30 - (opacity * 30)}px)`;
                        grid.classList.add("visible");
                    }
                }
            }
        });
        
        gsap.from(".feature-card", {
            scrollTrigger: {
                trigger: ".features-grid",
                start: "top bottom-=100",
                toggleActions: "play none none reverse"
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: "power3.out"
        });
        
        gsap.from(".stat-item", {
            scrollTrigger: {
                trigger: ".scroll-card",
                start: "top bottom-=50",
                toggleActions: "play none none reverse"
            },
            scale: 0.8,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: "back.out(1.7)"
        });
    </script>
</body>
</html>
    """
    return render_template_string(html)

# ─── API PARA DATOS FINANCIEROS ────────────────────────────────────────────

@app.route("/api/financial-data")
def api_financial_data():
    """API para obtener datos financieros del usuario en formato JSON"""
    if "uid" not in session:
        return jsonify({"error": "No autorizado"}), 401
    uid = session["uid"]
    ingresos, gastos, metas = get_financial_data(uid)
    m = calcular_metricas(ingresos, gastos)
    return jsonify({
        "total_ingresos": m["total_ingresos"],
        "total_gastos": m["total_gastos"],
        "ahorro": m["ahorro"],
        "score": m["score"],
        "clasificacion": m["clasificacion"],
        "pct_gasto": m["pct_gasto"],
        "pct_ahorro": m["pct_ahorro"]
    })

# ─── PWA: MANIFEST, SERVICE WORKER E ICONOS ─────────────────────────────────

@app.route("/manifest.json")
def manifest():
    data = {
        "name": "FinAI - Inteligencia Financiera con IA",
        "short_name": "FinAI",
        "description": "Plataforma de educación financiera para Colombia con IA",
        "start_url": "/dashboard",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0f1724",
        "theme_color": "#0f1724",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }
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
const CACHE_NAME = 'finai-cache-v2';
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { self.clients.claim(); });
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
"""
    return Response(sw, mimetype="application/javascript")

# ─── INICIALIZAR ─────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    print("\n" + "═"*50)
    print("  ✦  FinAI  —  Inteligencia Financiera (COP)")
    print("  🤖  Chatbot con IA de Google (Gemini)")
    print("  🌐  http://127.0.0.1:5000")
    print("  📱  Página de scroll animado: /scroll-animation")
    print("═"*50 + "\n")
    app.run(debug=True, port=5000)
