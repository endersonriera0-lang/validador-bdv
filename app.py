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
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>

    <style>
        /* 🎨 DISEÑO CORPORATIVO DASHBOARD 🎨 */
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; min-height: 100vh; background-image: url('https://i.imgur.com/rgsa5XH.png'); background-size: cover; background-position: center; background-attachment: fixed; overflow-x: hidden;}
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 40, 80, 0.75); z-index: -2; backdrop-filter: blur(4px); }
        
        .sidebar { position: fixed; top: 0; left: 0; height: 100vh; width: 240px; background: rgba(0, 15, 30, 0.92); backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.1); padding-top: 30px; display: flex; flex-direction: column; align-items: center; z-index: 100; box-shadow: 4px 0 20px rgba(0,0,0,0.5); }
        .sidebar-logo { max-width: 160px; margin-bottom: 40px; filter: drop-shadow(0px 2px 5px rgba(0,0,0,0.5)); }
        
        .nav-item { display: block; width: 80%; padding: 12px 15px; margin-bottom: 12px; background: rgba(255,255,255,0.05); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: left; transition: 0.3s; border: 1px solid rgba(255,255,255,0.1); font-size: 0.95em; box-sizing: border-box;}
        .nav-item:hover, .nav-item.active { background: rgba(25, 135, 84, 0.8); border-color: #198754; transform: translateX(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.3);}
        
        .user-tag { margin-top: auto; margin-bottom: 30px; background: rgba(255,255,255,0.1); padding: 10px 15px; border-radius: 8px; color: #aaa; font-size: 0.8em; text-align: center; width: 75%; border: 1px dashed rgba(255,255,255,0.2);}
        .user-tag span { display: block; color: white; font-weight: bold; font-size: 1.2em; margin-bottom: 3px;}

        .btn-logout { position: fixed; top: 25px; right: 30px; background: rgba(206,17,38,0.85); color: white; padding: 10px 25px; border-radius: 8px; font-weight: bold; text-decoration: none; border: 1px solid #ff4d4d; z-index: 100; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 0.95em; letter-spacing: 1px;}
        .btn-logout:hover { background: #ce1126; transform: scale(1.05); }

        .fab-cierre { position: fixed; bottom: 80px; right: 30px; background: #ffc107; color: #333; padding: 15px 25px; border-radius: 50px; font-weight: 900; font-size: 1.1em; border: 3px solid white; cursor: pointer; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 100; transition: 0.3s; text-transform: uppercase; display: flex; align-items: center; gap: 8px;}
        .fab-cierre:hover { background: #e0a800; transform: translateY(-5px) scale(1.05); }

        .app-footer { position: fixed; bottom: 20px; left: calc(50% + 120px); transform: translateX(-50%); background: rgba(0, 15, 30, 0.6); backdrop-filter: blur(8px); padding: 8px 30px; border-radius: 30px; color: rgba(255,255,255,0.8); font-size: 0.85em; font-weight: bold; letter-spacing: 1.5px; border: 1px solid rgba(255,255,255,0.15); z-index: 90; box-shadow: 0 4px 10px rgba(0,0,0,0.3);}

        .main-wrapper { margin-left: 240px; width: calc(100% - 240px); display: flex; flex-direction: row; gap: 30px; justify-content: center; align-items: flex-start; padding: 40px; box-sizing: border-box; margin-bottom: 80px; transition: 0.3s;}
        .login-wrapper { margin-left: 0 !important; width: 100% !important; align-items: center; margin-top: 5vh; }

        .card-panel { background: rgba(255, 255, 255, 0.95); padding: 30px 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); backdrop-filter: blur(5px); box-sizing: border-box;}
        .form-section { flex: 1; max-width: 450px; width: 100%; border-top: 6px solid #198754; }
        .result-section { flex: 1.2; max-width: 650px; width: 100%; }
        
        .titulo-panel { margin-top: 0; color: #003366; text-align: center; margin-bottom: 20px; font-size: 1.4em; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;}
        .form-group { margin-bottom: 15px; text-align: left; }
        .form-label { display: block; font-weight: bold; color: #444; margin-bottom: 6px; font-size: 0.85em; text-transform: uppercase; }
        .form-control { width: 100%; padding: 12px; border: 1px solid #c0c0c0; border-radius: 8px; font-size: 15px; box-sizing: border-box; background: #fff; transition: 0.3s;}
        .form-control:focus { outline: none; border-color: #198754; box-shadow: 0 0 0 3px rgba(25,135,84,0.1); }
        .btn-submit { background: #198754; color: white; width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; margin-top: 15px; transition: 0.3s; text-transform: uppercase; box-shadow: 0 4px 6px rgba(25, 135, 84, 0.3);}
        .btn-submit:hover { background: #146c43; transform: translateY(-2px); }

        .placeholder-box { background: rgba(255, 255, 255, 0.1); border: 2px dashed rgba(255, 255, 255, 0.4); border-radius: 15px; padding: 40px 20px; text-align: center; color: rgba(255, 255, 255, 0.8); font-weight: bold; }
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border-left: 8px solid #ce1126; text-align: left; animation: slideIn 0.4s ease-out; }
        .header-card { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px dashed #eee; padding-bottom: 15px; margin-bottom: 15px; }
        .monto { font-size: 1.8em; font-weight: 900; color: #1d1d1b; }
        .datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .dato-item { display: flex; flex-direction: column; }
        .dato-label { font-size: 0.75em; color: #888; text-transform: uppercase; font-weight: bold; }
        .dato-valor { font-size: 1.05em; color: #222; margin-top: 4px; font-weight: 600;}
        .ref { font-family: monospace; font-size: 1.2em; color: #0056b3; font-weight: bold; }
        
        .pantalla-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.85); z-index: 9999; display: none; justify-content: center; align-items: center; backdrop-filter: blur(8px); }
        .caja-exito { background: #2ecc71; padding: 40px 60px; border-radius: 20px; text-align: center; color: white; border: 5px solid white; animation: estallar 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; align-items: center; }
        .icono-exito { font-size: 90px; margin-bottom: 10px; line-height: 1;}
        .texto-exito { font-size: 38px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;}
        
        .tabla-contenedor { overflow-x: auto; margin-top: 10px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05); border: 1px solid #eee;}
        .tabla-datos { width: 100%; border-collapse: collapse; font-size: 0.9em; background: white;}
        .tabla-datos th, .tabla-datos td { border-bottom: 1px solid #eee; padding: 12px 15px; text-align: left; }
        .tabla-datos th { background-color: #003366; color: white; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; position: sticky; top: 0;}
        .badge-tabla { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
        .badge-verde { background: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
        .badge-amarillo { background: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
        
        @keyframes estallar { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

        @media (max-width: 900px) {
            .sidebar { width: 100%; height: auto; position: relative; flex-direction: row; flex-wrap: wrap; padding: 15px; justify-content: center; }
            .main-wrapper { margin-left: 0; width: 100%; flex-direction: column; align-items: center; padding: 20px;}
            .app-footer { left: 50%; transform: translateX(-50%); bottom: 10px;}
        }
    </style>
</head>
<body>
    <div class="overlay"></div>
    <iframe id="iframeTicket" style="display:none;"></iframe>
    <iframe id="iframeCarta" style="display:none;"></iframe>

    {% if session.usuario %}
    <div class="sidebar">
        <img src="https://i.imgur.com/j4gWZ33.png" class="sidebar-logo">
        <a href="/?view=caja" class="nav-item {% if view == 'caja' %}active{% endif %}" style="border-left: 4px solid #198754;">💳 Validar Pagos</a>
        {% if session.rol == 'admin' %}
            <a href="/?view=reportes" class="nav-item {% if view == 'reportes' %}active{% endif %}" style="border-left: 4px solid #17a2b8;">📊 Reportes</a>
            <a href="/?view=cierre_admin" class="nav-item {% if view == 'cierre_admin' %}active{% endif %}" style="border-left: 4px solid #fd7e14;">🔐 Cierres Carta</a>
            <a href="/?view=admin" class="nav-item {% if view == 'admin' %}active{% endif %}" style="border-left: 4px solid #ffc107;">⚙️ Usuarios</a>
        {% endif %}
        <div class="user-tag"><span>{{ session.usuario }}</span>Perfil: {{ session.rol | capitalize }}</div>
    </div>

    <a href="/logout" class="btn-logout">Salir 🚪</a>
    
    {% if view == 'caja' %}
    <button class="fab-cierre" onclick="mostrarModalAutorizacion()">🖨️ CIERRE DE CAJA</button>
    {% endif %}
    
    <div class="app-footer">CILA Pagos Automáticos © 2026</div>
    {% endif %}

    <div id="pantallaExito" class="pantalla-modal">
        <div class="caja-exito">
            <div class="icono-exito">✅</div><div class="texto-exito">¡PAGO VERIFICADO!</div><div id="textoSucursal" style="font-size: 18px; font-weight: bold; margin-top: 10px;">Procesado con éxito</div>
        </div>
    </div>

    <div id="modalAutorizacion" class="pantalla-modal">
        <div class="card-panel" style="max-width: 350px; text-align: center; border-top: 6px solid #ffc107;">
            <h3 style="color: #333; margin-top:0;">🔒 Autorización</h3>
            <p style="font-size:0.9em; color:#666;">Ingrese la clave para imprimir el ticket de caja.</p>
            <input type="password" id="clave_cierre_input" class="form-control" style="text-align:center; font-size: 1.2em; letter-spacing: 3px; margin-bottom: 20px;">
            <div style="display:flex; gap: 10px;">
                <button class="btn-submit" style="background:#6c757d; margin-top:0;" onclick="document.getElementById('modalAutorizacion').style.display='none'">Cancelar</button>
                <button class="btn-submit" style="background:#ffc107; color:#333; margin-top:0;" onclick="procesarAutorizacion()">Imprimir</button>
            </div>
        </div>
    </div>

    <div class="main-wrapper {% if not session.usuario %}login-wrapper{% endif %}">
        
        {% if not session.usuario %}
        <div class="card-panel form-section" style="border-top-color: #0056b3; margin: auto; max-width: 400px;">
            <div style="text-align: center; margin-bottom: 20px;"><img src="https://i.imgur.com/j4gWZ33.png" style="max-height: 80px;"></div>
            <h2 class="titulo-panel">Acceso al Sistema</h2>
            {% if error %}<div class="alerta-error" style="margin-bottom: 15px;">{{ error }}</div>{% endif %}
            <form action="/login" method="POST">
                <div class="form-group"><label class="form-label">👤 Usuario</label><input type="text" name="usuario" class="form-control" required></div>
                <div class="form-group"><label class="form-label">🔒 Contraseña</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn-submit" style="background: #0056b3;">INICIAR SESIÓN</button>
            </form>
        </div>

        {% elif view == 'cierre_admin' and session.rol == 'admin' %}
        <div class="form-section card-panel" style="border-top-color: #fd7e14; height: fit-content;">
            <h2 class="titulo-panel">Cierres de Auditoría</h2>
            <div class="form-group"><label class="form-label">📅 Fecha:</label><input type="date" id="fechaCierreCarta" class="form-control"></div>
            <div class="form-group"><label class="form-label">📍 Sucursal:</label><select id="sucursalCierreCarta" class="form-control"><option value="Todas">Todas las sucursales</option><option value="Cila 22">Cila 22</option><option value="Cila 23">Cila 23</option><option value="Cila 24">Cila 24</option><option value="Cila 25">Cila 25</option><option value="Cila Babilon">Cila Babilon</option></select></div>
            <button class="btn-submit" style="background: #003366;" onclick="visualizarCierreCarta()">👁️ Visualizar</button>
            <button class="btn-submit" style="background: #fd7e14; margin-top: 10px;" onclick="generarCierreCarta()">🖨️ Imprimir</button>
        </div>
        <div class="result-section card-panel" style="max-width: 700px; padding: 20px;"><div id="vistaPreviaCierre"><div class="placeholder-box" style="margin: 40px 0;">👁️<br>Visualización previa aquí</div></div></div>

        {% elif view == 'reportes' and session.rol == 'admin' %}
        <div class="card-panel" style="width: 100%; max-width: 1000px; border-top: 6px solid #17a2b8;">
            <h2 class="titulo-panel">📊 Histórico de Transacciones</h2>
            <div style="display: flex; gap: 15px; margin-bottom: 25px; align-items: flex-end; flex-wrap: wrap; background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 150px;"><label class="form-label">Desde:</label><input type="date" id="filtroInicio" class="form-control"></div>
                <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 150px;"><label class="form-label">Hasta:</label><input type="date" id="filtroFin" class="form-control"></div>
                <button class="btn-submit" style="background: #007bff; width: auto; margin-top: 0; padding: 12px 20px;" onclick="generarReporte()">🔍 Filtrar</button>
                <div style="flex-basis: 100%; height: 0;"></div>
                <button class="btn-submit" style="background: #28a745; width: auto; margin-top: 0; padding: 10px 15px;" onclick="exportarExcel()">📗 Excel</button>
                <button class="btn-submit" style="background: #dc3545; width: auto; margin-top: 0; padding: 10px 15px;" onclick="exportarPDF()">📕 PDF</button>
            </div>
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div style="flex:1; background: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;"><h4>Total Ingresos</h4><h2 id="resumenMonto">Bs. 0,00</h2></div>
                <div style="flex:1; background: #e2e3e5; padding: 20px; border-radius: 10px; text-align: center;"><h4>Operaciones</h4><h2 id="resumenConteo">0</h2></div>
            </div>
            <div class="tabla-contenedor" style="max-height: 400px; overflow-y: auto;"><table class="tabla-datos" id="tablaReportes"><thead><tr><th>Fecha y Hora</th><th>Ref</th><th>Telf</th><th>Monto</th><th>Sucursal</th><th>Estado</th></tr></thead><tbody id="bodyReportes"><tr><td colspan="6" style="text-align:center; padding: 20px;">Use los filtros arriba para buscar</td></tr></tbody></table></div>
        </div>

        {% elif view == 'admin' and session.rol == 'admin' %}
        <div class="card-panel" style="width: 100%; max-width: 850px; border-top: 6px solid #ffc107;">
            <h2 class="titulo-panel">⚙️ Panel de Administración</h2>
            <div style="display: flex; gap: 25px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px; background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                    <h3>Crear Perfil</h3>
                    <form action="/crear_usuario" method="POST">
                        <div class="form-group"><label class="form-label">Usuario</label><input type="text" name="usuario" class="form-control" required></div>
                        <div class="form-group"><label class="form-label">Clave</label><input type="text" name="password" class="form-control" required></div>
                        <div class="form-group"><label class="form-label">Sucursal</label><select name="sucursal" class="form-control"><option value="Cila 22">Cila 22</option><option value="Cila 23">Cila 23</option><option value="Cila 24">Cila 24</option><option value="Cila 25">Cila 25</option><option value="Cila Babilon">Cila Babilon</option></select></div>
                        <button type="submit" class="btn-submit" style="background: #333;">Añadir</button>
                    </form>
                </div>
            </div>
        </div>

        {% else %}
        <div class="form-section card-panel" style="height: fit-content;">
            <h2 class="titulo-panel">Validación de Pagos</h2>
            <div class="form-group"><label class="form-label">📍 Ubicación:</label><select id="val_ubicacion" class="form-control"><option value="Cila 22" {% if session.sucursal == 'Cila 22' %}selected{% endif %}>Cila 22</option><option value="Cila 23" {% if session.sucursal == 'Cila 23' %}selected{% endif %}>Cila 23</option><option value="Cila 24" {% if session.sucursal == 'Cila 24' %}selected{% endif %}>Cila 24</option><option value="Cila 25" {% if session.sucursal == 'Cila 25' %}selected{% endif %}>Cila 25</option><option value="Cila Babilon" {% if session.sucursal == 'Cila Babilon' %}selected{% endif %}>Cila Babilon</option></select></div>
            <div class="form-group"><label class="form-label">💰 Monto:</label><input type="text" id="val_monto" class="form-control" placeholder="Ej: 25,50"></div>
            <div class="form-group"><label class="form-label">🧾 Referencia:</label><input type="text" id="val_referencia" class="form-control" placeholder="Últimos dígitos"></div>
            <button class="btn-submit" onclick="buscarPago()">Validar Pago</button>
        </div>
        <div class="result-section" id="resultadoBusqueda"><div class="placeholder-box" style="margin-top: 20px;">🔍<br>Resultado aquí</div></div>
        {% endif %}
    </div>

    <script>
        const SESION_ROL = "{{ session.rol | default('cajero') }}";
        let todosLosPagos = [];

        // CORRECCIÓN: Cargar pagos sin disparar alertas de reporte automáticamente
        async function cargarPagosFondo() {
            try { 
                const res = await fetch('/api/pagos'); 
                todosLosPagos = await res.json(); 
                // Ya no llamamos a generarReporte() aquí para evitar el bucle de alertas
            } catch(e) {}
        }
        setInterval(cargarPagosFondo, 5000);
        cargarPagosFondo();

        // --- CAJA ---
        function buscarPago() {
            const m = document.getElementById('val_monto').value.trim().replace('.', ','); 
            const r = document.getElementById('val_referencia').value.trim();
            const resDiv = document.getElementById('resultadoBusqueda');
            if(!r) return alert("Debe poner la referencia.");
            const p = todosLosPagos.find(x => x.ref.includes(r) && (m === "" ? true : x.monto.includes(m)));
            if(p) {
                if(p.estado === 'verificado') { resDiv.innerHTML = `<div class="alerta-duplicado"><h3>🚨 DUPLICADO</h3><p>Ya procesado en: ${p.ubicacion}</p></div>`; }
                else { resDiv.innerHTML = `<div class="card"><h3>Bs. ${p.monto}</h3><p>Ref: ${p.ref}</p><button class="btn-submit" onclick="marcarVerificado('${p.id}', this)">✔️ Confirmar</button></div>`; }
            } else { resDiv.innerHTML = `<div class="alerta-error">No encontrado</div>`; }
        }

        async function marcarVerificado(id, btn) {
            const ubi = document.getElementById('val_ubicacion').value;
            await fetch('/api/verificar/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ubicacion: ubi }) });
            document.getElementById('pantallaExito').style.display = 'flex';
            setTimeout(() => { document.getElementById('pantallaExito').style.display = 'none'; cargarPagosFondo(); buscarPago(); }, 2000);
        }

        // --- REPORTES (LÓGICA CORREGIDA) ---
        function generarReporte() {
            const ini = document.getElementById('filtroInicio').value;
            const fin = document.getElementById('filtroFin').value;
            if(!ini || !fin) {
                alert("Por favor, seleccione ambas fechas (Desde y Hasta) antes de filtrar.");
                return;
            }
            const tbody = document.getElementById('bodyReportes');
            let filtrados = todosLosPagos.filter(x => {
                let f = x.fecha.split(' - ')[0].split('/').reverse().join('-'); // Convierte DD/MM/YYYY a YYYY-MM-DD
                return f >= ini && f <= fin;
            });
            tbody.innerHTML = ""; let sum = 0; let count = 0;
            filtrados.forEach(x => {
                if(x.estado === 'verificado') { sum += parseFloat(x.monto.replace(/\./g, '').replace(',', '.')); count++; }
                tbody.innerHTML += `<tr><td>${x.fecha}</td><td>${x.ref}</td><td>${x.telf}</td><td>${x.monto}</td><td>${x.ubicacion||'-'}</td><td>${x.estado}</td></tr>`;
            });
            document.getElementById('resumenMonto').innerText = "Bs. " + sum.toLocaleString('es-VE');
            document.getElementById('resumenConteo').innerText = count;
        }

        // --- CIERRES CARTA ---
        let filtradosCarta = [];
        function visualizarCierreCarta() {
            const f = document.getElementById('fechaCierreCarta').value;
            if(!f) return alert("Ponga una fecha");
            const suc = document.getElementById('sucursalCierreCarta').value;
            filtradosCarta = todosLosPagos.filter(x => {
                let fechaX = x.fecha.split(' - ')[0].split('/').reverse().join('-');
                return x.estado === 'verificado' && fechaX === f && (suc === "Todas" ? true : x.ubicacion === suc);
            });
            let sum = 0; let html = `<table class="tabla-datos"><thead><tr><th>Hora</th><th>Ref</th><th>Sucursal</th><th>Monto</th></tr></thead><tbody>`;
            filtradosCarta.forEach(x => { sum += parseFloat(x.monto.replace(/\./g, '').replace(',', '.')); html += `<tr><td>${x.fecha.split(' - ')[1]}</td><td>${x.ref}</td><td>${x.ubicacion}</td><td>Bs. ${x.monto}</td></tr>`; });
            document.getElementById('vistaPreviaCierre').innerHTML = `<h3>Total: Bs. ${sum.toLocaleString('es-VE')}</h3>` + html + "</tbody></table>";
        }

        // Autorización para ticket
        function mostrarModalAutorizacion() { document.getElementById('modalAutorizacion').style.display='flex'; }
        async function procesarAutorizacion() {
            const c = document.getElementById('clave_cierre_input').value;
            const r = await fetch('/api/validar_cierre', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clave: c }) });
            const d = await r.json();
            if(d.status === 'ok') { document.getElementById('modalAutorizacion').style.display='none'; window.print(); } else { alert("Clave mal"); }
        }
    </script>
</body>
</html>
"""

# Rutas Python (Se mantienen igual)
@app.route('/')
def home():
    view = request.args.get('view', 'caja')
    return render_template_string(HTML_TEMPLATE, view=view)

@app.route('/login', methods=['POST'])
def do_login():
    u = request.form.get('usuario'); p = request.form.get('password')
    if u == 'admin' and p == 'cila2026':
        session['usuario'] = 'Admin'; session['rol'] = 'admin'; session['sucursal'] = 'Todas'; return redirect('/')
    try:
        res = requests.get(FIREBASE_USUARIOS)
        if res.json():
            for i, info in res.json().items():
                if info.get('usuario') == u and info.get('password') == p:
                    session['usuario'] = u; session['rol'] = info.get('rol','cajero'); session['sucursal'] = info.get('sucursal'); return redirect('/')
    except: pass
    return render_template_string(HTML_TEMPLATE, error="Error")

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    requests.post(FIREBASE_USUARIOS, json=request.form.to_dict()); return redirect('/?view=admin')

@app.route('/api/pagos')
def get_pagos():
    r = requests.get(FIREBASE_PAGOS)
    if r.json():
        l = []
        for k, v in r.json().items(): v['id'] = k; l.append(v)
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
