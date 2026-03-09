from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import re
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
# Pega tu enlace de Firebase aquí. ¡NO BORRES el /pagos.json del final!
FIREBASE_URL = "https://validador-bdv-default-rtdb.firebaseio.com/pagos.json"

# Plantilla Visual: Módulo Profesional
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Panel de Pagos BDV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #e9ecef; padding: 20px; text-align: center; }
        .container { max-width: 550px; margin: auto; }
        .buscador { width: 95%; padding: 14px; margin-bottom: 20px; border-radius: 8px; border: 2px solid #ddd; font-size: 16px; outline: none; transition: border-color 0.3s;}
        .buscador:focus { border-color: #007bff; }
        
        /* Diseño del Módulo de Pago */
        .card { background: white; padding: 20px; margin: 15px 0; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-top: 5px solid #ce1126; text-align: left; transition: all 0.3s; }
        .card.verificado { border-top-color: #2ecc71; background: #fafffa; }
        
        .header-card { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 12px; margin-bottom: 15px; }
        .monto { font-size: 1.6em; font-weight: 900; color: #1d1d1b; }
        
        /* Cuadrícula de Datos */
        .datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
        .dato-item { display: flex; flex-direction: column; }
        .dato-label { font-size: 0.75em; color: #777; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px; }
        .dato-valor { font-size: 1em; color: #222; margin-top: 4px; font-weight: 500;}
        .ref { font-family: monospace; font-size: 1.1em; color: #0056b3; font-weight: bold; }
        
        /* Botones y Etiquetas */
        .btn-verificar { width: 100%; background: #007bff; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; transition: background 0.3s; }
        .btn-verificar:hover { background: #0056b3; }
        .badge-verificado { color: #2ecc71; font-weight: bold; font-size: 1.2em; display: flex; align-items: center; gap: 5px;}
    </style>
</head>
<body>
    <div class="container">
        <h2 style="color: #333; margin-bottom: 25px;">💻 Módulo de Caja BDV</h2>
        <input type="text" id="inputBusqueda" class="buscador" onkeyup="filtrarPagos()" placeholder="🔍 Buscar N° de Referencia o Monto...">
        <div id="lista">Conectando con la base de datos...</div>
    </div>
    
    <script>
        let todosLosPagos = [];

        async function actualizar() {
            try {
                const res = await fetch('/api/pagos');
                todosLosPagos = await res.json();
                filtrarPagos(); 
            } catch(e) {
                console.log("Esperando conexión...");
            }
        }

        function filtrarPagos() {
            const texto = document.getElementById('inputBusqueda').value.toLowerCase();
            const divLista = document.getElementById('lista');
            
            if(todosLosPagos.length === 0) {
                divLista.innerHTML = "<p style='color:#777;'>No hay pagos registrados aún en la Base de Datos.</p>";
                return;
            }

            const pagosFiltrados = todosLosPagos.filter(p => 
                p.ref.includes(texto) || p.monto.includes(texto)
            );

            divLista.innerHTML = pagosFiltrados.map(p => `
                <div class="card ${p.estado === 'verificado' ? 'verificado' : ''}">
                    
                    <div class="header-card">
                        <div class="monto">Bs. ${p.monto}</div>
                        ${p.estado === 'verificado' ? '<div class="badge-verificado">✅ Verificado</div>' : ''}
                    </div>
                    
                    <div class="datos-grid">
                        <div class="dato-item">
                            <span class="dato-label">🏦 Entidad Emisora</span>
                            <span class="dato-valor">Banco BDV</span>
                        </div>
                        <div class="dato-item">
                            <span class="dato-label">📅 Fecha de Pago</span>
                            <span class="dato-valor">${p.fecha}</span>
                        </div>
                        <div class="dato-item">
                            <span class="dato-label">📱 Teléfono Emisor</span>
                            <span class="dato-valor">${p.telf}</span>
                        </div>
                        <div class="dato-item">
                            <span class="dato-label">🧾 N° Referencia</span>
                            <span class="dato-valor ref">${p.ref}</span>
                        </div>
                    </div>
                    
                    ${p.estado !== 'verificado' 
                        ? `<button class="btn-verificar" onclick="marcarVerificado('${p.id}', this)">Marcar Pago como Verificado</button>` 
                        : ''}
                </div>
            `).join('');
        }

        async function marcarVerificado(id_pago, boton) {
            boton.innerText = "Procesando...";
            boton.style.background = "#888";
            
            await fetch('/api/verificar/' + id_pago, { method: 'POST' });
            actualizar(); 
        }

        setInterval(actualizar, 3000);
        actualizar();
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
        base_url = FIREBASE_URL.replace('.json', '')
        url_item = f"{base_url}/{id_pago}.json"
        requests.patch(url_item, json={"estado": "verificado"})
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
            "banco": "Banco BDV", # <-- FIJADO A BANCO BDV
            "fecha": hora_venezuela.strftime("%d/%m/%Y - %I:%M %p"),
            "estado": "pendiente"
        }
        
        requests.post(FIREBASE_URL, json=pago)
        return {"status": "ok"}, 200
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
