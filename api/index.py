from flask import Flask, render_template_string, request
import cloudscraper # Librería antibloqueo
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuración del Scraper para imitar un navegador real (Chrome)
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
    
    # Paginación
    start_page = request.args.get('start', 1, type=int)
    if start_page < 1: start_page = 1
    end_page = start_page + 10 # Escanear 10 páginas
    
    # Lógica de escaneo
    for page in range(start_page, end_page):
        try:
            url = f"https://www.forocoches.com/foro/forumdisplay.php?f=2&order=desc&page={page}"
            
            # USAMOS EL SCRAPER EN LUGAR DE REQUESTS
            response = scraper.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                
                links = soup.find_all('a', id=lambda x: x and x.startswith('thread_title_'))
                
                for link in links:
                    titulo_raw = link.get_text().strip()
                    # Limpieza de comillas para no romper el HTML
                    titulo_safe = titulo_raw.replace('"', "'")
                    url_hilo = "https://www.forocoches.com/foro/" + link['href']
                    
                    if "+18" in titulo_raw:
                        hilos_encontrados.append({
                            'titulo': titulo_safe, 
                            'url': url_hilo, 
                            'pagina': page
                        })
        except Exception as e:
            print(f"Error en página {page}: {e}")
            continue

    # --- PLANTILLA HTML (Tu diseño completo) ---
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
            :root { --bg-body: #f8f9fa; --text-main: #212529; --text-muted: #6c757d; --card-bg: #ffffff; --card-border: #e9ecef; --control-bg: #ffffff; --velvet-color: #8a0b18; --active-filter-bg: #212529; --active-filter-text: #ffffff; }
            [data-theme="dark"] { --bg-body: #121212; --text-main: #e0e0e0; --text-muted: #a0a0a0; --card-bg: #1e1e1e; --card-border: #333333; --control-bg: #1e1e1e; --velvet-color: #a01523; --active-filter-bg: #e0e0e0; --active-filter-text: #121212; }
            body { font-family: 'Inter', sans-serif; background: var(--bg-body); color: var(--text-main); transition: 0.3s; }
            .age-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
            .age-modal { background: var(--card-bg); border: 2px solid var(--velvet-color); padding: 2rem; border-radius: 12px; text-align: center; width: 350px; }
            .btn-yes { background: var(--velvet-color); color: white; border: none; padding: 10px 30px; border-radius: 6px; font-weight: bold; margin: 10px; cursor: pointer; }
            .btn-no { background: transparent; border: 1px solid var(--text-muted); color: var(--text-muted); padding: 10px 30px; margin: 10px; cursor: pointer; }
            .thread-card { background: var(--card-bg); border: 1px solid var(--card-border); border-left: 5px solid var(--velvet-color); border-radius: 6px; padding: 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
            .filter-btn { padding: 6px 12px; border-radius: 20px; border: 1px solid var(--card-border); background: var(--control-bg); color: var(--text-muted); cursor: pointer; margin: 0 5px; }
            .filter-btn.active { background: var(--active-filter-bg); color: var(--active-filter-text); }
        </style>
    </head>
    <body>
        <div id="ageOverlay" class="age-overlay"><div class="age-modal"><h2>⚠️ +18</h2><p>¿Eres mayor de edad?</p><button class="btn-yes" onclick="verify(true)">SÍ</button><button class="btn-no" onclick="verify(false)">NO</button></div></div>
        
        <div class="container py-4" style="max-width: 800px;">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h5 fw-bold m-0">Scanner +18</h1>
                <button id="themeToggle" style="background:none; border:none; color:var(--text-main); font-size:1.2rem"><i class="fa-solid fa-moon"></i></button>
            </div>
            
            <div class="d-flex justify-content-center mb-3 flex-wrap">
                <button class="filter-btn active" onclick="filter('all', this)">Todos <span id="c-all"></span></button>
                <button class="filter-btn" onclick="filter('nsfw', this)">🔥 NSFW <span id="c-nsfw"></span></button>
                <button class="filter-btn" onclick="filter('penas', this)">👥 Peñas <span id="c-penas"></span></button>
            </div>
            
            <div class="d-flex justify-content-between mb-3 p-2 bg-light rounded" style="background:var(--control-bg)!important; border:1px solid var(--card-border)">
                {% if start > 1 %}<a href="/?start={{ start - 10 }}" class="btn btn-sm btn-outline-secondary">Anterior</a>{% else %}<button disabled class="btn btn-sm btn-outline-secondary">Anterior</button>{% endif %}
                <span class="small align-self-center">Pág {{ start }}-{{ end - 1 }}</span>
                <a href="/?start={{ start + 10 }}" class="btn btn-sm btn-outline-secondary">Siguiente</a>
            </div>
            
            <div id="list">
                {% for hilo in hilos %}
                <div class="thread-card" data-t="{{ hilo.titulo|lower }}">
                    <div><div class="fw-bold">{{ hilo.titulo }}</div><small class="text-muted">Pág. {{ hilo.pagina }}</small></div>
                    <a href="{{ hilo.url }}" target="_blank" class="btn btn-sm btn-danger" style="background:var(--velvet-color); border:none">Ver</a>
                </div>
                {% else %}
                    <div class="text-center py-5 text-muted">
                        <i class="fa-solid fa-robot fa-2x mb-2"></i><br>
                        No se encontraron hilos.<br>
                        <small>Si esto persiste, Forocoches está bloqueando la IP.</small>
                    </div>
                {% endfor %}
            </div>
            
            <div class="text-center mt-4"><a href="/?start={{ start + 10 }}" class="btn btn-outline-dark">Cargar más</a></div>
        </div>

        <script>
            // Edad
            if(localStorage.getItem('age')==='1') document.getElementById('ageOverlay').style.display='none';
            function verify(k){ if(k){localStorage.setItem('age','1'); document.getElementById('ageOverlay').style.display='none';} else window.location.href='https://google.com'; }
            
            // Tema
            const html=document.documentElement, btn=document.getElementById('themeToggle');
            if(localStorage.getItem('theme')==='dark') { html.setAttribute('data-theme','dark'); btn.innerHTML='<i class="fa-solid fa-sun"></i>'; }
            btn.onclick=()=>{ 
                const isD = html.getAttribute('data-theme')==='dark';
                html.setAttribute('data-theme', isD?'light':'dark'); 
                localStorage.setItem('theme', isD?'light':'dark');
                btn.innerHTML=isD?'<i class="fa-solid fa-moon"></i>':'<i class="fa-solid fa-sun"></i>';
            };
            
            // Filtros
            function filter(k,b){
                document.querySelectorAll('.filter-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active');
                document.querySelectorAll('.thread-card').forEach(c=>{
                    const t=c.getAttribute('data-t'), isP=t.startsWith('penya')||t.startsWith('peña')||t.startsWith('seguimiento');
                    c.style.display=(k==='all'||(k==='penas'&&isP)||(k==='nsfw'&&!isP))?'flex':'none';
                });
            }
            
            // Contadores
            const all=document.querySelectorAll('.thread-card'); let n=0,p=0;
            all.forEach(c=>{ const t=c.getAttribute('data-t'); (t.startsWith('penya')||t.startsWith('peña')||t.startsWith('seguimiento'))?p++:n++; });
            document.getElementById('c-all').innerText=`(${all.length})`; document.getElementById('c-nsfw').innerText=`(${n})`; document.getElementById('c-penas').innerText=`(${p})`;
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, hilos=hilos_encontrados, start=start_page, end=end_page)
