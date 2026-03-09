from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import re
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
# Pega tu enlace de Firebase aquí. ¡NO BORRES el /pagos.json del final!
FIREBASE_URL = "https://validador-bdv-default-rtdb.firebaseio.com/pagos.json"

# Plantilla Visual
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Panel de Pagos BDV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; text-align: center; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 15px; margin: 10px 0; border-radius: 10px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 6px solid #ce1126; text-align: left; }
        .monto { font-size: 1.2em; font-weight: bold; color: #2ecc71; }
        .info { color: #555; font-size: 0.9em; margin-top: 3px; }
        .ref { font-family: monospace; font-size: 1.1em; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h2>💰 Pagos Recibidos BDV</h2>
        <div id="lista">Esperando conexión con la base de datos...</div>
    </div>
    <script>
        async function actualizar() {
            try {
                const res = await fetch('/api/pagos');
                const data = await res.json();
                if(data.length === 0) {
                    document.getElementById('lista').innerHTML = "No hay pagos registrados aún en la Base de Datos.";
                    return;
                }
                document.getElementById('lista').innerHTML = data.map(p => `
                    <div class="card">
                        <div class="monto">Bs. ${p.monto}</div>
                        <div class="info"><b>Ref:</b> <span class="ref">${p.ref}</span></div>
                        <div class="info"><b>Telf:</b> ${p.telf}</div>
                        <div class="info" style="font-size:0.7em; margin-top:8px; color:#999;">${p.fecha}</div>
                    </div>
                `).join('');
            } catch(e) {
                console.log("Esperando conexión...");
            }
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
        # Aquí la app lee los datos guardados en Firebase
        respuesta = requests.get(FIREBASE_URL)
        if respuesta.status_code == 200 and respuesta.json():
            datos = respuesta.json()
            # Convertimos los datos a una lista y la invertimos para ver los nuevos arriba
            lista_pagos = list(datos.values())
            lista_pagos.reverse()
            return jsonify(lista_pagos)
        return jsonify([])
    except:
        return jsonify([])

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
        
        # Ajustamos la hora para Venezuela (Restamos 4 horas a la hora mundial)
        hora_venezuela = datetime.utcnow() - timedelta(hours=4)
        
        pago = {
            "monto": monto,
            "telf": telf,
            "ref": ref,
            "fecha": hora_venezuela.strftime("%H:%M:%S - %d/%m/%Y")
        }
        
        # Guardamos el pago para siempre en la Base de Datos
        requests.post(FIREBASE_URL, json=pago)
        
        return {"status": "ok"}, 200
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
