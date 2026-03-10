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
        /* 🎨 DISEÑO CORPORATIVO CILA 🎨 */
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; background-image: url('https://i.imgur.com/rgsa5XH.png'); background-size: cover; background-position: center; background-attachment: fixed; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 40, 80, 0.70); z-index: -2; backdrop-filter: blur(3px); }
        
        .top-bar { position: fixed; top: 0; left: 0; width: 100%; background: rgba(0, 15, 30, 0.95); padding: 10px 20px; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; z-index: 100; box-shadow: 0 4px 15px rgba(0,0,0,0.6); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .top-bar-espacio { flex: 1; color: white; font-size: 0.9em; font-weight: bold;}
        .top-bar-logo { flex: 1; text-align: center; }
        .top-bar-logo img { max-height: 45px; filter: drop-shadow(0px 2px 5px rgba(0,0,0,0.5)); }
        .top-bar-botones { flex: 1; text-align: right; display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap;}
        
        .btn-nav { background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 8px 12px; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.85em; transition: 0.3s; display: inline-flex; align-items: center; gap: 5px;}
        .btn-nav:hover { background: rgba(255,255,255,0.2); }
        .btn-cierre { background: #ffc107; color: #333; border: none; padding: 8px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85em; box-shadow: 0 4px 6px rgba(255, 193, 7, 0.3); transition: 0.3s; display: inline-flex; align-items: center; gap: 5px;}
        .btn-cierre:hover { background: #e0a800; transform: translateY(-2px); }

        .main-wrapper { display: flex; flex-direction: row; gap: 30px; justify-content: center; align-items: flex-start; width: 100%; max-width: 1100px; z-index: 1; margin-top: 100px; padding: 0 20px; box-sizing: border-box; margin-bottom: 40px;}

        .card-panel { background: rgba(255, 255, 255, 0.95); padding: 30px 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); backdrop-filter: blur(5px); width: 100%; box-sizing: border-box;}
        .form-section { flex: 1; max-width: 450px; width: 100%; border-top: 6px solid #198754; }
        .result-section { flex: 1; max-width: 500px; width: 100%; }
        
        .titulo-panel { margin-top: 0; color: #003366; text-align: center; margin-bottom: 20px; font-size: 1.4em; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;}
        .form-group { margin-bottom: 15px; text-align: left; }
        .form-label { display: block; font-weight: bold; color: #444; margin-bottom: 6px; font-size: 0.85em; text-transform: uppercase; }
        .form-control { width: 100%; padding: 12px; border: 1px solid #c0c0c0; border-radius: 8px; font-size: 15px; box-sizing: border-box; background: #fff; transition: 0.3s;}
        .form-control:focus { outline: none; border-color: #198754; box-shadow: 0 0 0 3px rgba(25,135,84,0.1); }
        .form-control:disabled { background: #e9ecef; font-weight: bold; color: #333; cursor: not-allowed; border-color: #ccc;}
        
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
        .btn-verificar { width: 100%; background: #007bff; color: white; border: none; padding: 14px; border-radius: 8px; font-size: 1.05em; font-weight: bold; cursor: pointer; text-transform: uppercase; transition: 0.3s;}
        
        .alerta-duplicado { background: #ffe3e3; padding: 25px; border-radius: 12px; border: 3px solid #ce1126; color: #900000; text-align: center; animation: slideIn 0.3s;}
        .alerta-error { background: #ffeeba; padding: 15px; border-radius: 8px; border: 1px solid #ffc107; color: #856404; text-align: center; font-size: 0.95em; animation: slideIn 0.3s;}
        
        .pantalla-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.85); z-index: 9999; display: none; justify-content: center; align-items: center; backdrop-filter: blur(8px); }
        .caja-exito { background: #2ecc71; padding: 40px 60px; border-radius: 20px; text-align: center; color: white; border: 5px solid white; animation: estallar 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; align-items: center; }
        .icono-exito { font-size: 90px; margin-bottom: 10px; line-height: 1;}
        .texto-exito { font-size: 38px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;}
        .subtexto-exito { font-size: 18px; margin-top: 10px; opacity: 0.9; font-weight: bold;}
        
        .tabla-contenedor { overflow-x: auto; margin-top: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
        .tabla-datos { width: 100%; border-collapse: collapse; font-size: 0.9em; background: white;}
        .tabla-datos th, .tabla-datos td { border: 1px solid #eee; padding: 12px 15px; text-align: left; }
        .tabla-datos th { background-color: #003366; color: white; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; position: sticky; top: 0;}
        .tabla-datos tr:nth-child(even) { background-color: #f8f9fa; }
        .badge-tabla { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
        .badge-verde { background: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
        .badge-amarillo { background: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
        
        @keyframes estallar { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

        .ocultar-movil { display: inline; }
        @media (max-width: 850px) {
            .main-wrapper { flex-direction: column; align-items: center; gap: 20px; margin-top: 90px;}
            .placeholder-box { display: none; }
            .top-bar-espacio, .ocultar-movil { display: none; }
            .btn-nav, .btn-cierre { padding: 8px; font-size: 0.9em;}
        }
    </style>
</head>
<body>
    <div class="overlay"></div>
    <iframe id="iframeTicket" style="display:none;"></iframe>
    <iframe id="iframeCarta" style="display:none;"></iframe>

    {% if session.usuario %}
    <div class="top-bar">
        <div class="top-bar-espacio">👤 {{ session.usuario }} ({{ session.rol | capitalize }})</div>
        <div class="top-bar-logo">
            <img src="https://i.imgur.com/j4gWZ33.png" alt="Logo Cila">
        </div>
        <div class="top-bar-botones">
            <button class="btn-cierre" onclick="mostrarModalAutorizacion()">🖨️ <span class="ocultar-movil">Cierre (Ticket)</span></button>
            
            {% if session.rol == 'admin' %}
                {% if view != 'cierre_admin' %}
                    <a href="/?view=cierre_admin" class="btn-nav" style="background: #fd7e14;">🔐 <span class="ocultar-movil">Cierres</span></a>
                {% endif %}
                {% if view != 'caja' %}
                    <a href="/" class="btn-nav">⬅️ <span class="ocultar-movil">Caja</span></a>
                {% endif %}
                {% if view != 'reportes' %}
                    <a href="/?view=reportes" class="btn-nav" style="background: #17a2b8;">📊 <span class="ocultar-movil">Reportes</span></a>
                {% endif %}
                {% if view != 'admin' %}
                    <a href="/?view=admin" class="btn-nav">⚙️ <span class="ocultar-movil">Usuarios</span></a>
                {% endif %}
            {% endif %}
            
            <a href="/logout" class="btn-nav" style="background: rgba(206,17,38,0.8); border-color: red;">Salir</a>
        </div>
    </div>
    {% endif %}

    <div id="pantallaExito" class="pantalla-modal">
        <div class="caja-exito">
            <div class="icono-exito">✅</div><div class="texto-exito">¡PAGO VERIFICADO!</div><div id="textoSucursal" class="subtexto-exito">Procesado con éxito</div>
        </div>
    </div>

    <div id="modalAutorizacion" class="pantalla-modal">
        <div class="card-panel" style="max-width: 350px; text-align: center; border-top: 6px solid #ffc107;">
            <h3 style="color: #333; margin-top:0;">🔒 Autorización</h3>
            <p style="font-size:0.9em; color:#666;">Ingrese la clave de administrador para imprimir el reporte.</p>
            <input type="password" id="clave_cierre_input" class="form-control" style="text-align:center; font-size: 1.2em; letter-spacing: 3px; margin-bottom: 20px;">
            <div style="display:flex; gap: 10px;">
                <button class="btn-submit" style="background:#6c757d; margin-top:0;" onclick="document.getElementById('modalAutorizacion').style.display='none'">Cancelar</button>
                <button class="btn-submit" style="background:#ffc107; color:#333; margin-top:0;" onclick="procesarAutorizacion()">Imprimir</button>
            </div>
        </div>
    </div>

    <div class="main-wrapper">
        
        {% if not session.usuario %}
        <div class="card-panel form-section" style="border-top-color: #0056b3; margin: auto;">
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
        <div class="card-panel" style="width: 100%; max-width: 500px; border-top: 6px solid #fd7e14; margin: 0 auto;">
            <div style="text-align:center; font-size: 3em; margin-bottom: 10px;">🖨️</div>
            <h2 class="titulo-panel">Módulo de Cierres (Carta)</h2>
            <p style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 25px;">
                Genera un informe detallado listo para imprimir en formato A4/Carta para el control financiero.
            </p>
            
            <div class="form-group">
                <label class="form-label">📅 Fecha de Cierre:</label>
                <input type="date" id="fechaCierreCarta" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label class="form-label">📍 Filtrar Sucursal:</label>
                <select id="sucursalCierreCarta" class="form-control">
                    <option value="Todas">👉 Todas las sucursales (Consolidado)</option>
                    <option value="Cila 22">Cila 22</option>
                    <option value="Cila 23">Cila 23</option>
                    <option value="Cila 24">Cila 24</option>
                    <option value="Cila 25">Cila 25</option>
                    <option value="Cila Babilon">Cila Babilon</option>
                </select>
            </div>

            <button class="btn-submit" style="background: #fd7e14; font-size: 1.2em;" onclick="generarCierreCarta()">📄 Generar Impresión</button>
        </div>

        {% elif view == 'reportes' and session.rol == 'admin' %}
        <div class="card-panel" style="width: 100%; max-width: 1000px; border-top: 6px solid #17a2b8;">
            <h2 class="titulo-panel">📊 Histórico de Transacciones</h2>
            <div style="display: flex; gap: 15px; margin-bottom: 25px; align-items: flex-end; flex-wrap: wrap; background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef;">
                <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 150px;"><label class="form-label">Desde Fecha:</label><input type="date" id="filtroInicio" class="form-control"></div>
                <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 150px;"><label class="form-label">Hasta Fecha:</label><input type="date" id="filtroFin" class="form-control"></div>
                <button class="btn-submit" style="background: #007bff; width: auto; margin-top: 0; padding: 12px 20px;" onclick="generarReporte()">🔍 Filtrar</button>
                <div style="flex-basis: 100%; height: 0;"></div>
                <button class="btn-submit" style="background: #28a745; width: auto; margin-top: 0; padding: 10px 15px;" onclick="exportarExcel()">📗 Exportar a Excel</button>
                <button class="btn-submit" style="background: #dc3545; width: auto; margin-top: 0; padding: 10px 15px;" onclick="exportarPDF()">📕 Exportar a PDF</button>
            </div>
            <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                <div style="flex:1; min-width: 200px; background: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #c3e6cb;"><h4 style="margin:0; color: #155724;">Total Ingresos</h4><h2 style="margin:10px 0 0 0; color: #28a745;" id="resumenMonto">Bs. 0,00</h2></div>
                <div style="flex:1; min-width: 200px; background: #e2e3e5; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #d6d8db;"><h4 style="margin:0; color: #383d41;">Operaciones Validadas</h4><h2 style="margin:10px 0 0 0; color: #495057;" id="resumenConteo">0</h2></div>
            </div>
            <div class="tabla-contenedor" style="max-height: 500px; overflow-y: auto;">
                <table class="tabla-datos" id="tablaReportes">
                    <thead><tr><th>Fecha y Hora</th><th>Referencia</th><th>Teléfono</th><th>Monto (Bs)</th><th>Sucursal</th><th>Estado</th></tr></thead>
                    <tbody id="bodyReportes"><tr><td colspan="6" style="text-align:center; padding: 20px;">Seleccione un rango de fechas y presione "Filtrar"</td></tr></tbody>
                </table>
            </div>
        </div>

        {% elif view == 'admin' and session.rol == 'admin' %}
        <div class="card-panel" style="width: 100%; max-width: 850px; border-top: 6px solid #ffc107;">
            <h2 class="titulo-panel">⚙️ Panel de Administración</h2>
            <div style="display: flex; gap: 25px; flex-wrap: wrap; align-items: flex-start;">
                <div style="flex: 1; min-width: 300px; background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                    <h3 style="margin-top: 0; color: #333;">Crear Nuevo Perfil</h3>
                    <form action="/crear_usuario" method="POST">
                        <div class="form-group"><label class="form-label">Nombre de Usuario</label><input type="text" name="usuario" class="form-control" required></div>
                        <div class="form-group"><label class="form-label">Contraseña</label><input type="text" name="password" class="form-control" required></div>
                        <div class="form-group"><label class="form-label">Rol del Sistema</label><select name="rol" class="form-control"><option value="cajero">Cajero</option><option value="admin">Administrador</option></select></div>
                        <div class="form-group"><label class="form-label">Sucursal Base</label><select name="sucursal" class="form-control"><option value="Cila 22">Cila 22</option><option value="Cila 23">Cila 23</option><option value="Cila 24">Cila 24</option><option value="Cila 25">Cila 25</option><option value="Cila Babilon">Cila Babilon</option></select></div>
                        <button type="submit" class="btn-submit" style="background: #333; margin-top: 5px;">Añadir Usuario</button>
                    </form>
                </div>
                <div style="flex: 1; min-width: 300px; display: flex; flex-direction: column; gap: 20px;">
                    <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border: 1px solid #ffeeba;">
                        <h3 style="margin-top: 0; color: #856404;">🔒 Clave de Cierre de Caja</h3>
                        <p style="font-size: 0.85em; color: #666; margin-bottom:15px;">Clave maestra para que los cajeros impriman el reporte.</p>
                        <form action="/configurar_clave" method="POST">
                            <div class="form-group" style="margin-bottom:10px;"><input type="text" name="clave_cierre" class="form-control" placeholder="Escriba nueva clave" required></div>
                            <button type="submit" class="btn-submit" style="background: #28a745; margin-top: 0; padding:10px;">Actualizar Clave</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        {% else %}
        <div class="form-section card-panel">
            <h2 class="titulo-panel">Validación de Pagos</h2>
            
            <div class="form-group">
                <label class="form-label">📍 Ubicación (Sucursal)</label>
                <select id="val_ubicacion" class="form-control">
                    <option value="Cila 22" {% if session.sucursal == 'Cila 22' %}selected{% endif %}>Cila 22</option>
                    <option value="Cila 23" {% if session.sucursal == 'Cila 23' %}selected{% endif %}>Cila 23</option>
                    <option value="Cila 24" {% if session.sucursal == 'Cila 24' %}selected{% endif %}>Cila 24</option>
                    <option value="Cila 25" {% if session.sucursal == 'Cila 25' %}selected{% endif %}>Cila 25</option>
                    <option value="Cila Babilon" {% if session.sucursal == 'Cila Babilon' %}selected{% endif %}>Cila Babilon</option>
                </select>
                {% if session.rol != 'admin' %}
                <div style="font-size: 0.75em; color: #0056b3; margin-top: 4px;">ℹ️ Tu sucursal principal está seleccionada. Cámbiala solo si estás de rotación.</div>
                {% endif %}
            </div>
            
            <div class="form-group"><label class="form-label">🏦 Entidad Emisora</label><select class="form-control" disabled><option>Banco BDV</option></select></div>
            <div class="form-group"><label class="form-label">💰 Monto (Bs.)</label><input type="text" id="val_monto" class="form-control" placeholder="Ej: 25,50"></div>
            <div class="form-group"><label class="form-label">🧾 Número de Referencia</label><input type="text" id="val_referencia" class="form-control" placeholder="Últimos 4 o 6 dígitos"></div>
            <button class="btn-submit" onclick="buscarPago()">Validar Pago</button>
        </div>

        <div class="result-section" id="resultadoBusqueda">
            <div class="placeholder-box">🔍<br>El resultado de la validación<br>aparecerá aquí</div>
        </div>
        {% endif %}
    </div>

    <script>
        const SESION_ROL = "{{ session.rol | default('cajero') }}";
    </script>

    <script>
        let todosLosPagos = [];

        async function cargarPagosFondo() {
            try { 
                const res = await fetch('/api/pagos'); 
                todosLosPagos = await res.json(); 
                if(document.getElementById('tablaReportes') && document.getElementById('filtroInicio').value !== "") {
                    generarReporte();
                }
            } catch(e) {}
        }
        setInterval(cargarPagosFondo, 3000);
        cargarPagosFondo();

        // --- CAJA ---
        function buscarPago() {
            if(!document.getElementById('val_monto')) return;
            const inputMonto = document.getElementById('val_monto');
            const inputRef = document.getElementById('val_referencia');
            const monto = inputMonto.value.trim().replace('.', ','); 
            const ref = inputRef.value.trim();
            const divRes = document.getElementById('resultadoBusqueda');

            if(ref === "") { divRes.innerHTML = "<div class='alerta-error'>⚠️ <b>Campo obligatorio:</b> Debes ingresar el N° de Referencia.</div>"; return; }
            inputMonto.value = ''; inputRef.value = '';

            const pagoEncontrado = todosLosPagos.find(p => p.ref.includes(ref) && (monto === "" ? true : p.monto.includes(monto)));

            if(pagoEncontrado) {
                if(pagoEncontrado.estado === 'verificado') {
                    divRes.innerHTML = `<div class="alerta-duplicado"><h3>🚨 PAGO DUPLICADO 🚨</h3><p>Este pago <b>ya fue procesado</b>.</p><p><b>📍 Lugar:</b> ${pagoEncontrado.ubicacion || 'Desconocido'}</p><p><b>🧾 Ref:</b> ${pagoEncontrado.ref}</p><p><b>💰 Monto:</b> Bs. ${pagoEncontrado.monto}</p></div>`;
                } else {
                    divRes.innerHTML = `
                        <div class="card">
                            <div class="header-card"><div class="monto">Bs. ${pagoEncontrado.monto}</div><div style="color: #007bff; font-weight: bold;">⏳ Pendiente</div></div>
                            <div class="datos-grid">
                                <div class="dato-item"><span class="dato-label">🏦 Entidad Emisora</span><span class="dato-valor">Banco BDV</span></div>
                                <div class="dato-item"><span class="dato-label">📅 Fecha de Pago</span><span class="dato-valor">${pagoEncontrado.fecha}</span></div>
                                <div class="dato-item"><span class="dato-label">📱 Teléfono Emisor</span><span class="dato-valor">${pagoEncontrado.telf}</span></div>
                                <div class="dato-item"><span class="dato-label">🧾 N° Referencia</span><span class="dato-valor ref">${pagoEncontrado.ref}</span></div>
                            </div>
                            <button class="btn-verificar" onclick="marcarVerificado('${pagoEncontrado.id}', this)">✔️ Confirmar Pago en Caja</button>
                        </div>`;
                }
            } else { divRes.innerHTML = `<div class='alerta-error'><strong>⚠️ Pago no encontrado.</strong><br><br>Verifique e intente de nuevo.</div>`; }
        }

        async function marcarVerificado(id_pago, boton) {
            const ubicacionSeleccionada = document.getElementById('val_ubicacion').value;
            boton.innerText = "Procesando..."; boton.style.background = "#888";
            await fetch('/api/verificar/' + id_pago, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ubicacion: ubicacionSeleccionada }) });
            document.getElementById('textoSucursal').innerText = "Despachado en: " + ubicacionSeleccionada;
            const pantalla = document.getElementById('pantallaExito');
            pantalla.style.display = 'flex';
            setTimeout(async () => {
                pantalla.style.display = 'none';
                await cargarPagosFondo(); 
                document.getElementById('resultadoBusqueda').innerHTML = `<div class="placeholder-box" style="border-color: #2ecc71; color: #2ecc71;">✅<br>Pago registrado correctamente<br>Listo para la próxima validación</div>`;
            }, 2500);
        }

        // --- AUTORIZACIÓN PARA TICKET 80mm ---
        function mostrarModalAutorizacion() {
            document.getElementById('clave_cierre_input').value = '';
            document.getElementById('modalAutorizacion').style.display = 'flex';
            document.getElementById('clave_cierre_input').focus();
        }

        async function procesarAutorizacion() {
            const clave = document.getElementById('clave_cierre_input').value;
            if(!clave) return alert("Debe ingresar la clave.");
            const res = await fetch('/api/validar_cierre', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clave: clave }) });
            const data = await res.json();
            if(data.status === 'ok') {
                document.getElementById('modalAutorizacion').style.display = 'none';
                imprimirCierre80mm();
            } else {
                alert("❌ CLAVE INCORRECTA. Acceso Denegado.");
            }
        }

        // --- CIERRE CAJEROS (TICKET 80mm) ---
        function imprimirCierre80mm() {
            let d = new Date();
            let dia = String(d.getDate()).padStart(2, '0'); let mes = String(d.getMonth() + 1).padStart(2, '0'); let ano = d.getFullYear();
            let fechaHoy = `${dia}/${mes}/${ano}`;

            let pagosHoy = todosLosPagos.filter(p => p.estado === 'verificado' && p.fecha.includes(fechaHoy));
            
            // RESTRICCIÓN ESTRICTA DE CAJERA: Solo imprimir los pagos de la sucursal que tiene seleccionada en pantalla
            let ubiCaja = document.getElementById('val_ubicacion');
            if (SESION_ROL !== 'admin' && ubiCaja) {
                let sucursalActual = ubiCaja.value;
                pagosHoy = pagosHoy.filter(p => p.ubicacion === sucursalActual);
            }

            let totalBs = 0; let desglose = {};
            pagosHoy.forEach(p => {
                let montoNumerico = parseFloat(p.monto.replace(/\./g, '').replace(',', '.'));
                if(!isNaN(montoNumerico)) { totalBs += montoNumerico; }
                let ubi = p.ubicacion || 'Sin especificar';
                if(!desglose[ubi]) desglose[ubi] = { cant: 0, bs: 0 };
                desglose[ubi].cant += 1; desglose[ubi].bs += montoNumerico;
            });

            let totalFormateado = totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            let ticketHTML = `<!DOCTYPE html><html><head><style>@page { margin: 0; } body { font-family: 'Courier New', Courier, monospace; width: 76mm; margin: 0 auto; padding: 10px 5px; color: #000; font-size: 13px; background: white;} .centrado { text-align: center; } .titulo { font-size: 18px; font-weight: bold; margin: 5px 0; } .subtitulo { font-size: 14px; margin: 3px 0; border-bottom: 1px dashed #000; padding-bottom: 5px; } .linea-punteada { border-top: 1px dashed #000; margin: 10px 0; } .fila { display: flex; justify-content: space-between; margin-bottom: 3px; } .bold { font-weight: bold; } .total-caja { font-size: 18px; border-top: 2px dashed #000; border-bottom: 2px dashed #000; padding: 10px 0; margin: 15px 0;} </style></head><body><div class="centrado"><img src="https://i.imgur.com/j4gWZ33.png" style="max-width: 150px; filter: grayscale(100%); margin-bottom: 10px;"><div class="titulo">REPORTE DE CAJA</div><div class="subtitulo">VALIDADOR BDV</div></div><div style="margin-top: 15px;"><div class="fila"><span>FECHA:</span> <span>${fechaHoy}</span></div><div class="fila"><span>HORA IMPRESIÓN:</span> <span>${d.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}</span></div></div><div class="linea-punteada"></div><div class="centrado bold" style="margin-bottom: 10px;">RESUMEN GENERAL</div><div class="fila"><span>Operaciones Validadas:</span> <span>${pagosHoy.length}</span></div><div class="total-caja"><div class="fila bold"><span>TOTAL INGRESOS:</span> <span>Bs. ${totalFormateado}</span></div></div><div class="linea-punteada"></div><div class="centrado bold" style="margin-bottom: 10px;">DESGLOSE POR SUCURSAL</div>`;

            for (let [ubi, datos] of Object.entries(desglose)) {
                let bsF = datos.bs.toLocaleString('es-VE', { minimumFractionDigits: 2 });
                ticketHTML += `<div class="fila"><span>${ubi} (${datos.cant} op):</span> <span>Bs. ${bsF}</span></div>`;
            }

            if(Object.keys(desglose).length === 0) ticketHTML += `<div class="centrado" style="margin-top: 10px;">No hay pagos verificados para esta caja hoy.</div>`;
            ticketHTML += `<div class="linea-punteada"></div><div class="centrado" style="margin-top: 15px; font-size: 11px;">* Fin del reporte *<br>Generado por CILA Pagos Automáticos<br>- - - - - - - - - - -</div></body></html>`;

            let iframe = document.getElementById('iframeTicket');
            iframe.contentWindow.document.open(); iframe.contentWindow.document.write(ticketHTML); iframe.contentWindow.document.close();
            setTimeout(() => { iframe.contentWindow.focus(); iframe.contentWindow.print(); }, 500);
        }

        // --- CIERRE ADMIN (TAMAÑO CARTA) ---
        function generarCierreCarta() {
            const fechaInput = document.getElementById('fechaCierreCarta').value;
            const sucursalFiltro = document.getElementById('sucursalCierreCarta').value;
            
            if(!fechaInput) return alert("Por favor, seleccione una fecha para generar el cierre.");

            // Convertir de YYYY-MM-DD a DD/MM/YYYY para comparar con Firebase
            let partes = fechaInput.split('-');
            let fechaFirebaseFormat = `${partes[2]}/${partes[1]}/${partes[0]}`;

            let pagosFiltrados = todosLosPagos.filter(p => p.estado === 'verificado' && p.fecha.includes(fechaFirebaseFormat));
            
            if (sucursalFiltro !== "Todas") {
                pagosFiltrados = pagosFiltrados.filter(p => p.ubicacion === sucursalFiltro);
            }

            let totalBs = 0;
            let filasHTML = "";
            
            pagosFiltrados.forEach((p, index) => {
                let montoNumerico = parseFloat(p.monto.replace(/\./g, '').replace(',', '.'));
                if(!isNaN(montoNumerico)) { totalBs += montoNumerico; }
                
                filasHTML += `
                    <tr>
                        <td style="text-align:center;">${index + 1}</td>
                        <td>${p.fecha.split(' - ')[1]}</td>
                        <td>${p.ref}</td>
                        <td>${p.telf}</td>
                        <td>${p.ubicacion || '-'}</td>
                        <td style="text-align:right;">Bs. ${p.monto}</td>
                    </tr>
                `;
            });

            let totalFormateado = totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            let fechaImpresion = new Date().toLocaleString('es-VE');

            let cartaHTML = `
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        @page { size: letter; margin: 15mm; }
                        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; margin:0; padding:0; }
                        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #003366; padding-bottom: 15px; margin-bottom: 25px; }
                        .logo { max-width: 200px; }
                        .titulo-doc { text-align: right; }
                        .titulo-doc h1 { margin: 0; color: #003366; font-size: 24px; text-transform: uppercase; }
                        .titulo-doc p { margin: 5px 0 0 0; color: #666; font-size: 14px; }
                        .info-box { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; margin-bottom: 25px; border-radius: 5px; }
                        .info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
                        .info-item { font-size: 13px; }
                        .info-item strong { color: #003366; }
                        table { width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 12px; }
                        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                        th { background-color: #003366; color: white; text-transform: uppercase; }
                        tr:nth-child(even) { background-color: #f2f2f2; }
                        .totales { display: flex; justify-content: flex-end; }
                        .caja-total { border: 2px solid #003366; padding: 15px 30px; text-align: right; background: #e8f4fd; border-radius: 5px; }
                        .caja-total h3 { margin: 0; color: #003366; font-size: 14px; text-transform: uppercase; }
                        .caja-total h2 { margin: 5px 0 0 0; color: #28a745; font-size: 24px; }
                        .footer { text-align: center; margin-top: 50px; font-size: 10px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <img src="https://i.imgur.com/j4gWZ33.png" class="logo">
                        <div class="titulo-doc">
                            <h1>Cierre de Caja Operativo</h1>
                            <p>Validador de Pagos BDV</p>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div class="info-grid">
                            <div class="info-item"><strong>Fecha de Cierre:</strong><br>${fechaFirebaseFormat}</div>
                            <div class="info-item"><strong>Sucursal Auditada:</strong><br>${sucursalFiltro}</div>
                            <div class="info-item"><strong>Generado por:</strong><br>Admin / ${fechaImpresion}</div>
                        </div>
                    </div>

                    ${pagosFiltrados.length === 0 ? '<p style="text-align:center; padding:50px; color:#666;">No se registraron transacciones verificadas en esta sucursal para la fecha seleccionada.</p>' : `
                    <table>
                        <thead>
                            <tr>
                                <th style="text-align:center; width: 40px;">#</th>
                                <th>Hora</th>
                                <th>N° Referencia</th>
                                <th>Teléfono Emisor</th>
                                <th>Sucursal Origen</th>
                                <th style="text-align:right;">Monto Validado</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${filasHTML}
                        </tbody>
                    </table>

                    <div class="totales">
                        <div class="caja-total">
                            <h3>Total Ingresos Consolidados</h3>
                            <h2>Bs. ${totalFormateado}</h2>
                            <p style="margin:5px 0 0 0; font-size:12px; color:#666;">Transacciones: ${pagosFiltrados.length}</p>
                        </div>
                    </div>
                    `}

                    <div class="footer">
                        Documento generado automáticamente por el Sistema Corporativo CILA.<br>
                        Este reporte incluye únicamente las transacciones marcadas como "Verificadas" y despachadas en tienda.
                    </div>
                </body>
                </html>
            `;

            let iframe = document.getElementById('iframeCarta');
            iframe.contentWindow.document.open();
            iframe.contentWindow.document.write(cartaHTML);
            iframe.contentWindow.document.close();
            setTimeout(() => { iframe.contentWindow.focus(); iframe.contentWindow.print(); }, 800);
        }

        // --- REPORTES ---
        function convertirFechaA_YYYYMMDD(fechaFirebase) {
            if(!fechaFirebase) return "";
            let parteFecha = fechaFirebase.split(' - ')[0]; 
            let partes = parteFecha.split('/');
            if(partes.length === 3) return `${partes[2]}-${partes[1]}-${partes[0]}`;
            return "";
        }

        function generarReporte() {
            const fechaIn = document.getElementById('filtroInicio').value; 
            const fechaFi = document.getElementById('filtroFin').value;
            const tbody = document.getElementById('bodyReportes');
            
            if(!fechaIn || !fechaFi) return alert("Seleccione Fecha Desde y Fecha Hasta.");

            let pagosFiltrados = todosLosPagos.filter(p => {
                let fechaTransaccion = convertirFechaA_YYYYMMDD(p.fecha);
                return fechaTransaccion >= fechaIn && fechaTransaccion <= fechaFi;
            });

            tbody.innerHTML = "";
            let totalBs = 0; let totalOp = 0;

            if(pagosFiltrados.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px;">No se encontraron transacciones.</td></tr>`;
            } else {
                pagosFiltrados.forEach(p => {
                    let esVerificado = p.estado === 'verificado';
                    let badgeColor = esVerificado ? 'badge-verde' : 'badge-amarillo';
                    let textoEstado = esVerificado ? 'Verificado' : 'Pendiente';
                    
                    if(esVerificado) {
                        let montoNumerico = parseFloat(p.monto.replace(/\./g, '').replace(',', '.'));
                        if(!isNaN(montoNumerico)) totalBs += montoNumerico;
                        totalOp++;
                    }

                    tbody.innerHTML += `<tr><td>${p.fecha}</td><td style="font-family:monospace; font-weight:bold;">${p.ref}</td><td>${p.telf}</td><td>Bs. ${p.monto}</td><td>${p.ubicacion || '-'}</td><td><span class="badge-tabla ${badgeColor}">${textoEstado}</span></td></tr>`;
                });
            }

            let totalFormateado = totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            document.getElementById('resumenMonto').innerText = `Bs. ${totalFormateado}`;
            document.getElementById('resumenConteo').innerText = totalOp;
        }

        function exportarExcel() {
            if(document.getElementById('bodyReportes').innerHTML.includes("Seleccione un rango")) return alert("Primero debe filtrar las fechas.");
            let wb = XLSX.utils.table_to_book(document.getElementById('tablaReportes'), {sheet:"Reporte CILA"});
            XLSX.writeFile(wb, 'Historial_CILA.xlsx');
        }

        function exportarPDF() {
            if(document.getElementById('bodyReportes').innerHTML.includes("Seleccione un rango")) return alert("Primero debe filtrar las fechas.");
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF('landscape'); 
            doc.setFontSize(18); doc.text("Reporte Histórico de Transacciones - CILA", 14, 20);
            doc.setFontSize(11);
            let desde = document.getElementById('filtroInicio').value; let hasta = document.getElementById('filtroFin').value;
            doc.text(`Período: ${desde} al ${hasta}`, 14, 28);
            let ingresos = document.getElementById('resumenMonto').innerText; doc.text(`Total Validados: ${ingresos}`, 14, 34);
            doc.autoTable({ html: '#tablaReportes', startY: 40, theme: 'grid', headStyles: { fillColor: [0, 51, 102] } });
            doc.save('Historial_CILA.pdf');
        }
    </script>
</body>
</html>
"""

# ==========================================
# RUTAS DE AUTENTICACIÓN Y PANELES
# ==========================================

@app.route('/')
def home():
    view = request.args.get('view', 'caja')
    return render_template_string(HTML_TEMPLATE, view=view)

@app.route('/login', methods=['POST'])
def do_login():
    usuario_form = request.form.get('usuario')
    password_form = request.form.get('password')

    if usuario_form == 'admin' and password_form == 'cila2026':
        session['usuario'] = 'Admin Maestro'
        session['rol'] = 'admin'
        session['sucursal'] = 'Todas'
        return redirect('/')

    try:
        res = requests.get(FIREBASE_USUARIOS)
        if res.status_code == 200 and res.json():
            usuarios_db = res.json()
            for id_fb, u_info in usuarios_db.items():
                if u_info.get('usuario') == usuario_form and u_info.get('password') == password_form:
                    session['usuario'] = u_info.get('usuario')
                    session['rol'] = u_info.get('rol')
                    session['sucursal'] = u_info.get('sucursal')
                    return redirect('/')
    except:
        pass
        
    return render_template_string(HTML_TEMPLATE, error="Usuario o contraseña incorrecta. Intente de nuevo.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') != 'admin': return redirect('/')
    nuevo_usuario = { "usuario": request.form.get('usuario'), "password": request.form.get('password'), "rol": request.form.get('rol'), "sucursal": request.form.get('sucursal') }
    requests.post(FIREBASE_USUARIOS, json=nuevo_usuario)
    return redirect('/?view=admin')

@app.route('/configurar_clave', methods=['POST'])
def configurar_clave():
    if session.get('rol') != 'admin': return redirect('/')
    nueva_clave = request.form.get('clave_cierre')
    requests.patch(FIREBASE_CONFIG, json={"clave_cierre": nueva_clave})
    return redirect('/?view=admin')

@app.route('/api/validar_cierre', methods=['POST'])
def validar_cierre():
    data = request.get_json() or {}
    clave_ingresada = data.get("clave", "")
    try:
        res = requests.get(FIREBASE_CONFIG)
        clave_real = res.json().get("clave_cierre", "1234") if res.status_code == 200 and res.json() else "1234"
        if clave_ingresada == clave_real: return jsonify({"status": "ok"})
        else: return jsonify({"status": "error"})
    except:
        return jsonify({"status": "error"})

# ==========================================
# RUTAS DE API Y WEBHOOK
# ==========================================

@app.route('/api/pagos')
def get_pagos():
    try:
        respuesta = requests.get(FIREBASE_PAGOS)
        if respuesta.status_code == 200 and respuesta.json():
            datos = respuesta.json()
            lista_pagos = []
            for id_firebase, info_pago in datos.items():
                info_pago['id'] = id_firebase
                if 'estado' not in info_pago: info_pago['estado'] = 'pendiente'
                lista_pagos.append(info_pago)
            lista_pagos.reverse()
            return jsonify(lista_pagos)
        return jsonify([])
    except:
        return jsonify([])

@app.route('/api/verificar/<id_pago>', methods=['POST'])
def verificar_pago(id_pago):
    try:
        data = request.get_json() or {}
        ubicacion_caja = data.get("ubicacion", "Desconocida")
        url_item = f"{FIREBASE_URL_BASE}/pagos/{id_pago}.json"
        requests.patch(url_item, json={"estado": "verificado", "ubicacion": ubicacion_caja})
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/webhook', methods=['POST'])
def webhook():
    texto = request.get_data(as_text=True)
    texto_limpio = texto.lower()
    if "pagomovil" not in texto_limpio and "pagomóvil" not in texto_limpio:
        return {"status": "ignorado"}, 200

    try:
        monto_match = re.search(r"bs\.?\s?([\d,.]+)", texto, re.IGNORECASE)
        monto = monto_match.group(1) if monto_match else "0,00"
        telf_match = re.search(r"del\s(04\d{2}[-]?\d{7})", texto, re.IGNORECASE)
        telf = telf_match.group(1).replace("-", "") if telf_match else "Desconocido"
        ref_match = re.search(r"ref:\s?(\d+)", texto, re.IGNORECASE)
        ref = ref_match.group(1)[-6:] if ref_match else "000000" 
        hora_venezuela = datetime.utcnow() - timedelta(hours=4)
        
        pago = { "monto": monto, "telf": telf, "ref": ref, "banco": "Banco BDV", "fecha": hora_venezuela.strftime("%d/%m/%Y - %I:%M %p"), "estado": "pendiente" }
        requests.post(FIREBASE_PAGOS, json=pago)
        return {"status": "ok"}, 200
    except Exception as e:
        return {"status": "error", "msg": str(e)}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
