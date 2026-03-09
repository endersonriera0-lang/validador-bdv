from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import re

app = Flask(__name__)

# Base de datos en memoria
pagos = []

# Plantilla Visual (El panel de control que tú ves)
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
        <div id="lista">Esperando pagos...</div>
    </div>
    <script>
        async function actualizar() {
            try {
                const res = await fetch('/api/pagos');
                const data = await res.json();
                if(data.length === 0) {
                    document.getElementById('lista').innerHTML = "No hay pagos registrados aún";
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

# Ruta principal (Muestra la página web)
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# Ruta que le da los datos a la página web
@app.route('/api/pagos')
def get_pagos():
    return jsonify(pagos)

# Ruta que recibe los datos desde MacroDroid
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
        
        pago = {
            "monto": monto,
            "telf": telf,
            "ref": ref,
            "fecha": datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
        }
        pagos.insert(0, pago) # Añade el pago más reciente arriba
        print("PAGO EXITOSO:", pago)
        return {"status": "ok"}, 200
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
