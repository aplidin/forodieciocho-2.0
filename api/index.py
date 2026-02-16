import sys
import socket
from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuración
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def find_free_port(start_port=5000):
    """Encuentra un puerto libre automáticamente."""
    port = start_port
    while port < start_port + 10:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(('127.0.0.1', port))
            if res != 0: # El puerto está libre
                return port
            port += 1
    return start_port

@app.route('/')
def home():
    hilos_encontrados = []
    
    # Paginación
    start_page = request.args.get('start', 1, type=int)
    if start_page < 1: start_page = 1
    end_page = start_page + 10
    
    print(f"Escaneando páginas {start_page} a {end_page}...") # Log en consola
    
    # Lógica de escaneo
    for page in range(start_page, end_page):
        try:
            url = f"https://www.forocoches.com/foro/forumdisplay.php?f=2&order=desc&page={page}"
            response = requests.get(url, headers=HEADERS, timeout=3)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                
                links = soup.find_all('a', id=lambda x: x and x.startswith('thread_title_'))
                
                for link in links:
                    titulo_raw = link.get_text().strip()
                    # IMPORTANTE: Reemplazamos comillas dobles para no romper el HTML attribute data-title
                    titulo_safe = titulo_raw.replace('"', "'")
                    
                    url_hilo = "https://www.forocoches.com/foro/" + link['href']
                    
                    if "+18" in titulo_raw:
                        hilos_encontrados.append({
                            'titulo': titulo_safe, 
                            'url': url_hilo, 
                            'pagina': page
                        })
        except Exception as e:
            print(f"Error escaneando página {page}: {e}")
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
            :root {
                --bg-body: #f8f9fa;
                --text-main: #212529;
                --text-muted: #6c757d;
                --card-bg: #ffffff;
                --card-border: #e9ecef;
                --control-bg: #ffffff;
                --nav-btn-bg: #ffffff;
                --nav-btn-text: #495057;
                --nav-btn-hover: #e9ecef;
                --velvet-color: #8a0b18;
                --velvet-hover: #63050f;
                --active-filter-bg: #212529;
                --active-filter-text: #ffffff;
            }

            [data-theme="dark"] {
                --bg-body: #121212;
                --text-main: #e0e0e0;
                --text-muted: #a0a0a0;
                --card-bg: #1e1e1e;
                --card-border: #333333;
                --control-bg: #1e1e1e;
                --nav-btn-bg: #2d2d2d;
                --nav-btn-text: #e0e0e0;
                --nav-btn-hover: #3d3d3d;
                --velvet-color: #a01523;
                --velvet-hover: #c41e30;
                --active-filter-bg: #e0e0e0;
                --active-filter-text: #121212;
            }

            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-body);
                color: var(--text-main);
                transition: background-color 0.3s, color 0.3s;
                overflow-x: hidden; /* Prevenir scroll horizontal */
            }
            
            /* MODAL REFORZADO */
            .age-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.95);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
                backdrop-filter: blur(5px);
            }

            .age-modal {
                background: var(--card-bg);
                color: var(--text-main);
                border: 2px solid var(--velvet-color);
                padding: 2rem;
                border-radius: 12px;
                text-align: center;
                max-width: 90%;
                width: 400px;
                box-shadow: 0 0 50px rgba(138, 11, 24, 0.5);
            }

            .btn-age-yes {
                background: var(--velvet-color);
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: 800;
                margin: 10px;
                cursor: pointer;
            }
            .btn-age-no {
                background: transparent;
                border: 1px solid var(--text-muted);
                color: var(--text-muted);
                padding: 10px 30px;
                border-radius: 6px;
                margin: 10px;
                cursor: pointer;
            }

            .thread-card {
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-left: 5px solid var(--velvet-color);
                border-radius: 6px;
                padding: 1.2rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .hidden { display: none !important; }
            
            .btn-velvet {
                background-color: var(--velvet-color);
                color: white !important;
                padding: 0.6rem 1.2rem;
                border-radius: 5px;
                text-decoration: none;
                font-weight: 600;
            }
            
            /* Filtros */
            .filter-container { display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;}
            .filter-btn { padding: 8px 15px; border-radius: 20px; border: 1px solid var(--card-border); background: var(--control-bg); color: var(--text-muted); cursor: pointer; }
            .filter-btn.active { background: var(--active-filter-bg); color: var(--active-filter-text); }
        </style>
    </head>
    <body>

        <div id="ageOverlay" class="age-overlay">
            <div class="age-modal">
                <h2 class="mb-3">⚠️ Advertencia</h2>
                <p>Contenido para adultos (+18).<br>¿Eres mayor de edad?</p>
                <button class="btn-age-yes" onclick="verifyAge(true)">SÍ</button>
                <button class="btn-age-no" onclick="verifyAge(false)">NO</button>
            </div>
        </div>

        <div class="container py-4" style="max-width: 900px;">
            <div class="text-center mb-4">
                <button id="themeToggle" style="float: right; background:none; border:1px solid var(--text-muted); border-radius:50%; width:35px; height:35px; color:var(--text-main); cursor:pointer"><i class="fa-solid fa-moon"></i></button>
                <h1 class="h4 fw-bold">Scanner +18</h1>
            </div>

            <div class="d-flex justify-content-between mb-3">
                {% if start > 1 %}
                    <a href="/?start={{ start - 10 }}" class="btn btn-sm btn-outline-secondary">Anterior</a>
                {% else %}
                    <button class="btn btn-sm btn-outline-secondary" disabled>Anterior</button>
                {% endif %}
                <span class="text-muted small align-self-center">Páginas {{ start }} - {{ end - 1 }}</span>
                <a href="/?start={{ start + 10 }}" class="btn btn-sm btn-outline-secondary">Siguiente</a>
            </div>

            <div class="filter-container">
                <button class="filter-btn active" onclick="filterThreads('all', this)">Todos <span id="c-all" class="small opacity-50"></span></button>
                <button class="filter-btn" onclick="filterThreads('nsfw', this)">🔥 NSFW <span id="c-nsfw" class="small opacity-50"></span></button>
                <button class="filter-btn" onclick="filterThreads('penas', this)">👥 Peñas <span id="c-penas" class="small opacity-50"></span></button>
            </div>

            <div id="threadContainer">
                {% for hilo in hilos %}
                <div class="thread-card" data-title="{{ hilo.titulo }}">
                    <div>
                        <div class="fw-bold" style="color: var(--text-main)">{{ hilo.titulo }}</div>
                        <small class="text-muted">Pág. {{ hilo.pagina }}</small>
                    </div>
                    <a href="{{ hilo.url }}" target="_blank" class="btn-velvet">Ver</a>
                </div>
                {% else %}
                <div class="text-center py-5 text-muted">
                    No se encontraron hilos o hubo un error de conexión.
                </div>
                {% endfor %}
            </div>

            <div class="text-center mt-4">
                <a href="/?start={{ start + 10 }}" class="btn btn-outline-dark px-5">Cargar Siguientes</a>
            </div>
        </div>

        <script>
            // --- GESTIÓN DE ERRORES Y EDAD ---
            try {
                // Verificar Edad
                const isVerified = localStorage.getItem('ageVerified');
                const overlay = document.getElementById('ageOverlay');
                
                if (isVerified === 'true') {
                    overlay.style.display = 'none';
                } else {
                    // Si no está verificado, aseguramos que se vea
                    overlay.style.display = 'flex';
                    document.body.style.overflow = 'hidden';
                }
            } catch (e) {
                console.error("Error acceso localStorage", e);
                // En caso de error (modo incógnito estricto), ocultamos para no bloquear
                document.getElementById('ageOverlay').style.display = 'none';
            }

            function verifyAge(isAdult) {
                if (isAdult) {
                    try { localStorage.setItem('ageVerified', 'true'); } catch(e){}
                    document.getElementById('ageOverlay').style.display = 'none';
                    document.body.style.overflow = 'auto';
                } else {
                    window.location.href = "https://www.google.com";
                }
            }

            // --- MODO OSCURO ---
            const htmlEl = document.documentElement;
            const toggleBtn = document.getElementById('themeToggle');
            
            if (localStorage.getItem('theme') === 'dark') {
                htmlEl.setAttribute('data-theme', 'dark');
                toggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            }

            toggleBtn.onclick = () => {
                const isDark = htmlEl.getAttribute('data-theme') === 'dark';
                const newTheme = isDark ? 'light' : 'dark';
                htmlEl.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                toggleBtn.innerHTML = newTheme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
            };

            // --- FILTROS ---
            function filterThreads(cat, btn) {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const cards = document.querySelectorAll('.thread-card');
                cards.forEach(c => {
                    const t = c.getAttribute('data-title').toLowerCase();
                    const isPena = t.startsWith('penya') || t.startsWith('peña') || t.startsWith('seguimiento');
                    
                    let show = (cat === 'all') || 
                               (cat === 'penas' && isPena) || 
                               (cat === 'nsfw' && !isPena);
                               
                    c.style.display = show ? 'flex' : 'none';
                });
            }

            // Contadores iniciales
            document.addEventListener('DOMContentLoaded', () => {
                const cards = document.querySelectorAll('.thread-card');
                let nsfw = 0, penas = 0;
                cards.forEach(c => {
                    const t = c.getAttribute('data-title').toLowerCase();
                    if (t.startsWith('penya') || t.startsWith('peña') || t.startsWith('seguimiento')) penas++;
                    else nsfw++;
                });
                document.getElementById('c-all').innerText = `(${cards.length})`;
                document.getElementById('c-nsfw').innerText = `(${nsfw})`;
                document.getElementById('c-penas').innerText = `(${penas})`;
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, hilos=hilos_encontrados, start=start_page, end=end_page)

if __name__ == '__main__':
    # Busca un puerto libre automáticamente para evitar errores "Address already in use"
    port = find_free_port()
    print(f"--- INICIANDO SERVIDOR EN: http://127.0.0.1:{port} ---")
    app.run(debug=True, port=port)
