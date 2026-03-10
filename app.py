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
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Sistema Corporativo CILA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

    <style>
        /* 🎨 RESET Y FONDO GLOBAL 🎨 */
        body, html { margin: 0; padding: 0; min-height: 100vh; font-family: 'Segoe UI', sans-serif; overflow-x: hidden; }
        body { 
            background-image: url('https://i.imgur.com/rgsa5XH.png'); 
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 40, 80, 0.75); z-index: -2; backdrop-filter: blur(3px); }

        /* 💻 DISEÑO PARA COMPUTADORAS (ESCRITORIO) 💻 */
        .sidebar { 
            position: fixed; top: 0; left: 0; height: 100vh; width: 240px; 
            background: rgba(0, 15, 30, 0.95); display: flex; flex-direction: column; 
            align-items: center; padding-top: 30px; z-index: 100; border-right: 1px solid rgba(255,255,255,0.1); 
        }
        .sidebar-logo { max-width: 160px; margin-bottom: 40px; }
        .nav-item { 
            display: block; width: 85%; padding: 12px 15px; margin-bottom: 10px; 
            color: white; text-decoration: none; border-radius: 10px; font-weight: bold; 
            transition: 0.3s; font-size: 0.9em; background: rgba(255,255,255,0.05);
        }
        .nav-item.active { background: #198754; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .user-tag { margin-top: auto; margin-bottom: 80px; color: #aaa; font-size: 0.8em; text-align: center; }
        .user-tag span { display: block; color: white; font-weight: bold; font-size: 1.1em; }

        .main-wrapper { margin-left: 240px; padding: 40px; display: flex; gap: 30px; justify-content: center; align-items: flex-start; }
        .mobile-header, .mobile-nav { display: none; } /* Ocultos en PC */

        .btn-logout { position: fixed; top: 20px; right: 20px; background: #ce1126; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; z-index: 102; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

        /* 📱 DISEÑO PARA MÓVILES (TELÉFONOS) 📱 */
        @media (max-width: 900px) {
            .sidebar { display: none; }
            .main-wrapper { margin-left: 0; padding: 80px 15px 100px 15px; flex-direction: column; }
            .mobile-header { 
                display: flex; position: fixed; top: 0; width: 100%; height: 60px; 
                background: #000f1e; z-index: 101; align-items: center; justify-content: center; 
                border-bottom: 1px solid rgba(255,255,255,0.1); 
            }
            .mobile-header img { height: 35px; }
            .mobile-nav { 
                display: flex; position: fixed; bottom: 0; width: 100%; background: #000f1e; 
                height: 70px; z-index: 1000; justify-content: space-around; align-items: center;
                border-top: 1px solid rgba(255,255,255,0.1);
            }
            .mobile-nav-item { color: #888; text-decoration: none; font-size: 0.7em; text-align: center; display: flex; flex-direction: column; }
            .mobile-nav-item.active { color: #198754; }
            .mobile-nav-item i { font-size: 20px; margin-bottom: 4px; }
            .btn-logout { top: 12px; right: 12px; padding: 8px 12px; font-size: 0.8em; }
        }

        /* 🃏 TARJETAS Y COMPONENTES 🃏 */
        .card-panel { background: rgba(255, 255, 255, 0.96); padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); width: 100%; box-sizing: border-box; }
        .form-section { flex: 1; max-width: 420px; border-top: 6px solid #198754; }
        .result-section { flex: 1.3; max-width: 600px; }
        
        .titulo-panel { margin-top: 0; color: #003366; text-align: center; font-size: 1.3em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px;}
        .form-group { margin-bottom: 15px; }
        .form-label { display: block; font-weight: bold; color: #555; margin-bottom: 5px; font-size: 0.85em; }
        .form-control { width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        
        .btn-submit { background: #198754; color: white; width: 100%; padding: 16px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; text-transform: uppercase; transition: 0.3s; }
        .btn-submit:hover { background: #146c43; transform: translateY(-2px); }

        /* MODALES */
        .pantalla-modal { 
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0, 0, 0, 0.85); z-index: 9999; 
            display: none; justify-content: center; align-items: center; backdrop-filter: blur(8px); 
        }
        .caja-exito { background: #2ecc71; padding: 40px 60px; border-radius: 20px; text-align: center; color: white; border: 5px solid white; animation: estallar 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .icono-exito { font-size: 80px; margin-bottom: 10px; }

        .fab-cierre { 
            position: fixed; bottom: 30px; right: 30px; background: #ffc107; 
            color: #333; padding: 18px 25px; border-radius: 50px; font-weight: 900; 
            border: 3px solid white; cursor: pointer; box-shadow: 0 8px 25px rgba(0,0,0,0.5); z-index: 100; 
        }
        
        /* FOOTER */
        .app-footer { 
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); 
            background: rgba(0, 15, 30, 0.6); padding: 8px 30px; border-radius: 30px; 
            color: white; font-size: 0.8em; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); 
        }

        .login-container { height: 100vh; display: flex; align-items: center; justify-content: center; }

    </style>
</head>
<body>
    <div class="overlay"></div>
    <iframe id="iframeTicket" style="display:none;"></iframe>

    {% if session.usuario %}
    <div class="sidebar">
        <img src="https://i.imgur.com/j4gWZ33.png" class="sidebar-logo">
        <a href="/?view=caja" class="nav-item {% if view == 'caja' %}active{% endif %}">💳 Caja Principal</a>
        {% if session.rol == 'admin' %}
            <a href="/?view=reportes" class="nav-item {% if view == 'reportes' %}active{% endif %}">📊 Reportes</a>
            <a href="/?view=admin" class="nav-item {% if view == 'admin' %}active{% endif %}">⚙️ Usuarios</a>
        {% endif %}
        <div class="user-tag"><span>{{ session.usuario }}</span>{{ session.rol | capitalize }}</div>
    </div>

    <div class="mobile-header"><img src="https://i.imgur.com/j4gWZ33.png"></div>
    <div class="mobile-nav">
        <a href="/?view=caja" class="mobile-nav-item {% if view == 'caja' %}active{% endif %}"><i class="fas fa-cash-register"></i><span>Caja</span></a>
        {% if session.rol == 'admin' %}
        <a href="/?view=reportes" class="mobile-nav-item {% if view == 'reportes' %}active{% endif %}"><i class="fas fa-chart-line"></i><span>Reportes</span></a>
        <a href="/?view=admin" class="mobile-nav-item {% if view == 'admin' %}active{% endif %}"><i class="fas fa-users-cog"></i><span>Admin</span></a>
        {% endif %}
    </div>

    <a href="/logout" class="btn-logout">Salir</a>
    {% if view == 'caja' %}<button class="fab-cierre" onclick="document.getElementById('modalAutorizacion').style.display='flex'">🖨️ CIERRE</button>{% endif %}
    {% endif %}

    <div class="main-wrapper">
        
        {% if not session.usuario %}
        <div class="login-container">
            <div class="card-panel" style="max-width: 380px; border-top: 6px solid #0056b3;">
                <center><img src="https://i.imgur.com/j4gWZ33.png" style="height:60px; margin-bottom:20px;"></center>
                <h2 class="titulo-panel">Acceso</h2>
                <form action="/login" method="POST">
                    <div class="form-group"><label class="form-label">Usuario</label><input type="text" name="usuario" class="form-control" required></div>
                    <div class="form-group"><label class="form-label">Contraseña</label><input type="password" name="password" class="form-control" required></div>
                    <button type="submit" class="btn-submit" style="background: #0056b3;">ENTRAR</button>
                </form>
            </div>
        </div>

        {% elif view == 'caja' %}
        <div class="form-section card-panel">
            <h2 class="titulo-panel">Validar Pago</h2>
            <div class="form-group">
                <label class="form-label">📍 Sucursal</label>
                <select id="val_ubicacion" class="form-control">
                    <option value="Cila 22" {% if session.sucursal == 'Cila 22' %}selected{% endif %}>Cila 22</option>
                    <option value="Cila 23" {% if session.sucursal == 'Cila 23' %}selected{% endif %}>Cila 23</option>
                    <option value="Cila Babilon" {% if session.sucursal == 'Cila Babilon' %}selected{% endif %}>Cila Babilon</option>
                </select>
            </div>
            <div class="form-group"><label class="form-label">💰 Monto</label><input type="text" id="val_monto" class="form-control" placeholder="0,00"></div>
            <div class="form-group"><label class="form-label">🧾 Referencia</label><input type="text" id="val_referencia" class="form-control" placeholder="Últimos dígitos"></div>
            <button class="btn-submit" onclick="buscarPago()">VERIFICAR AHORA</button>
        </div>
        <div class="result-section" id="resultadoBusqueda">
            <div class="placeholder-box">Esperando datos de validación...</div>
        </div>
        {% endif %}
    </div>

    <div id="modalAutorizacion" class="pantalla-modal">
        <div class="card-panel" style="max-width: 320px; text-align: center; border-top: 6px solid #ffc107;">
            <h3 style="margin-top:0;">Clave de Cierre</h3>
            <p style="font-size: 0.8em; color:#666;">Ingrese clave de administrador</p>
            <input type="password" id="clave_cierre_input" class="form-control" style="text-align:center; font-size: 1.5em; letter-spacing: 5px;">
            <div style="display:flex; gap: 10px; margin-top: 20px;">
                <button class="btn-submit" style="background:#666; margin-top:0;" onclick="document.getElementById('modalAutorizacion').style.display='none'">CANCELAR</button>
                <button class="btn-submit" style="background:#ffc107; color:#333; margin-top:0;" onclick="procesarAutorizacion()">IMPRIMIR</button>
            </div>
        </div>
    </div>

    <div id="pantallaExito" class="pantalla-modal">
        <div class="caja-exito"><div class="icono-exito">✅</div><div class="texto-exito">VERIFICADO</div></div>
    </div>

    <div class="app-footer">CILA Pagos Automáticos © 2026</div>

    <script>
        let todosLosPagos = [];
        async function cargarPagos() {
            try { const res = await fetch('/api/pagos'); todosLosPagos = await res.json(); } catch(e){}
        }
        setInterval(cargarPagos, 5000); cargarPagos();

        function buscarPago() {
            const m = document.getElementById('val_monto').value.trim().replace('.', ','); 
            const r = document.getElementById('val_referencia').value.trim();
            const resDiv = document.getElementById('resultadoBusqueda');
            if(!r) return;
            const p = todosLosPagos.find(x => x.ref.includes(r) && (m === "" ? true : x.monto.includes(m)));
            if(p) {
                if(p.estado === 'verificado') resDiv.innerHTML = `<div class="card"><h3>⚠️ DUPLICADO</h3><p>Procesado en: ${p.ubicacion}</p></div>`;
                else resDiv.innerHTML = `<div class="card" style="border-color:#198754"><h3>Bs. ${p.monto}</h3><p>Ref: ${p.ref}</p><button class="btn-submit" onclick="marcarVerificado('${p.id}')">CONFIRMAR PAGO</button></div>`;
            } else { resDiv.innerHTML = `<div class="card" style="border-color:#ce1126"><h3>❌ NO ENCONTRADO</h3></div>`; }
        }

        async function marcarVerificado(id) {
            const ubi = document.getElementById('val_ubicacion').value;
            await fetch('/api/verificar/' + id, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ubicacion: ubi}) });
            document.getElementById('pantallaExito').style.display = 'flex';
            setTimeout(() => { location.reload(); }, 2000);
        }

        async function procesarAutorizacion() {
            const c = document.getElementById('clave_cierre_input').value;
            const r = await fetch('/api/validar_cierre', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({clave: c}) });
            const d = await r.json();
            if(d.status === 'ok') { window.print(); } else { alert("Clave Incorrecta"); }
        }
    </script>
</body>
</html>
"""

# --- RUTAS DE SERVIDOR (Iguales) ---
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
