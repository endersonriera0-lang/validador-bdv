from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime, timedelta
import re
import requests
import os

app = Flask(__name__)
app.secret_key = 'cila_secreto_super_seguro_2026' 

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
FIREBASE_URL_BASE = "https://validador-bdv-default-rtdb.firebaseio.com"
FIREBASE_PAGOS = f"{FIREBASE_URL_BASE}/pagos.json"
FIREBASE_USUARIOS = f"{FIREBASE_URL_BASE}/usuarios.json"
FIREBASE_CONFIG = f"{FIREBASE_URL_BASE}/config.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sistema Corporativo CILA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>

    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; min-height: 100vh; background-image: url('https://i.imgur.com/rgsa5XH.png'); background-size: cover; background-position: center; background-attachment: fixed; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 40, 80, 0.78); z-index: -2; backdrop-filter: blur(4px); }
        
        /* SIDEBAR (PC) */
        .sidebar { position: fixed; top: 0; left: 0; height: 100vh; width: 240px; background: rgba(0, 15, 30, 0.95); padding-top: 30px; display: flex; flex-direction: column; align-items: center; z-index: 100; border-right: 1px solid rgba(255,255,255,0.1); }
        .sidebar-logo { max-width: 160px; margin-bottom: 40px; }
        .nav-item { display: block; width: 85%; padding: 12px 15px; margin-bottom: 10px; background: rgba(255,255,255,0.05); color: white; text-decoration: none; border-radius: 10px; font-weight: bold; transition: 0.3s; font-size: 0.9em; }
        .nav-item.active { background: #198754; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

        /* HEADER MÓVIL (OCULTO EN PC) */
        .mobile-header { display: none; position: fixed; top: 0; width: 100%; height: 60px; background: rgba(0, 15, 30, 0.95); z-index: 101; align-items: center; justify-content: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .mobile-header img { height: 35px; }

        /* BOTONES DE ACCIÓN */
        .btn-logout { position: fixed; top: 20px; right: 20px; background: #ce1126; color: white; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; z-index: 102; font-size: 0.85em; }
        .fab-cierre { position: fixed; bottom: 30px; right: 25px; background: #ffc107; color: #333; padding: 15px 20px; border-radius: 50px; font-weight: bold; border: 2px solid white; cursor: pointer; box-shadow: 0 8px 20px rgba(0,0,0,0.4); z-index: 100; transition: 0.3s; }

        /* CONTENEDOR PRINCIPAL */
        .main-wrapper { margin-left: 240px; padding: 40px; display: flex; gap: 30px; justify-content: center; align-items: flex-start; }
        .card-panel { background: rgba(255, 255, 255, 0.96); padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); width: 100%; box-sizing: border-box; }
        
        .form-section { flex: 1; max-width: 420px; border-top: 6px solid #198754; }
        .result-section { flex: 1.3; max-width: 600px; }

        .app-footer { position: fixed; bottom: 15px; left: calc(50% + 120px); transform: translateX(-50%); background: rgba(255,255,255,0.1); padding: 5px 20px; border-radius: 20px; color: white; font-size: 0.75em; z-index: 90; }

        /* 📱 RESPONSIVIDAD MÓVIL EXTREMA 📱 */
        @media (max-width: 900px) {
            .sidebar { display: none; } /* Ocultamos sidebar en móvil */
            .mobile-header { display: flex; } /* Mostramos cabecera */
            .main-wrapper { margin-left: 0; padding: 80px 15px 120px 15px; flex-direction: column; }
            .form-section, .result-section { max-width: 100%; }
            .app-footer { left: 50%; bottom: 85px; background: rgba(0,0,0,0.3); }
            .btn-logout { top: 12px; right: 12px; padding: 8px 12px; }

            /* NAVEGACIÓN INFERIOR MÓVIL */
            .mobile-nav { display: flex; position: fixed; bottom: 0; width: 100%; background: #000f1e; height: 70px; z-index: 1000; border-top: 1px solid rgba(255,255,255,0.1); justify-content: space-around; align-items: center; }
            .mobile-nav-item { color: #888; text-decoration: none; font-size: 0.7em; text-align: center; display: flex; flex-direction: column; gap: 4px; }
            .mobile-nav-item.active { color: #198754; }
            .mobile-nav-item i { font-size: 20px; }

            .fab-cierre { bottom: 90px; right: 15px; padding: 12px 18px; font-size: 0.85em; }
        }

        /* Estilos de inputs y botones (Se mantienen para consistencia) */
        .titulo-panel { margin-top: 0; color: #003366; text-align: center; font-size: 1.3em; text-transform: uppercase; letter-spacing: 1px;}
        .form-group { margin-bottom: 15px; }
        .form-label { display: block; font-weight: bold; color: #555; margin-bottom: 5px; font-size: 0.8em; }
        .form-control { width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        .btn-submit { background: #198754; color: white; width: 100%; padding: 16px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 1em; }
        .card { background: white; padding: 20px; border-radius: 12px; border-left: 8px solid #ce1126; animation: slideIn 0.3s; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="overlay"></div>
    <iframe id="iframeTicket" style="display:none;"></iframe>
    <iframe id="iframeCarta" style="display:none;"></iframe>

    {% if session.usuario %}
    <div class="sidebar">
        <img src="https://i.imgur.com/j4gWZ33.png" class="sidebar-logo">
        <a href="/?view=caja" class="nav-item {% if view == 'caja' %}active{% endif %}">💳 Caja</a>
        {% if session.rol == 'admin' %}
            <a href="/?view=reportes" class="nav-item {% if view == 'reportes' %}active{% endif %}">📊 Reportes</a>
            <a href="/?view=cierre_admin" class="nav-item {% if view == 'cierre_admin' %}active{% endif %}">🔐 Auditoría</a>
            <a href="/?view=admin" class="nav-item {% if view == 'admin' %}active{% endif %}">⚙️ Usuarios</a>
        {% endif %}
        <div class="user-tag"><span>{{ session.usuario }}</span>{{ session.rol | capitalize }}</div>
    </div>

    <div class="mobile-header">
        <img src="https://i.imgur.com/j4gWZ33.png">
    </div>

    <div class="mobile-nav">
        <a href="/?view=caja" class="mobile-nav-item {% if view == 'caja' %}active{% endif %}">
            <i class="fas fa-cash-register"></i><span>Caja</span>
        </a>
        {% if session.rol == 'admin' %}
        <a href="/?view=reportes" class="mobile-nav-item {% if view == 'reportes' %}active{% endif %}">
            <i class="fas fa-chart-line"></i><span>Reportes</span>
        </a>
        <a href="/?view=cierre_admin" class="mobile-nav-item {% if view == 'cierre_admin' %}active{% endif %}">
            <i class="fas fa-file-invoice-dollar"></i><span>Auditoría</span>
        </a>
        <a href="/?view=admin" class="mobile-nav-item {% if view == 'admin' %}active{% endif %}">
            <i class="fas fa-users-cog"></i><span>Perfil</span>
        </a>
        {% endif %}
    </div>

    <a href="/logout" class="btn-logout">Salir</a>
    
    {% if view == 'caja' %}
    <button class="fab-cierre" onclick="mostrarModalAutorizacion()">🖨️ CIERRE</button>
    {% endif %}
    {% endif %}

    <div id="pantallaExito" class="pantalla-modal">
        <div class="caja-exito">
            <div class="icono-exito">✅</div><div class="texto-exito">VERIFICADO</div>
        </div>
    </div>

    <div id="modalAutorizacion" class="pantalla-modal">
        <div class="card-panel" style="max-width: 320px; text-align: center; border-top: 6px solid #ffc107;">
            <h3 style="margin-top:0;">Clave de Cierre</h3>
            <input type="password" id="clave_cierre_input" class="form-control" style="text-align:center; margin-bottom: 15px;">
            <div style="display:flex; gap: 10px;">
                <button class="btn-submit" style="background:#666; margin-top:0;" onclick="document.getElementById('modalAutorizacion').style.display='none'">X</button>
                <button class="btn-submit" style="background:#ffc107; color:#333; margin-top:0;" onclick="procesarAutorizacion()">Imprimir</button>
            </div>
        </div>
    </div>

    <div class="main-wrapper {% if not session.usuario %}login-wrapper{% endif %}">
        {% if not session.usuario %}
        <div class="card-panel" style="max-width: 380px; border-top: 6px solid #0056b3;">
            <center><img src="https://i.imgur.com/j4gWZ33.png" style="height:60px; margin-bottom:20px;"></center>
            <h2 class="titulo-panel">Acceso</h2>
            <form action="/login" method="POST">
                <div class="form-group"><label class="form-label">Usuario</label><input type="text" name="usuario" class="form-control" required></div>
                <div class="form-group"><label class="form-label">Clave</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn-submit" style="background: #0056b3;">ENTRAR</button>
            </form>
        </div>
        {% elif view == 'caja' %}
        <div class="form-section card-panel">
            <h2 class="titulo-panel">Validar Pago</h2>
            <div class="form-group">
                <label class="form-label">📍 Sucursal</label>
                <select id="val_ubicacion" class="form-control">
                    <option value="Cila 22" {% if session.sucursal == 'Cila 22' %}selected{% endif %}>Cila 22</option>
                    <option value="Cila 23" {% if session.sucursal == 'Cila 23' %}selected{% endif %}>Cila 23</option>
                    <option value="Cila 24" {% if session.sucursal == 'Cila 24' %}selected{% endif %}>Cila 24</option>
                    <option value="Cila 25" {% if session.sucursal == 'Cila 25' %}selected{% endif %}>Cila 25</option>
                    <option value="Cila Babilon" {% if session.sucursal == 'Cila Babilon' %}selected{% endif %}>Cila Babilon</option>
                </select>
            </div>
            <div class="form-group"><label class="form-label">💰 Monto</label><input type="text" id="val_monto" class="form-control" placeholder="0.00"></div>
            <div class="form-group"><label class="form-label">🧾 Referencia</label><input type="text" id="val_referencia" class="form-control" placeholder="Últimos dígitos"></div>
            <button class="btn-submit" onclick="buscarPago()">VERIFICAR</button>
        </div>
        <div class="result-section" id="resultadoBusqueda"><div class="placeholder-box">Esperando datos...</div></div>
        {% elif view == 'reportes' %}
            <div class="card-panel" style="border-top-color: #17a2b8;">
                <h2 class="titulo-panel">Histórico</h2>
                <input type="date" id="filtroInicio" class="form-control" style="margin-bottom:10px;">
                <input type="date" id="filtroFin" class="form-control" style="margin-bottom:10px;">
                <button class="btn-submit" style="background:#007bff;" onclick="generarReporte()">BUSCAR</button>
                <div class="tabla-contenedor" style="margin-top:20px;">
                    <table class="tabla-datos" id="tablaReportes"><thead><tr><th>Fecha</th><th>Monto</th><th>Sucursal</th></tr></thead><tbody id="bodyReportes"></tbody></table>
                </div>
            </div>
        {% endif %}
    </div>

    <div class="app-footer">CILA Pagos © 2026</div>

    <script>
        let todosLosPagos = [];
        async function cargarPagosFondo() {
            try { const res = await fetch('/api/pagos'); todosLosPagos = await res.json(); } catch(e) {}
        }
        setInterval(cargarPagosFondo, 5000); cargarPagosFondo();

        function buscarPago() {
            const m = document.getElementById('val_monto').value.trim().replace('.', ','); 
            const r = document.getElementById('val_referencia').value.trim();
            const resDiv = document.getElementById('resultadoBusqueda');
            if(!r) return;
            const p = todosLosPagos.find(x => x.ref.includes(r) && (m === "" ? true : x.monto.includes(m)));
            if(p) {
                if(p.estado === 'verificado') resDiv.innerHTML = `<div class="card" style="border-color:#ffc107;"><h3>DUPLICADO</h3><p>Validado en: ${p.ubicacion}</p></div>`;
                else resDiv.innerHTML = `<div class="card" style="border-color:#198754;"><h3>Bs. ${p.monto}</h3><p>Ref: ${p.ref}</p><button class="btn-submit" onclick="marcarVerificado('${p.id}')">CONFIRMAR</button></div>`;
            } else { resDiv.innerHTML = `<div class="card" style="border-color:#ce1126;"><h3>NO HALLADO</h3></div>`; }
        }

        async function marcarVerificado(id) {
            const ubi = document.getElementById('val_ubicacion').value;
            await fetch('/api/verificar/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ubicacion: ubi }) });
            document.getElementById('pantallaExito').style.display = 'flex';
            setTimeout(() => { location.reload(); }, 1500);
        }

        function mostrarModalAutorizacion() { document.getElementById('modalAutorizacion').style.display='flex'; }
        async function procesarAutorizacion() {
            const c = document.getElementById('clave_cierre_input').value;
            const r = await fetch('/api/validar_cierre', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clave: c }) });
            const d = await r.json();
            if(d.status === 'ok') { window.print(); } else { alert("Error"); }
        }
    </script>
</body>
</html>
"""

# --- RUTAS FLASK (Lógica de servidor intacta) ---
@app.route('/')
def home():
    view = request.args.get('view', 'caja')
    return render_template_string(HTML_TEMPLATE, view=view)

@app.route('/login', methods=['POST'])
def do_login():
    u, p = request.form.get('usuario'), request.form.get('password')
    if u == 'admin' and p == 'cila2026':
        session['usuario'], session['rol'], session['sucursal'] = 'Admin', 'admin', 'Todas'
        return redirect('/')
    try:
        res = requests.get(FIREBASE_USUARIOS).json()
        for i, info in res.items():
            if info.get('usuario') == u and info.get('password') == p:
                session['usuario'], session['rol'], session['sucursal'] = u, info.get('rol','cajero'), info.get('sucursal')
                return redirect('/')
    except: pass
    return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/api/pagos')
def get_pagos():
    r = requests.get(FIREBASE_PAGOS).json()
    if r:
        l = []
        for k, v in r.items(): v['id'] = k; l.append(v)
        return jsonify(l[::-1])
    return jsonify([])

@app.route('/api/verificar/<id>', methods=['POST'])
def verificar_pago(id):
    requests.patch(f"{FIREBASE_URL_BASE}/pagos/{id}.json", json={"estado": "verificado", "ubicacion": request.json.get('ubicacion')})
    return jsonify({"status": "ok"})

@app.route('/api/validar_cierre', methods=['POST'])
def v_c():
    c = requests.get(FIREBASE_CONFIG).json().get('clave_cierre', '1234') if requests.get(FIREBASE_CONFIG).json() else '1234'
    return jsonify({"status": "ok" if request.json.get('clave') == c else "error"})

@app.route('/webhook', methods=['POST'])
def webhook():
    t = request.get_data(as_text=True)
    m = re.search(r"bs\.?\s?([\d,.]+)", t, re.I); mon = m.group(1) if m else "0,00"
    te = re.search(r"del\s(04\d+)", t, re.I); telf = te.group(1) if te else "000"
    r = re.search(r"ref:\s?(\d+)", t, re.I); ref = r.group(1)[-6:] if r else "000"
    h = datetime.utcnow() - timedelta(hours=4)
    requests.post(FIREBASE_PAGOS, json={"monto": mon, "telf": telf, "ref": ref, "fecha": h.strftime("%d/%m/%Y - %I:%M %p"), "estado": "pendiente"})
    return {"status": "ok"}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
