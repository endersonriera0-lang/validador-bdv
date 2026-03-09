from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import re
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
# Pega tu enlace de Firebase aquí. ¡NO BORRES el /pagos.json del final!
FIREBASE_URL = "https://validador-bdv-default-rtdb.firebaseio.com/pagos.json"

# Plantilla Visual: Validador con Formulario
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Validador de Pagos BDV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #e9ecef; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 450px; }
        
        /* Estilos del Formulario */
        .formulario-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #0056b3; }
        .titulo-form { margin-top: 0; color: #0056b3; text-align: center; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; text-align: left; }
        .form-label { display: block; font-weight: bold; color: #555; margin-bottom: 5px; font-size: 0.85em; text-transform: uppercase; }
        .form-control { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background: #fdfdfd; }
        .form-control:focus { outline: none; border-color: #0056b3; }
        
        .btn-submit { background: #198754; color: white; width: 100%; padding: 14px; border: none; border-radius: 6px; font-size: 1.1em; font-weight: bold; cursor: pointer; margin-top: 10px; transition: 0.3s; }
        .btn-submit:hover { background: #157347; }

        /* Estilos de la Tarjeta de Resultado */
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 6px solid #ce1126; text-align: left; animation: fadeIn 0.5s; }
        .card.verificado { border-left-color: #2ecc71; background: #fafffa; }
        .header-card { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 12px; margin-bottom: 15px; }
        .monto { font-size: 1.6em; font-weight: 900; color: #1d1d1b; }
        
        .datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
        .dato-item { display: flex; flex-direction: column; }
        .dato-label { font-size: 0.75em; color: #777; text-transform: uppercase; font-weight: bold; }
        .dato-valor { font-size: 1em; color: #222; margin-top: 4px; font-weight: 500;}
        .ref { font-family: monospace; font-size: 1.1em; color: #0056b3; font-weight: bold; }
        
        .btn-verificar { width: 100%; background: #007bff; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; }
        .badge-verificado { color: #2ecc71; font-weight: bold; font-size: 1.1em; }
        .badge-ubicacion { text-align: center; color: #157347; font-weight: bold; margin-top: 10px; font-size: 0.9em; background: #e8f5e9; padding: 8px; border-radius: 5px; }

        .alerta-error { background: #ffeeba; padding: 15px; border-radius: 8px; border: 1px solid #ffc107; color: #856404; text-align: center; font-size: 0.95em; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        
        <div class="formulario-card">
            <h2 class="titulo-form">💳 Validación de Pagos</h2>
            
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
                <select id="val_banco" class="form-control" disabled>
                    <option value="BDV">Banco BDV</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">📱 Teléfono (Opcional)</label>
                <input type="text" id="val_telefono" class="form-control" placeholder="Ej: 04121234567">
            </div>

            <div class="form-group">
                <label class="form-label">🧾 Número de Referencia</label>
                <input type="text" id="val_referencia" class="form-control" placeholder="Últimos 4 o 6 dígitos">
            </div>

            <button class="btn-submit" onclick="buscarPago()">BUSCAR Y VALIDAR</button>
        </div>

        <div id="resultadoBusqueda"></div>

    </div>
    
    <script>
        let todosLosPagos = [];

        // La app descarga los pagos en el fondo silenciosamente
        async function cargarPagosFondo() {
            try {
                const res = await fetch('/api/pagos');
                todosLosPagos = await res.json();
            } catch(e) {}
        }
        setInterval(cargarPagosFondo, 3000);
        cargarPagosFondo();

        function buscarPago() {
            const telf = document.getElementById('val_telefono').value.trim();
            const ref = document.getElementById('val_referencia').value.trim();
            const divRes = document.getElementById('resultadoBusqueda');

            if(ref === "") {
                divRes.innerHTML = "<div class='alerta-error'>⚠️ Debes ingresar el N° de Referencia para buscar.</div>";
                return;
            }

            // Busca una coincidencia en la base de datos
            const pagoEncontrado = todosLosPagos.find(p => p.ref.includes(ref) && p.telf.includes(telf));

            if(pagoEncontrado) {
                divRes.innerHTML = `
                    <div class="card ${pagoEncontrado.estado === 'verificado' ? 'verificado' : ''}">
                        <div class="header-card">
                            <div class="monto">Bs. ${pagoEncontrado.monto}</div>
                            ${pagoEncontrado.estado === 'verificado' ? '<div class="badge-verificado">✅ Verificado</div>' : ''}
                        </div>
                        
                        <div class="datos-grid">
                            <div class="dato-item"><span class="dato-label">🏦 Entidad Emisora</span><span class="dato-valor">Banco BDV</span></div>
                            <div class="dato-item"><span class="dato-label">📅 Fecha de Pago</span><span class="dato-valor">${pagoEncontrado.fecha}</span></div>
                            <div class="dato-item"><span class="dato-label">📱 Teléfono Emisor</span><span class="dato-valor">${pagoEncontrado.telf}</span></div>
                            <div class="dato-item"><span class="dato-label">🧾 N° Referencia</span><span class="dato-valor ref">${pagoEncontrado.ref}</span></div>
                        </div>
                        
                        ${pagoEncontrado.estado !== 'verificado' 
                            ? `<button class="btn-verificar" onclick="marcarVerificado('${pagoEncontrado.id}', this)">✔️ Confirmar Pago en Caja</button>` 
                            : `<div class="badge-ubicacion">Despachado en: ${pagoEncontrado.ubicacion || 'Otra sucursal'}</div>`}
                    </div>
                `;
            } else {
                divRes.innerHTML = `<div class='alerta-error'><strong>⚠️ Pago no encontrado.</strong><br><br>El pago no se ha reflejado en el banco o los datos son incorrectos. Espere unos segundos e intente de nuevo.</div>`;
            }
        }

        async function marcarVerificado(id_pago, boton) {
            const ubicacionSeleccionada = document.getElementById('val_ubicacion').value;
            boton.innerText = "Procesando...";
            boton.style.background = "#888";
            
            // Enviamos a la base de datos el estado y la sucursal donde se verificó
            await fetch('/api/verificar/' + id_pago, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ubicacion: ubicacionSeleccionada })
            });
            
            await cargarPagosFondo(); // Recargamos
            buscarPago(); // Volvemos a mostrar la tarjeta actualizada
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
        # Obtenemos la ubicación desde el formulario web
        data = request.get_json() or {}
        ubicacion_caja = data.get("ubicacion", "Desconocida")

        base_url = FIREBASE_URL.replace('.json', '')
        url_item = f"{base_url}/{id_pago}.json"
        
        # Guardamos que fue verificado y en qué ubicación
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
    app.run(host='0.0.0.0', port=5000)
