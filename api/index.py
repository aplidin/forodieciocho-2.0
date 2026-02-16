from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Cabeceras más completas para parecer un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "DNT": "1"
}

@app.route('/')
def home():
    hilos_encontrados = []
    debug_info = {} # Variable para guardar errores
    
    start_page = request.args.get('start', 1, type=int)
    if start_page < 1: start_page = 1
    
    try:
        url = f"https://www.forocoches.com/foro/forumdisplay.php?f=2&order=desc&page={start_page}"
        
        # Petición
        response = requests.get(url, headers=HEADERS, timeout=5)
        
        # Guardamos info para el diagnóstico
        debug_info['status'] = response.status_code
        debug_info['url'] = url
        
        # Decodificamos
        content = response.content.decode('utf-8', errors='ignore')
        
        # Guardamos un trozo del HTML para ver si es Cloudflare
        debug_info['preview'] = content[:500].replace('<', '&lt;') 
        
        if response.status_code == 200:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Buscamos enlaces
            links = soup.find_all('a', id=lambda x: x and x.startswith('thread_title_'))
            debug_info['enlaces_totales'] = len(links) # Cuántos hilos ve en total (sin filtrar)
            
            for link in links:
                titulo_raw = link.get_text().strip()
                titulo_safe = titulo_raw.replace('"', "'")
                url_hilo = "https://www.forocoches.com/foro/" + link['href']
                
                # FILTRO +18
                if "+18" in titulo_raw:
                    hilos_encontrados.append({
                        'titulo': titulo_safe, 
                        'url': url_hilo, 
                        'pagina': start_page
                    })
        else:
            debug_info['error'] = "El servidor no respondió OK (200)"

    except Exception as e:
        debug_info['status'] = "Error Python"
        debug_info['preview'] = str(e)

    # HTML simple para ver los datos
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diagnóstico FC</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: monospace; padding: 20px; background: #f4f4f4; }
            .card { margin-bottom: 20px; }
            .debug-box { background: #333; color: #0f0; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 0.8rem;}
            .thread-link { display: block; padding: 10px; background: white; margin-bottom: 5px; text-decoration: none; color: #333; border-left: 4px solid #f60; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">🕵️ Panel de Diagnóstico</h1>
            
            {% if hilos %}
                <h3 class="text-success">✅ ¡Funciona! Se encontraron {{ hilos|length }} hilos +18</h3>
                <div class="mb-4">
                {% for hilo in hilos %}
                    <a href="{{ hilo.url }}" target="_blank" class="thread-link">{{ hilo.titulo }}</a>
                {% endfor %}
                </div>
            {% else %}
                <h3 class="text-danger">❌ No se encontraron hilos +18</h3>
                <p>Mira los datos técnicos abajo para saber por qué.</p>
            {% endif %}

            <div class="card shadow-sm">
                <div class="card-header bg-dark text-white fw-bold">DATOS TÉCNICOS (Compárteme esto)</div>
                <div class="card-body">
                    <ul>
                        <li><strong>Estado HTTP:</strong> {{ debug.status }}</li>
                        <li><strong>URL intentada:</strong> {{ debug.url }}</li>
                        <li><strong>Hilos totales detectados (sin filtrar):</strong> {{ debug.enlaces_totales|default(0) }}</li>
                    </ul>
                    
                    <label class="fw-bold">Lo que Vercel ve (Primeros 500 caracteres):</label>
                    <pre class="debug-box">{{ debug.preview }}</pre>
                </div>
            </div>
            
            <div class="text-center mt-3">
                <a href="/?start={{ start + 10 }}" class="btn btn-primary">Probar siguiente página</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, hilos=hilos_encontrados, debug=debug_info, start=start_page)
