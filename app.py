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
        .header-card { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 12px; margin-bottom:
