import { Marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import hljs from 'highlight.js';

// ── Markdown setup ──────────────────────────────────────────────────────────
const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
  })
);

// ── State ───────────────────────────────────────────────────────────────────
let manifest = null;
const sidebar = document.getElementById('sidebar');
const content = document.getElementById('content');

// ── Router ──────────────────────────────────────────────────────────────────
function getRoute() {
  const hash = location.hash.replace(/^#\/?/, '') || '';
  return hash;
}

function navigate(route) {
  location.hash = '#/' + route;
}

async function handleRoute() {
  const route = getRoute();
  updateActiveNav(route);

  if (!route || route === '') {
    renderHome();
    renderSidebar(null);
  } else if (route === 'downloads') {
    renderDownloads();
    renderSidebar(null);
  } else if (route === 'architecture') {
    renderArchitecture();
    renderSidebar(null);
  } else if (route === 'services') {
    renderServices();
    renderSidebar(null);
  } else if (route.startsWith('docs')) {
    const docPath = route.replace(/^docs\/?/, '');
    await renderDocs(docPath);
  } else {
    content.innerHTML = '<div class="md"><h1>404</h1><p>Strona nie znaleziona.</p></div>';
  }
}

function updateActiveNav(route) {
  document.querySelectorAll('.nav-link').forEach((el) => {
    const page = el.dataset.page;
    const isActive =
      (page === 'home' && !route) ||
      (page === 'docs' && route.startsWith('docs')) ||
      (page === 'downloads' && route === 'downloads') ||
      (page === 'architecture' && route === 'architecture') ||
      (page === 'services' && route === 'services');
    el.classList.toggle('active', isActive);
  });
}

// ── Home Page ───────────────────────────────────────────────────────────────
function renderHome() {
  content.innerHTML = `
    <div class="home-hero">
      <h1>🔬 C2004 Identification System</h1>
      <p>System identyfikacji RFID, QR, Barcode i Manual — z panelem administracyjnym, DSL i aplikacjami desktopowymi.</p>
    </div>

    <div class="home-cards">
      <a class="home-card" href="#/docs/_root/README.md">
        <div class="home-card-icon">📖</div>
        <h3>Dokumentacja</h3>
        <p>Pełna dokumentacja projektu, API, architektura i przewodniki wdrożenia.</p>
      </a>
      <a class="home-card" href="#/downloads">
        <div class="home-card-icon">⬇️</div>
        <h3>Downloads</h3>
        <p>Pobierz aplikacje desktopowe: Frontend Kiosk, Frontend Desktop, Admin Panel.</p>
      </a>
      <a class="home-card" href="#/architecture">
        <div class="home-card-icon">🏗️</div>
        <h3>Architektura</h3>
        <p>Przegląd architektury systemu, portów, baz danych i modułów.</p>
      </a>
      <a class="home-card" href="#/docs/desktop/README.md">
        <div class="home-card-icon">🖥️</div>
        <h3>Desktop Apps</h3>
        <p>Dokumentacja aplikacji Tauri: kiosk, desktop i admin.</p>
      </a>
      <a class="home-card" href="#/docs/_root/DEPLOYMENT-GUIDE.md">
        <div class="home-card-icon">🚀</div>
        <h3>Deployment</h3>
        <p>Docker Compose, K3s, Kiosk, Admin Desktop — wszystkie opcje wdrożenia.</p>
      </a>
      <a class="home-card" href="#/docs/INDEX.md">
        <div class="home-card-icon">🗂️</div>
        <h3>Indeks dokumentacji</h3>
        <p>Pełny spis treści wszystkich dokumentów w projekcie.</p>
      </a>
    </div>

    <div class="md">
      <h2>Porty serwisów</h2>
      <table>
        <thead><tr><th>Port</th><th>Serwis</th><th>Opis</th></tr></thead>
        <tbody>
          <tr><td>8100</td><td>Frontend</td><td>Główna aplikacja (Vite / nginx)</td></tr>
          <tr><td>8101</td><td>Backend API</td><td>FastAPI (uvicorn)</td></tr>
          <tr><td>8102</td><td>Admin Panel</td><td>Panel administracyjny</td></tr>
          <tr><td>8103</td><td>DSL API</td><td>Domain Specific Language</td></tr>
          <tr><td>8200</td><td>Docs Site</td><td>Ta strona dokumentacji</td></tr>
        </tbody>
      </table>

      <h2>Aplikacje desktopowe</h2>
      <table>
        <thead><tr><th>Aplikacja</th><th>Technologia</th><th>Tryb</th><th>Cel</th></tr></thead>
        <tbody>
          <tr><td><strong>Frontend Kiosk</strong></td><td>Tauri + Vite SPA</td><td>Fullscreen</td><td>Stanowisko identyfikacji</td></tr>
          <tr><td><strong>Frontend Desktop</strong></td><td>Tauri + Vite SPA</td><td>Okno</td><td>Standardowe użytkowanie</td></tr>
          <tr><td><strong>Admin Desktop</strong></td><td>Tauri + WebView</td><td>Okno 1400×900</td><td>Panel administracyjny</td></tr>
        </tbody>
      </table>
    </div>
  `;
}

// ── Downloads Page ──────────────────────────────────────────────────────────
function renderDownloads() {
  content.innerHTML = `
    <div class="md">
      <h1>Downloads</h1>
      <p>Pobierz aplikacje desktopowe systemu C2004. Wszystkie aplikacje wymagają 64-bit Linux lub Windows.</p>
    </div>

    <div class="downloads-grid">
      <div class="download-card">
        <span class="download-card-badge badge-kiosk">Kiosk</span>
        <h3>🖥️ Frontend Kiosk</h3>
        <p>Samodzielna aplikacja do stanowisk identyfikacji. Tryb fullscreen, bez dekoracji, always-on-top.</p>
        <div class="download-card-meta">
          <span class="meta-tag">Tauri v2</span>
          <span class="meta-tag">Vite SPA</span>
          <span class="meta-tag">Port 8101</span>
          <span class="meta-tag">~/.identification-kiosk/</span>
        </div>
        <div class="download-actions">
          <a class="btn btn-primary" href="artifacts/Identification-Kiosk_1.0.0_amd64.deb" download>📦 .deb (Debian/Ubuntu)</a>
          <a class="btn btn-secondary" href="artifacts/Identification-Kiosk_1.0.0_amd64.AppImage" download>📦 AppImage</a>
          <a class="btn btn-secondary" href="artifacts/Identification-Kiosk_1.0.0_x64-setup.exe" download>📦 .exe (Windows)</a>
        </div>
      </div>

      <div class="download-card">
        <span class="download-card-badge badge-desktop">Desktop</span>
        <h3>🖥️ Frontend Desktop</h3>
        <p>Standardowa wersja okienkowa aplikacji identyfikacji. Resizable, z dekoracjami okna.</p>
        <div class="download-card-meta">
          <span class="meta-tag">Tauri v2</span>
          <span class="meta-tag">Vite SPA</span>
          <span class="meta-tag">Port 8101</span>
        </div>
        <div class="download-actions">
          <a class="btn btn-primary" href="artifacts/Identification_1.0.0_amd64.deb" download>📦 .deb (Debian/Ubuntu)</a>
          <a class="btn btn-secondary" href="artifacts/Identification_1.0.0_amd64.AppImage" download>📦 AppImage</a>
          <a class="btn btn-secondary" href="artifacts/Identification_1.0.0_x64-setup.exe" download>📦 .exe (Windows)</a>
        </div>
      </div>

      <div class="download-card">
        <span class="download-card-badge badge-admin">Admin</span>
        <h3>⚙️ Admin Desktop</h3>
        <p>Panel administracyjny w natywnym oknie. Automatycznie uruchamia backend admin (uvicorn).</p>
        <div class="download-card-meta">
          <span class="meta-tag">Tauri v2</span>
          <span class="meta-tag">WebView → FastAPI</span>
          <span class="meta-tag">Port 8102</span>
          <span class="meta-tag">Python 3.11+</span>
        </div>
        <div class="download-actions">
          <a class="btn btn-primary" href="artifacts/Identification-Admin_1.0.0_amd64.deb" download>📦 .deb (Debian/Ubuntu)</a>
          <a class="btn btn-secondary" href="artifacts/Identification-Admin_1.0.0_amd64.AppImage" download>📦 AppImage</a>
          <a class="btn btn-secondary" href="artifacts/Identification-Admin_1.0.0_x64-setup.exe" download>📦 .exe (Windows)</a>
        </div>
      </div>
    </div>

    <div class="md">
      <h2>🚀 Deployment na środowisko produkcyjne</h2>
      <div class="deployment-steps">
        <h3>1. Przygotowanie środowiska (VPS)</h3>
        <pre><code class="language-bash"># Klonowanie repozytorium
cd /root && git clone https://github.com/zlecenia/c2004.git
cd c2004

# Instalacja wszystkich zależności (Rust, Node, Python, desktop deps)
make install

# Aktywacja Rust
source "$HOME/.cargo/env"</code></pre>

        <h3>2. Budowanie aplikacji desktopowych</h3>
        <pre><code class="language-bash"># Buduj wszystkie aplikacje Linux (.deb + AppImage)
make desktop-linux
make desktop-build-linux
make admin-desktop-linux

# Zbierz artefakty do site/public/artifacts/
make site-collect-artifacts

# Sprawdź zebrane pliki
ls -lh site/public/artifacts/</code></pre>

        <h3>3. Budowanie i deployment dokumentacji</h3>
        <pre><code class="language-bash"># Zbuduj dokumentację ze wszystkimi artefaktami
make site-build

# Deploy na VPS (Kubernetes/K3s)
make vps-deploy-docs

# Sprawdź status deploymentu
kubectl get pods -n identification</code></pre>

        <h3>4. Weryfikacja</h3>
        <pre><code class="language-bash"># Sprawdź dostępność stron
curl -I https://docs.mask.services
curl -I https://download.mask.services

# Sprawdź czy artefakty są dostępne
curl -I https://download.mask.services/artifacts/Identification_1.0.0_amd64.deb</code></pre>
      </div>

      <h2>🔄 Aktualizacja systemu</h2>
      <p>Przy aktualizacji kodu wykonaj:</p>
      <pre><code class="language-bash"># 1. Pobierz zmiany
git pull

# 2. Zbuduj nowe aplikacje (jeśli zmiany w desktop)
make desktop-linux
make desktop-build-linux
make admin-desktop-linux
make site-collect-artifacts

# 3. Zaktualizuj dokumentację
make vps-deploy-docs</code></pre>

      <h2>🛠️ Budowanie ze źródeł (deweloperskie)</h2>
      <pre><code class="language-bash"># Frontend Kiosk (fullscreen)
make desktop

# Frontend Desktop (okno)  
make desktop-build-linux

# Admin Desktop
make admin-desktop

# Wszystkie na raz
make desktop-linux
make desktop-build-linux
make admin-desktop-linux</code></pre>

      <h2>📋 Wymagania systemowe</h2>
      <ul>
        <li><strong>Rust toolchain</strong> — <code>curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh</code></li>
        <li><strong>Node.js 20+</strong> (dla frontend builds)</li>
        <li><strong>Python 3.11+</strong> + uvicorn (dla admin desktop)</li>
        <li><strong>System deps (Linux)</strong> — <code>apt install pkg-config libglib2.0-dev libgtk-3-dev libwebkit2gtk-4.1-dev</code></li>
        <li><strong>Kubernetes/K3s</strong> — dla deploymentu dokumentacji</li>
        <li><strong>Docker</strong> — opcjonalnie, dla kontenerowego deploymentu</li>
      </ul>
    </div>
  `;
}

// ── Architecture Page ───────────────────────────────────────────────────────
function renderArchitecture() {
  content.innerHTML = `
    <div class="md">
      <h1>Architektura systemu</h1>
      <p>Przegląd architektury C2004 Identification System.</p>
    </div>

    <div class="arch-diagram">┌─────────────────────────────────────────────────────────────────────┐
│                         TRAEFIK (port 80/443)                       │
│                                                                     │
│  /           → Frontend (nginx:8100)                                │
│  /api/*      → Backend (uvicorn:8101)                               │
│  /ws/*       → Backend WebSocket                                    │
│  /firmware/* → Firmware (uvicorn:8202)                               │
└─────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Frontend    │ │  Backend API │ │   DSL    │ │   Firmware   │
│  :8100       │ │  :8101       │ │  :8103   │ │   :8202      │
│  Vite / SPA  │ │  FastAPI     │ │  FastAPI │ │   FastAPI    │
└──────┬───────┘ └──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │                │              │               │
       │                ▼              ▼               │
       │         ┌──────────────────────────┐          │
       │         │      SQLite Databases    │          │
       │         │  main (51) │ menu (6)    │          │
       │         │  dsl (11)  │ config      │          │
       │         └──────────────────────────┘          │
       │                                               │
       └───────────── Admin Panel (:8102) ─────────────┘
                   Fleet / Git Sync / CQRS</div>

    <div class="md">
      <h2>Aplikacje desktopowe (Tauri v2)</h2>
    </div>

    <div class="arch-diagram">┌───────────────────────────────────────────────────────────┐
│                    Tauri v2 (Rust + WebView)               │
│                                                            │
│  ┌───────────────────┐    ┌─────────────────────────────┐  │
│  │    Rust main.rs   │    │         WebView             │  │
│  │                   │───▶│                             │  │
│  │  • auto-start     │    │  Frontend Kiosk:            │  │
│  │    backend        │    │    Vite SPA (dist/)         │  │
│  │  • kiosk data dir │    │    → fullscreen, no-decor   │  │
│  │  • config.json    │    │                             │  │
│  │  • env generator  │    │  Admin Desktop:             │  │
│  └───────────────────┘    │    http://localhost:8102    │  │
│           │               └─────────────────────────────┘  │
│           ▼                                                │
│  ~/.identification-kiosk/                                  │
│  ├── config/ (config.json, .env)                           │
│  ├── db/ (main, menu, config, logs)                        │
│  ├── logs/ (backend, heartbeat, sync)                      │
│  └── backups/                                              │
└────────────────────────────────────────────────────────────┘</div>

    <div class="md">
      <h2>Tryby wdrożenia</h2>
      <table>
        <thead><tr><th>Opcja</th><th>Środowisko</th><th>Opis</th></tr></thead>
        <tbody>
          <tr><td>Docker Compose</td><td>Dev / mały prod</td><td><code>make prod</code></td></tr>
          <tr><td>K3s</td><td>Produkcja / klaster</td><td><code>make prod-k3s</code></td></tr>
          <tr><td>Frontend Kiosk</td><td>RPi / stanowisko</td><td><code>make desktop</code></td></tr>
          <tr><td>Admin Desktop</td><td>Stacja zarządzania</td><td><code>make admin-desktop</code></td></tr>
        </tbody>
      </table>
    </div>
  `;
}

// ── Docker Services Page ──────────────────────────────────────────────────
const SERVICES_CONFIG = [
  {
    category: 'Core System',
    icon: '🎯',
    badge: 'core',
    services: [
      { name: 'Frontend', port: 8100, url: 'http://localhost:8100', health: '/' },
      { name: 'Backend API', port: 8101, url: 'http://localhost:8101', health: '/api/v3/health' },
      { name: 'Admin Panel', port: 8102, url: 'http://localhost:8102', health: '/api/health' }
    ]
  },
  {
    category: 'DSL & Scenariusze',
    icon: '📜',
    badge: 'dsl',
    services: [
      { name: 'CQL Editor', port: 8091, url: 'http://localhost:8091', health: '/' },
      { name: 'DSL API', port: 8103, url: 'http://localhost:8103', health: '/api/v1/health' },
      { name: 'CQL Backend', port: 8108, url: 'http://localhost:8108', health: '/api/v1/health' }
    ]
  },
  {
    category: 'Firmware & Test',
    icon: '🔧',
    badge: 'firmware',
    services: [
      { name: 'Test Simulator', port: 8202, url: 'http://localhost:8202', health: '/health' }
    ]
  },
  {
    category: 'Encoder Control',
    icon: '🕹️',
    badge: 'encoder',
    services: [
      { name: 'Encoder Dashboard', port: 8105, url: 'http://localhost:8105', health: '/encoder/status' },
      { name: 'c2004 Iframe Test', port: 8105, url: 'http://localhost:8105/c2004-test', health: null }
    ]
  },
  {
    category: 'Platform',
    icon: '🌐',
    badge: 'platform',
    services: [
      { name: 'Platform Gateway', port: 3000, url: 'http://localhost:3000', health: '/health' },
      { name: 'Platform UI', port: 5173, url: 'http://localhost:5173', health: '/' }
    ]
  },
  {
    category: 'Dokumentacja',
    icon: '📚',
    badge: 'docs',
    services: [
      { name: 'Docs Site', port: 8200, url: 'http://localhost:8200', health: null, active: true }
    ]
  }
];

function renderServices() {
  content.innerHTML = `
    <div class="md">
      <h1>🐳 Serwisy Docker - Dashboard</h1>
      <p>Wszystkie uruchomione kontenery i moduły systemu C2004. 
         <span class="health-indicator" id="health-summary">Sprawdzanie...</span>
         <button class="btn-sm" onclick="runHealthCheck()" style="margin-left:12px;">🔄 Odśwież</button>
      </p>
    </div>

    <div class="services-grid" id="services-grid">
      <div class="docker-loading">Ładowanie usług...</div>
    </div>

    <div class="md">
      <h2>📊 Szczegółowy Health Check</h2>
      <p>Ostatni check: <span id="health-time">-</span> | 
         ✅ <span id="healthy-count">0</span> zdrowych | 
         ❌ <span id="unhealthy-count">0</span> problemów</p>
    </div>

    <div class="health-table-wrapper" id="health-table">
      <div class="docker-loading">Uruchom check aby zobaczyć szczegóły...</div>
    </div>
  `;

  renderServicesGrid();
  runHealthCheck();
}

function renderServicesGrid() {
  const grid = document.getElementById('services-grid');
  
  let html = '';
  for (const cat of SERVICES_CONFIG) {
    const isActive = cat.badge === 'docs' ? 'active' : '';
    const coreClass = cat.badge === 'core' ? 'core' : '';
    
    html += `
      <div class="service-card ${coreClass} ${isActive}">
        <div class="service-header">
          <span class="service-icon">${cat.icon}</span>
          <h3>${cat.category}</h3>
          <span class="service-badge ${cat.badge}">${cat.badge}</span>
        </div>
        <div class="service-links">
          ${cat.services.map(s => `
            <a href="${s.url}" target="_blank" class="service-link ${isActive}" data-port="${s.port}">
              <span class="link-port">${s.port}</span>
              <span class="link-name">${s.name}</span>
              <span class="health-dot" id="health-${s.port}">●</span>
            </a>
          `).join('')}
        </div>
      </div>
    `;
  }
  
  grid.innerHTML = html;
}

async function checkServiceHealth(service) {
  if (!service.health) return { status: 'unknown', responseTime: 0 };
  
  const start = performance.now();
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    
    // Use proxy endpoint to bypass CORS
    const proxyUrl = `/health/${service.port}`;
    
    const resp = await fetch(proxyUrl, { 
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    const time = Math.round(performance.now() - start);
    
    return { 
      status: resp.ok ? 'healthy' : 'degraded', 
      responseTime: time,
      httpStatus: resp.status
    };
  } catch (e) {
    return { 
      status: 'unhealthy', 
      responseTime: Math.round(performance.now() - start),
      error: e.message 
    };
  }
}

async function runHealthCheck() {
  const summary = document.getElementById('health-summary');
  const timeEl = document.getElementById('health-time');
  const healthyEl = document.getElementById('healthy-count');
  const unhealthyEl = document.getElementById('unhealthy-count');
  const table = document.getElementById('health-table');
  
  summary.textContent = 'Sprawdzanie...';
  summary.className = 'health-indicator checking';
  
  const allServices = SERVICES_CONFIG.flatMap(c => c.services);
  const results = [];
  
  // Check all services in parallel
  await Promise.all(allServices.map(async (s) => {
    const health = await checkServiceHealth(s);
    results.push({ ...s, ...health });
    
    // Update dot on card
    const dot = document.getElementById(`health-${s.port}`);
    if (dot) {
      dot.className = `health-dot ${health.status}`;
    }
  }));
  
  // Update summary
  const healthy = results.filter(r => r.status === 'healthy').length;
  const unhealthy = results.filter(r => r.status === 'unhealthy').length;
  const degraded = results.filter(r => r.status === 'degraded').length;
  
  healthyEl.textContent = healthy;
  unhealthyEl.textContent = unhealthy + degraded;
  timeEl.textContent = new Date().toLocaleTimeString();
  
  if (unhealthy === 0 && degraded === 0) {
    summary.textContent = `✅ Wszystkie usługi zdrowe (${healthy})`;
    summary.className = 'health-indicator healthy';
  } else if (unhealthy === 0) {
    summary.textContent = `⚠️ ${healthy} OK, ${degraded} z problemami`;
    summary.className = 'health-indicator degraded';
  } else {
    summary.textContent = `❌ ${unhealthy} niedostępne`;
    summary.className = 'health-indicator unhealthy';
  }
  
  // Render detailed table
  let html = '<table class="health-table">';
  html += '<thead><tr><th>Usługa</th><th>Port</th><th>Status</th><th>Response</th><th>Ostatni błąd</th></tr></thead>';
  html += '<tbody>';
  
  for (const r of results) {
    const statusClass = r.status;
    const statusText = r.status === 'healthy' ? '✅ Zdrowy' : 
                       r.status === 'degraded' ? '⚠️ Ograniczony' : 
                       r.status === 'unknown' ? '❓ Nieznany' : '❌ Niedostępny';
    
    html += `
      <tr class="${statusClass}">
        <td><strong>${r.name}</strong></td>
        <td><a href="${r.url}" target="_blank">${r.port}</a></td>
        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        <td>${r.responseTime > 0 ? r.responseTime + 'ms' : '-'}</td>
        <td>${r.error || '-'}</td>
      </tr>
    `;
  }
  
  html += '</tbody></table>';
  table.innerHTML = html;
}

async function loadDockerStatus() {
  const container = document.getElementById('docker-status');
  const timeEl = document.getElementById('docker-time');
  
  try {
    // Try to fetch from a local endpoint or simulate with static data
    const containers = [
      { name: 'identification-frontend', port: '8100', status: 'running', image: 'c2004-frontend' },
      { name: 'identification-backend', port: '8101', status: 'running', image: 'c2004-backend' },
      { name: 'c2004-admin', port: '8102', status: 'running', image: 'c2004-admin' },
      { name: 'cql-editor', port: '8091', status: 'running', image: 'cql-editor' },
      { name: 'cql-backend', port: '8108', status: 'running', image: 'cql-backend' },
      { name: 'test-simulator-firmware', port: '8202', status: 'running', image: 'firmware-sim' },
      { name: 'c2004-postgres', port: '5432', status: 'running', image: 'postgres:15' },
    ];

    let html = '<div class="docker-table-wrapper">';
    html += '<table class="docker-table">';
    html += '<thead><tr><th>Kontener</th><th>Port</th><th>Status</th><th>Akcja</th></tr></thead>';
    html += '<tbody>';
    
    for (const c of containers) {
      const statusClass = c.status === 'running' ? 'status-running' : 'status-stopped';
      html += `<tr>
        <td><strong>${c.name}</strong><br><small>${c.image}</small></td>
        <td><code>${c.port}</code></td>
        <td><span class="status-badge ${statusClass}">${c.status}</span></td>
        <td><a href="http://localhost:${c.port}" target="_blank" class="btn-sm">Otwórz</a></td>
      </tr>`;
    }
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
    timeEl.textContent = new Date().toLocaleTimeString();
  } catch (e) {
    container.innerHTML = `<div class="docker-error">Nie można załadować statusu Docker: ${e.message}</div>`;
  }
}

// ── Docs Page ───────────────────────────────────────────────────────────────
async function renderDocs(docPath) {
  if (!manifest) {
    try {
      const res = await fetch('./docs-manifest.json');
      manifest = await res.json();
    } catch {
      content.innerHTML = '<div class="md"><h1>Błąd</h1><p>Nie można załadować manifestu dokumentacji. Uruchom <code>npm run manifest</code> w katalogu site/.</p></div>';
      return;
    }
  }

  renderSidebar(manifest);

  if (!docPath) {
    docPath = '_root/README.md';
  }

  // Highlight active sidebar item
  document.querySelectorAll('.sidebar-item').forEach((el) => {
    el.classList.toggle('active', el.dataset.slug === docPath);
  });

  // Fetch and render markdown
  const filePath = `./docs/${docPath}`;
  try {
    const res = await fetch(filePath);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const md = await res.text();
    const html = marked.parse(md);
    content.innerHTML = `<div class="md">${html}</div>`;
  } catch (e) {
    content.innerHTML = `<div class="md"><h1>Dokument nie znaleziony</h1><p>Nie można załadować: <code>${docPath}</code></p><p>${e.message}</p></div>`;
  }
}

// ── Sidebar ─────────────────────────────────────────────────────────────────
function renderSidebar(manifest) {
  if (!manifest) {
    sidebar.innerHTML = '';
    sidebar.style.display = 'none';
    return;
  }

  sidebar.style.display = '';
  let html = '';

  for (const section of manifest.sections) {
    if (section.type === 'group') {
      html += `<div class="sidebar-group">`;
      html += `<span class="sidebar-group-label">${esc(section.label)}</span>`;
      if (section.children) {
        for (const child of section.children) {
          if (child.type === 'doc') {
            html += `<a class="sidebar-item" href="#/docs/${child.slug}" data-slug="${esc(child.slug)}">${esc(child.label)}</a>`;
          } else if (child.type === 'group') {
            html += `<span class="sidebar-group-label" style="padding-left:28px;font-size:10px">${esc(child.label)}</span>`;
            if (child.children) {
              for (const sub of child.children) {
                html += `<a class="sidebar-item sidebar-child" href="#/docs/${sub.slug}" data-slug="${esc(sub.slug)}">${esc(sub.label)}</a>`;
              }
            }
          }
        }
      }
      html += `</div>`;
    } else if (section.type === 'doc') {
      html += `<a class="sidebar-item" href="#/docs/${section.slug}" data-slug="${esc(section.slug)}">${esc(section.label)}</a>`;
    }
  }

  sidebar.innerHTML = html;
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// ── Init ────────────────────────────────────────────────────────────────────
window.addEventListener('hashchange', handleRoute);
handleRoute();

// Expose functions for onclick handlers
window.runHealthCheck = runHealthCheck;
