from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import re

app = Flask(__name__)


# Base de datos en memoria (se borra si reinicias el servidor)
pagos = []

# Plantilla HTML integrada para no complicarnos con carpetas ahora
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
        .info { color: #555; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h2>💰 Pagos Recibidos BDV</h2>
        <div id="lista">Esperando pagos...</div>
    </div>
    <script>
        async function actualizar() {
            const res = await fetch('/api/pagos');
            const data = await res.json();
            document.getElementById('lista').innerHTML = data.map(p => `
                <div class="card">
                    <div class="monto">Bs. ${p.monto}</div>
                    <div class="info"><b>Ref:</b> ...${p.ref}</div>
                    <div class="info"><b>Telf:</b> ${p.telf}</div>
                    <div class="info" style="font-size:0.7em">${p.fecha}</div>
                </div>
            `).join('') || "No hay pagos registrados aún";
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

@app.route('/webhook', methods=['POST'])
def webhook():
    texto = request.get_data(as_text=True)
    
    # 1. IMPRIMIMOS EL MENSAJE EN RENDER PARA PODER VERLO
    print("--- MENSAJE RECIBIDO DESDE EL TELÉFONO ---")
    print(texto)
    print("------------------------------------------")
    
    # Pasamos todo a minúsculas para que no importen las tildes ni mayúsculas
    texto_limpio = texto.lower()

    # Filtro: Si no dice pagomovil (con o sin tilde), lo ignoramos
    if "pagomovil" not in texto_limpio and "pagomóvil" not in texto_limpio:
        print("Ignorado: El texto no parece del banco.")
        return {"status": "ignorado"}, 200

    try:
        # Extraemos el monto (Ignorando mayúsculas)
        monto_match = re.search(r"bs\.?\s?([\d,.]+)", texto, re.IGNORECASE)
        monto = monto_match.group(1) if monto_match else "0,00"

        # Extraemos el teléfono
        telf_match = re.search(r"del\s(04\d{2}[-]?\d{7})", texto, re.IGNORECASE)
        telf = telf_match.group(1).replace("-", "") if telf_match else "Desconocido"

        # Extraemos la Referencia
        ref_match = re.search(r"ref:\s?(\d+)", texto, re.IGNORECASE)
        ref = ref_match.group(1)[-6:] if ref_match else "000000" 
        
        pago = {
            "monto": monto,
            "telf": telf,
            "ref": ref,
            "fecha": datetime.now().strftime("%H:%M:%S - %d/%m")
        }
        pagos.insert(0, pago)
        print("¡PAGO REGISTRADO CON ÉXITO!", pago) # Aviso de éxito
        return {"status": "ok"}, 200
        
    except Exception as e:
        print(f"Error sacando los datos: {e}")
        return {"status": "error", "msg": str(e)}, 200
