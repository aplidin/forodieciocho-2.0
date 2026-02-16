from flask import Flask, render_template_string, request
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuración potente del scraper
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

@app.route('/')
def home():
    hilos_encontrados = []
    debug_info = {}
    
    start_page = request.args.get('start', 1, type=int)
    if start_page < 1: start_page = 1
    
    try:
        url = f"https://www.forocoches.com/foro/forumdisplay.php?f=2&order=desc&page={start_page}"
        
        # Petición con Cloudscraper
        response = scraper.get(url, timeout=10)
        
        # Guardar datos técnicos para el diagnóstico
        debug_info['status'] = response.status_code
        debug_info['url'] = url
        
        # Intentamos decodificar
        content = response.text
        debug_info['preview'] = content[:500].replace('<', '&lt;') # Ver los primeros 500 caracteres
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ver cuántos hilos detecta en total (aunque no sean +18)
        links = soup.find_all('a', id=lambda x: x and x.startswith('thread_title_'))
        debug_info['hilos_detectados'] = len(links)
        
        if len(links) > 0:
            for link in links:
                titulo_raw = link.get_text().strip()
                titulo_safe = titulo_raw.replace('"', "'")
                url_hilo = "https://www.forocoches.com/foro/" + link['href']
                
                if "+18" in titulo_raw:
                    hilos_encontrados.append({
                        'titulo': titulo_safe, 
                        'url': url_hilo, 
                        'pagina': start_page
                    })
        else:
            # Si no hay hilos, puede que estemos en la página de Cloudflare
            if "Just a moment" in content or "Cloudflare" in content:
                debug_info['error'] = "Detectado bloqueo Cloudflare (Captcha)"
            else:
                debug_info['error'] = "HTML descargado pero sin hilos (¿Cambio de estructura?)"

    except Exception as e:
        debug_info['status'] = "Error Python"
        debug_info['preview'] = str(e)
        debug_info['error'] = f"Excepción: {str(e)}"

    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diagnóstico Vercel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: monospace; padding: 20px; background: #121212; color: #e0e0e0; }
            .card { background: #1e1e1e; border: 1px solid #333; margin-bottom: 20px; }
            .debug-box { background: #000; color: #0f0; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 0.8rem; border: 1px solid #333; }
            .status-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; }
            .ok { background: #198754; color: white; }
            .fail { background: #dc3545; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">🛠️ Panel de Diagnóstico</h1>
            
            {% if hilos %}
                <div class="alert alert-success">✅ ¡ÉXITO! Se encontraron {{ hilos|length }} hilos +18.</div>
                <ul>
                {% for hilo in hilos %}
                    <li><a href="{{ hilo.url }}" target="_blank" style="color: #4da3ff">{{ hilo.titulo }}</a></li>
                {% endfor %}
                </ul>
            {% else %}
                <div class="alert alert-danger">❌ FALLO: No se encontraron hilos +18.</div>
            {% endif %}

            <div class="card">
                <div class="card-header fw-bold">DATOS TÉCNICOS</div>
                <div class="card-body">
                    <p><strong>Estado HTTP:</strong> 
                        <span class="status-badge {{ 'ok' if debug.status == 200 else 'fail' }}">{{ debug.status }}</span>
                    </p>
                    <p><strong>Hilos Totales Detectados:</strong> {{ debug.hilos_detectados|default(0) }}</p>
                    <p><strong>Error Interno:</strong> {{ debug.error|default('Ninguno aparente') }}</p>
                    
                    <label class="fw-bold mt-3">Lo que ve el servidor (HTML Preview):</label>
                    <pre class="debug-box">{{ debug.preview }}</pre>
                </div>
            </div>
            
            <div class="text-center mt-3">
                <a href="/?start={{ start + 10 }}" class="btn btn-outline-light">Probar siguiente página</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, hilos=hilos_encontrados, debug=debug_info, start=start_page)
