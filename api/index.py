from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- PEGA AQUÍ TU USER-AGENT (Manten las comillas) ---
MI_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

# --- PEGA AQUÍ TU COOKIE ENTERA (Dentro de las tres comillas) ---
# Ejemplo: "cf_clearance=AbCdEf...; bb_sessionhash=..."
MIS_COOKIES = "bblastactivity=0; bbforum_view=0bb291be25fef25002b52d50dea338753d97597aa-1-%7Bi-2_i-1771271104_%7D; bblastvisit=1764098083; bbuserid=840125; bbpassword=4911cc1b3f610b4bd4dddf1226ee7d75; bbimloggedin=yes; bbsessionhash=b9ff0247411445fdfe612b4dc3bc8d1b; cf_clearance=33wjQ3Wjeq7SvL6X6s5pIk4k1YqNpXzm9wost9kyJKQ-1771276072-1.2.1.1-Yvn2baaCVH6AH.O1caa0B_0ucI6iFbPmsuuZaMjFi7hbPw6cXigTET9tkBcK5a5pyBxK31jGzBNRrPsylO8ddeM9gfeR8BQcmK3N0wzydDUnjkAEFcM8Tetba8PFSzqZxk0V5MVMDxqBXH.CO51l52Ll2B7eZBgceBIhG5MjsVG6Ht2o5bHsylEYhElX64wDCQ1K6HtUPApuDo6by9Y3pnM_NKSr88RHwu0HHwlMkmY"

HEADERS = {
    "User-Agent": MI_USER_AGENT,
    "Cookie": MIS_COOKIES,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.google.com/"
}

@app.route('/')
def home():
    hilos_encontrados = []
    
    start_page = request.args.get('start', 1, type=int)
    if start_page < 1: start_page = 1
    end_page = start_page + 10
    
    for page in range(start_page, end_page):
        try:
            url = f"https://www.forocoches.com/foro/forumdisplay.php?f=2&order=desc&page={page}"
            
            # Usamos requests normal, pero con TUS cookies
            response = requests.get(url, headers=HEADERS, timeout=5)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                
                links = soup.find_all('a', id=lambda x: x and x.startswith('thread_title_'))
                
                for link in links:
                    titulo_raw = link.get_text().strip()
                    titulo_safe = titulo_raw.replace('"', "'")
                    url_hilo = "https://www.forocoches.com/foro/" + link['href']
                    
                    if "+18" in titulo_raw:
                        hilos_encontrados.append({
                            'titulo': titulo_safe, 
                            'url': url_hilo, 
                            'pagina': page
                        })
            else:
                print(f"Error {response.status_code} en página {page}")
                
        except Exception as e:
            print(f"Error: {e}")
            continue

    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FC Radar +18</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root { --bg-body: #f8f9fa; --text-main: #212529; --card-bg: #fff; --velvet: #8a0b18; }
            [data-theme="dark"] { --bg-body: #121212; --text-main: #e0e0e0; --card-bg: #1e1e1e; --velvet: #a01523; }
            body { background: var(--bg-body); color: var(--text-main); font-family: 'Inter', sans-serif; padding: 20px; }
            .thread-card { background: var(--card-bg); border-left: 5px solid var(--velvet); padding: 15px; margin-bottom: 10px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .btn-velvet { background: var(--velvet); color: white; text-decoration: none; padding: 5px 15px; border-radius: 4px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container" style="max-width: 800px;">
            <div class="d-flex justify-content-between mb-4">
                <h3>Scanner +18 <small style="font-size:0.6em; opacity:0.6">(Modo Cookies Manuales)</small></h3>
                <button onclick="toggleTheme()" class="btn btn-sm btn-outline-secondary">Tema</button>
            </div>

            <div class="d-flex justify-content-between mb-3">
                {% if start > 1 %}<a href="/?start={{ start - 10 }}" class="btn btn-outline-dark">Anterior</a>{% else %}<button disabled class="btn btn-outline-dark">Anterior</button>{% endif %}
                <span>Pág {{ start }} - {{ end - 1 }}</span>
                <a href="/?start={{ start + 10 }}" class="btn btn-outline-dark">Siguiente</a>
            </div>

            {% for hilo in hilos %}
            <div class="thread-card">
                <div><strong>{{ hilo.titulo }}</strong><br><small>Página {{ hilo.pagina }}</small></div>
                <a href="{{ hilo.url }}" target="_blank" class="btn-velvet">Ver</a>
            </div>
            {% else %}
            <div class="text-center py-5">
                <h4>No se encontraron hilos</h4>
                <p>Si las cookies han caducado o Cloudflare bloquea la IP, actualiza las cookies en el código.</p>
            </div>
            {% endfor %}
            
            <div class="text-center mt-4"><a href="/?start={{ start + 10 }}" class="btn btn-dark">Cargar más</a></div>
        </div>
        <script>
            if(localStorage.getItem('t')==='d') document.documentElement.setAttribute('data-theme','dark');
            function toggleTheme(){
                let d = document.documentElement.getAttribute('data-theme')==='dark';
                document.documentElement.setAttribute('data-theme', d?'light':'dark');
                localStorage.setItem('t', d?'l':'d');
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, hilos=hilos_encontrados, start=start_page, end=end_page)
