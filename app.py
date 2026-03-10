from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import re
import requests
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
FIREBASE_URL = "https://validador-bdv-default-rtdb.firebaseio.com/pagos.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Validador Corporativo BDV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        /* 🎨 DISEÑO CORPORATIVO CILA 🎨 */
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; 
            display: flex; flex-direction: column; align-items: center; min-height: 100vh;
            
            /* --- FONDO DE PANTALLA --- */
            background-image: url('https://i.imgur.com/rgsa5XH.png');
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        
        /* Capa oscura translúcida para legibilidad */
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 40, 80, 0.75); z-index: -1; backdrop-filter: blur(2px); }
        
        /* --- LOGO CORPORATIVO --- */
        .logo-container { text-align: center; margin-bottom: 30px; margin-top: 10px; width: 100%; z-index: 1;}
        .logo-container img { max-width: 200px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.3)); }

        /* CONTENEDOR LATERAL (FLEXBOX) */
        .main-wrapper {
            display: flex; flex-direction: row; gap: 30px; justify-content: center;
            align-items: flex-start; width: 100%; max-width: 1000px; z-index: 1;
        }

        /* --- FORMULARIO (IZQUIERDA) --- */
        .form-section { flex: 1; max-width: 450px; width: 100%; }
        
        .formulario-card { background: rgba(255, 255, 255, 0.95); padding: 30px 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border-top: 6px solid #198754; backdrop-filter: blur(5px); }
        .titulo-form { margin-top: 0; color: #003366; text-align: center; margin-bottom: 20px; font-size: 1.4em; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;}
        
        .form-group { margin-bottom: 15px; text-align: left; }
        .form-label { display: block; font-weight: bold; color: #444; margin-bottom: 6px; font-size: 0.85em; text-transform: uppercase; }
        .form-control { width: 100%; padding: 12px; border: 1px solid #c0c0c0; border-radius: 8px; font-size: 15px; box-sizing: border-box; background: #fff; transition: 0.3s;}
        .form-control:focus { outline: none; border-color: #198754; box-shadow: 0 0 0 3px rgba(25,135,84,0.1); }
        
        .btn-submit { background: #198754; color: white; width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; margin-top: 15px; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 6px rgba(25, 135, 84, 0.3);}
        .btn-submit:hover { background: #146c43; transform: translateY(-2px); }

        /* --- RESULTADO (DERECHA) --- */
        .result-section { flex: 1; max-width: 500px; width: 100%; }
        .placeholder-box { background: rgba(255, 255, 255, 0.1); border: 2px dashed rgba(255, 255, 255, 0.4); border-radius: 15px; padding: 40px 20px; text-align: center; color: rgba(255, 255, 255, 0.7); font-weight: bold; }

        /* Estilos del Recibo Estilo Módulo Profesional */
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border-left: 8px solid #ce1126; text-align: left; animation: slideIn 0.4s ease-out; }
        .header-card { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px dashed #eee; padding-bottom: 15px; margin-bottom: 15px; }
        .monto { font-size: 1.8em; font-weight: 900; color: #1d1d1b; }
        
        .datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .dato-item { display: flex; flex-direction: column; }
        .dato-label { font-size: 0.75em; color: #888; text-transform: uppercase; font-weight: bold; }
        .dato-valor { font-size: 1.05em; color: #222; margin-top: 4px; font-weight: 600;}
        .ref { font-family: monospace; font-size: 1.2em; color: #0056b3; font-weight: bold; }
        
        .btn-verificar { width: 100%; background: #007bff; color: white; border: none; padding: 14px; border-radius: 8px; font-size: 1.05em; font-weight: bold; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 6px rgba(0, 123, 255, 0.3); transition: 0.3s;}
        .btn-verificar:hover { background: #0056b3; }
        
        /* ALERTA DE PAGO DUPLICADO (ESTILO CILA) */
        .alerta-duplicado { background: #ffe3e3; padding: 25px; border-radius: 12px; border: 3px solid #ce1126; color: #900000; text-align: center; animation: slideIn 0.3s; box-shadow: 0 10px 20px rgba(206, 17, 38, 0.3);}
        .alerta-duplicado h3 { margin-top: 0; font-size: 1.5em; text-transform: uppercase; }
        
        .alerta-error { background: #ffeeba; padding: 15px; border-radius: 8px; border: 1px solid #ffc107; color: #856404; text-align: center; font-size: 0.95em; animation: slideIn 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.2);}
        
        /* --------------------------------------------------- */
        /* ANIMACIÓN GIGANTE DE ÉXITO                          */
        /* --------------------------------------------------- */
        .pantalla-exito {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85); z-index: 9999;
            display: none; justify-content: center; align-items: center;
            backdrop-filter: blur(8px);
        }
        .caja-exito {
            background: #2ecc71; padding: 40px 60px; border-radius: 20px;
            text-align: center; color: white; border: 5px solid white;
            box-shadow: 0 20px 50px rgba(46, 204, 113, 0.5);
            animation: estallar 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex; flex-direction: column; align-items: center;
        }
        .icono-exito { font-size: 90px; margin-bottom: 10px; line-height: 1;}
        .texto-exito { font-size: 38px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;}
        .subtexto-exito { font-size: 18px; margin-top: 10px; opacity: 0.9; font-weight: bold;}
        
        @keyframes estallar { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

        @media (max-width: 850px) {
            .main-wrapper { flex-direction: column; align-items: center; gap: 20px; }
            .placeholder-box { display: none; }
            .caja-exito { padding: 30px 20px; width: 85%; box-sizing: border-box;}
            .texto-exito { font-size: 28px; }
        }
    </style>
</head>
<body>
    <div class="overlay"></div>

    <div id="pantallaExito" class="pantalla-exito">
        <div class="caja-exito">
            <div class="icono-exito">✅</div>
            <div class="texto-exito">¡PAGO VERIFICADO!</div>
            <div id="textoSucursal" class="subtexto-exito">Procesado con éxito</div>
        </div>
    </div>
    
    <div class="logo-container">
        <img src="https://i.imgur.com/o5Q6bxd.png" alt="Logo Cila">
    </div>

    <div class="main-wrapper">
        <div class="form-section">
            <div class="formulario-card">
                <h2 class="titulo-form">Validación de Pagos</h2>
                
                <div class="form-group">
                    <label class="form-label">📍 Ubicación (Sucursal)</label>
                    <select id="val_ubicacion" class="form-control">
                        <option value="Cila 22">Cila 22</option>
                        <option value="Cila 23">Cila 23</option>
                        <option value="Cila 24">Cila 24</option>
                        <option value="Cila 25">Cila 25</option>
                        <option value="Cila Babilon">Cila Babilon</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">🏦 Entidad Emisora</label>
                    <select id="val_banco" class="form-control" disabled><option value="BDV">Banco BDV</option></select>
                </div>
                <div class="form-group">
                    <label class="form-label">💰 Monto (Bs.)</label>
                    <input type="text" id="val_monto" class="form-control" placeholder="Ej: 25,50">
                </div>
                <div class="form-group">
                    <label class="form-label">🧾 Número de Referencia</label>
                    <input type="text" id="val_referencia" class="form-control" placeholder="Últimos 4 o 6 dígitos">
                </div>
                <button class="btn-submit" onclick="buscarPago()">Validar Pago</button>
            </div>
        </div>

        <div class="result-section" id="resultadoBusqueda">
            <div class="placeholder-box">🔍<br>El resultado de la validación<br>aparecerá aquí</div>
        </div>
    </div>
    
    <script>
        let todosLosPagos = [];

        async function cargarPagosFondo() {
            try {
                const res = await fetch('/api/pagos');
                todosLosPagos = await res.json();
            } catch(e) {}
        }
        setInterval(cargarPagosFondo, 3000);
        cargarPagosFondo();

        function buscarPago() {
            const inputMonto = document.getElementById('val_monto');
            const inputRef = document.getElementById('val_referencia');
            
            const monto = inputMonto.value.trim().replace('.', ','); 
            const ref = inputRef.value.trim();
            const divRes = document.getElementById('resultadoBusqueda');

            if(ref === "") {
                divRes.innerHTML = "<div class='alerta-error'>⚠️ <b>Campo obligatorio:</b> Debes ingresar el N° de Referencia.</div>";
                return;
            }

            // LIMPIEZA AUTOMÁTICA DE LOS CAMPOS
            inputMonto.value = '';
            inputRef.value = '';

            const pagoEncontrado = todosLosPagos.find(p => {
                let coincideRef = p.ref.includes(ref);
                let coincideMonto = (monto === "") ? true : p.monto.includes(monto);
                return coincideRef && coincideMonto;
            });

            if(pagoEncontrado) {
                if(pagoEncontrado.estado === 'verificado') {
                    // ESCUDO ANTI-FRAUDE: ALERTA DE PAGO DUPLICADO
                    divRes.innerHTML = `
                        <div class="alerta-duplicado">
                            <h3>🚨 PAGO DUPLICADO 🚨</h3>
                            <p>Este pago <b>ya fue procesado y validado</b> anteriormente en el sistema.</p>
                            <br>
                            <p><b>📍 Lugar de despacho:</b> ${pagoEncontrado.ubicacion || 'Desconocido'}</p>
                            <p><b>🧾 Referencia:</b> ${pagoEncontrado.ref}</p>
                            <p><b>💰 Monto:</b> Bs. ${pagoEncontrado.monto}</p>
                            <br>
                            <i style="color: #600; font-size: 0.9em;">⚠️ No despache mercancía bajo esta referencia nuevamente.</i>
                        </div>
                    `;
                } else {
                    // PAGO NUEVO (LISTO PARA VERIFICAR)
                    divRes.innerHTML = `
                        <div class="card">
                            <div class="header-card">
                                <div class="monto">Bs. ${pagoEncontrado.monto}</div>
                                <div style="color: #007bff; font-weight: bold;">⏳ Pendiente</div>
                            </div>
                            <div class="datos-grid">
                                <div class="dato-item"><span class="dato-label">🏦 Entidad Emisora</span><span class="dato-valor">Banco BDV</span></div>
                                <div class="dato-item"><span class="dato-label">📅 Fecha de Pago</span><span class="dato-valor">${pagoEncontrado.fecha}</span></div>
                                <div class="dato-item"><span class="dato-label">📱 Teléfono Emisor</span><span class="dato-valor">${pagoEncontrado.telf}</span></div>
                                <div class="dato-item"><span class="dato-label">🧾 N° Referencia</span><span class="dato-valor ref">${pagoEncontrado.ref}</span></div>
                            </div>
                            
                            <button class="btn-verificar" onclick="marcarVerificado('${pagoEncontrado.id}', this)">✔️ Confirmar Pago en Caja</button>
                        </div>
                    `;
                }
            } else {
                divRes.innerHTML = `<div class='alerta-error'><strong>⚠️ Pago no encontrado.</strong><br><br>El pago no se ha reflejado en el banco o los datos son incorrectos. Verifique e intente de nuevo.</div>`;
            }
        }

        async function marcarVerificado(id_pago, boton) {
            const ubicacionSeleccionada = document.getElementById('val_ubicacion').value;
            
            boton.innerText = "Procesando...";
            boton.style.background = "#888";
            
            await fetch('/api/verificar/' + id_pago, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ubicacion: ubicacionSeleccionada })
            });
            
            document.getElementById('textoSucursal').innerText = "Despachado en: " + ubicacionSeleccionada;
            const pantalla = document.getElementById('pantallaExito');
            pantalla.style.display = 'flex';
            
            setTimeout(async () => {
                pantalla.style.display = 'none';
                await cargarPagosFondo(); 
                
                // DEJA LA CAJA LIMPIA
                document.getElementById('resultadoBusqueda').innerHTML = `
                    <div class="placeholder-box" style="border-color: #2ecc71; color: #2ecc71;">
                        ✅<br>Pago registrado correctamente<br>Listo para la próxima validación
                    </div>
                `;
            }, 2500);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/pagos')
def get_pagos():
    try:
        respuesta = requests.get(FIREBASE_URL)
        if respuesta.status_code == 200 and respuesta.json():
            datos = respuesta.json()
            lista_pagos = []
            for id_firebase, info_pago in datos.items():
                info_pago['id'] = id_firebase
                if 'estado' not in info_pago:
                    info_pago['estado'] = 'pendiente'
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

        base_url = FIREBASE_URL.replace('.json', '')
        url_item = f"{base_url}/{id_pago}.json"
        
        requests.patch(url_item, json={
            "estado": "verificado",
            "ubicacion": ubicacion_caja
        })
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
        
        pago = {
            "monto": monto,
            "telf": telf,
            "ref": ref,
            "banco": "Banco BDV",
            "fecha": hora_venezuela.strftime("%d/%m/%Y - %I:%M %p"),
            "estado": "pendiente"
        }
        
        requests.post(FIREBASE_URL, json=pago)
        return {"status": "ok"}, 200
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
