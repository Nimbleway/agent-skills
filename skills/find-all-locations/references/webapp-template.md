# Webapp Template

Fully parameterized single-file HTML template for an interactive location guide webapp. Generalized from the Williamsburg Coffee Guide.

When generating a webapp, replace all `{PLACEHOLDER}` values and customize the CONFIG object for the target category.

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{APP_TITLE}` | Page title | `"Park Slope Restaurants"` |
| `{HERO_TITLE}` | H1 with `<em>` on category | `"Park Slope <em>Restaurants</em>"` |
| `{TAGLINE}` | Subtitle text | `"Every restaurant in the neighborhood"` |
| `{EMOJI}` | Favicon emoji | `"🍽"`, `"☕"`, `"🍺"`, `"💪"` |
| `{DATA_FILENAME}` | JSON data file name | `"park_slope_restaurants_data.json"` |
| `{LOADING_TEXT}` | Loading screen text | `"Setting the table..."`, `"Brewing your guide..."` |
| `{EMPTY_ICON}` | Empty state icon | `"🍽"`, `"☕"`, `"🍺"` |
| `{EMPTY_TEXT}` | Empty state text | `"No restaurants match your filters"` |
| `{MAP_CENTER_LAT}` | Map center latitude | `40.674` |
| `{MAP_CENTER_LNG}` | Map center longitude | `-73.978` |
| `{MAP_ZOOM}` | Default zoom level | `14` |
| `{HERO_STATS}` | Hero stat blocks HTML | See below |
| `{FILTER_PILLS}` | Filter pill buttons HTML | See below |
| `{SORT_OPTIONS}` | Sort select options HTML | See below |
| `{CSS_VARIABLES}` | Color scheme CSS variables | See presets below |
| `{NORMALIZE_FIELDS}` | JS normalize function body | Category-specific field coercion |
| `{FILTER_LOGIC}` | JS applyFilters switch cases | Category-specific filter logic |
| `{SORT_LOGIC}` | JS sort switch cases | Category-specific sort logic |
| `{CARD_BADGES}` | JS badge generation code | Category-specific badges |
| `{CARD_SIGNALS}` | JS signal tag generation code | Category-specific signal tags |
| `{MODAL_BADGES}` | JS modal badge generation | Category-specific modal badges |
| `{MODAL_SIGNALS}` | JS modal signal bars config | Category-specific signals |
| `{MODAL_LINKS}` | JS modal link generation | Which social links to show |
| `{QUALITY_CLASS}` | CSS class for quality indicator | `"third-wave"`, `"craft"`, `"artisan"` |
| `{QUALITY_CHECK}` | JS quality check expression | `"s.isThirdWave"`, `"s.craft_signal >= 2"` |

## Color Scheme Presets

### Coffee (warm espresso tones)
```css
--gold: #D4A574; --gold-light: #E8C9A0; --gold-bright: #F0D4A8;
--gold-dark: #B8894A; --amber: #C4843C; --espresso: #3C2415;
--bg: #0F0B08; --bg-warm: #1A1410; --surface: #1E1914;
```

### Restaurant (warm burgundy/terracotta)
```css
--gold: #C45B4A; --gold-light: #D48070; --gold-bright: #E09888;
--gold-dark: #A84535; --amber: #B85A42; --espresso: #3C1815;
--bg: #0F0808; --bg-warm: #1A1210; --surface: #1E1614;
```

### Bar (deep navy/steel blue)
```css
--gold: #7B9FCC; --gold-light: #9BB8DD; --gold-bright: #B0C8E8;
--gold-dark: #5A80B0; --amber: #6A90C0; --espresso: #152030;
--bg: #080B0F; --bg-warm: #101418; --surface: #141A1E;
```

### Fitness (energetic green)
```css
--gold: #5CAA6E; --gold-light: #7BC08A; --gold-bright: #90D0A0;
--gold-dark: #3A8A4E; --amber: #4C9A5E; --espresso: #153020;
--bg: #080F0A; --bg-warm: #101A12; --surface: #141E16;
```

### Generic (teal/slate)
```css
--gold: #6BAAAA; --gold-light: #88C0C0; --gold-bright: #A0D0D0;
--gold-dark: #4A8A8A; --amber: #5A9A9A; --espresso: #152828;
--bg: #0A0F0F; --bg-warm: #121818; --surface: #161E1E;
```

## Template

````html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>{APP_TITLE}</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>{EMOJI}</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" crossorigin="">
<style>
:root {
  {CSS_VARIABLES}

  --cream: #FDF8F0;
  --cream-dim: #D4C8B8;
  --text: #F0E8E0;
  --text-mid: #B8A898;
  --text-dim: #7A6E64;
  --text-accent: var(--gold);
  --green: #5CAA6E;
  --green-dim: #3A7A4C;
  --red: #D45050;
  --blue: #5A8FD4;
  --border: rgba(212, 165, 116, 0.12);
  --border-gold: rgba(212, 165, 116, 0.25);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 40px rgba(0,0,0,0.5);
  --shadow-gold: 0 0 20px rgba(212, 165, 116, 0.15);
  --glass-bg: rgba(30, 25, 20, 0.85);
  --glass-border: rgba(212, 165, 116, 0.15);
  --glass-blur: blur(20px);
  --surface-raised: #2A2420;
  --surface-glass: rgba(30, 25, 20, 0.75);
  --card-bg: var(--surface);
  --card-hover: var(--surface-raised);
  --sidebar-w: 420px;
  --hero-h: 200px;
  --radius: 12px;
  --radius-sm: 8px;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 15px; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--gold); text-decoration: none; transition: color 0.2s; }
a:hover { color: var(--gold-light); }
button { font-family: var(--font-body); cursor: pointer; border: none; background: none; color: var(--text); }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(212,165,116,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(212,165,116,0.35); }

/* Hero */
.hero {
  position: relative; height: var(--hero-h);
  background: linear-gradient(135deg, var(--bg) 0%, var(--surface) 25%, var(--bg-warm) 50%, var(--bg) 75%, var(--bg) 100%);
  background-size: 300% 300%; animation: heroShift 12s ease-in-out infinite;
  overflow: hidden; z-index: 10;
}
@keyframes heroShift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.hero::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--gold-dark), transparent); }
.hero-content { position: relative; z-index: 1; height: 100%; display: flex; flex-direction: column; justify-content: center; padding: 0 40px; max-width: 1400px; margin: 0 auto; }
.hero-title { font-family: var(--font-display); font-size: 2.4rem; font-weight: 700; color: var(--cream); line-height: 1.1; margin-bottom: 4px; }
.hero-title em { font-style: italic; color: var(--gold); }
.hero-subtitle { font-size: 0.85rem; color: var(--text-mid); font-weight: 300; letter-spacing: 0.03em; margin-bottom: 16px; }
.hero-stats { display: flex; gap: 24px; flex-wrap: wrap; }
.hero-stat { text-align: left; }
.hero-stat-value { font-family: var(--font-display); font-size: 2rem; font-weight: 700; color: var(--gold); line-height: 1; }
.hero-stat-label { font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

/* Toolbar */
.toolbar { position: relative; z-index: 9; padding: 12px 20px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); background: var(--glass-bg); border-bottom: 1px solid var(--border); }
.search-box { position: relative; flex: 0 0 280px; }
.search-box input { width: 100%; padding: 9px 14px 9px 36px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 0.87rem; font-family: var(--font-body); outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
.search-box input::placeholder { color: var(--text-dim); }
.search-box input:focus { border-color: var(--gold-dark); box-shadow: 0 0 0 3px rgba(212,165,116,0.1); }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-dim); font-size: 14px; pointer-events: none; }
.filter-pills { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.pill { padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 500; background: var(--surface); border: 1px solid var(--border); color: var(--text-mid); transition: all 0.2s; white-space: nowrap; user-select: none; }
.pill:hover { border-color: var(--border-gold); color: var(--text); background: var(--surface-raised); }
.pill.active { background: var(--gold-dark); border-color: var(--gold-dark); color: var(--bg); font-weight: 600; }
.sort-select { padding: 7px 30px 7px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 0.8rem; font-family: var(--font-body); outline: none; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 5l3 3 3-3' fill='none' stroke='%237A6E64' stroke-width='1.5'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; cursor: pointer; }
.sort-select:focus { border-color: var(--gold-dark); }
.results-count { font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; margin-left: auto; }

/* Main Layout */
.main-layout { display: flex; height: calc(100vh - var(--hero-h) - 52px); }
.sidebar { width: var(--sidebar-w); min-width: var(--sidebar-w); overflow-y: auto; padding: 12px; background: var(--bg-warm); border-right: 1px solid var(--border); }
.card-list { display: flex; flex-direction: column; gap: 10px; }
.card-list-empty { text-align: center; padding: 60px 20px; color: var(--text-dim); font-size: 0.9rem; }
.card-list-empty .empty-icon { font-size: 2.5rem; margin-bottom: 12px; opacity: 0.4; }

/* Cards */
.shop-card { position: relative; background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 14px 14px 18px; cursor: pointer; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); opacity: 0; transform: translateY(12px); animation: cardEnter 0.4s ease forwards; }
.shop-card::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 3px; border-radius: 0 3px 3px 0; background: var(--text-dim); transition: background 0.2s; }
.shop-card.quality-highlight::before { background: var(--gold); box-shadow: 0 0 8px rgba(212, 165, 116, 0.3); }
.shop-card:hover { background: var(--card-hover); border-color: var(--border-gold); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.shop-card.highlighted { border-color: var(--gold-dark); box-shadow: var(--shadow-gold); }
@keyframes cardEnter { to { opacity: 1; transform: translateY(0); } }
.card-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; }
.card-name { font-size: 0.95rem; font-weight: 600; color: var(--text); flex: 1; line-height: 1.25; }
.card-badges { display: flex; gap: 4px; flex-shrink: 0; }
.badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 7px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; white-space: nowrap; }
.badge-quality { background: rgba(212, 165, 116, 0.15); color: var(--gold); border: 1px solid rgba(212, 165, 116, 0.25); }
.badge-special { background: rgba(92, 170, 110, 0.12); color: var(--green); border: 1px solid rgba(92, 170, 110, 0.2); }
.badge-info { background: rgba(90, 143, 212, 0.12); color: var(--blue); border: 1px solid rgba(90, 143, 212, 0.2); }
.card-address { font-size: 0.78rem; color: var(--text-dim); margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-meta { display: flex; align-items: center; gap: 12px; font-size: 0.78rem; }
.card-rating { display: flex; align-items: center; gap: 4px; color: var(--gold); font-weight: 600; }
.card-rating .star { font-size: 12px; }
.card-reviews { color: var(--text-dim); }
.card-price { color: var(--text-mid); font-weight: 500; }
.card-category { color: var(--text-dim); font-size: 0.72rem; }
.card-signals { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.signal-tag { font-size: 0.67rem; padding: 2px 6px; border-radius: 6px; background: var(--surface); color: var(--text-dim); border: 1px solid var(--border); }
.signal-tag.good { color: var(--green); border-color: rgba(92,170,110,0.2); background: rgba(92,170,110,0.08); }

/* Map */
.map-container { flex: 1; position: relative; }
#map { width: 100%; height: 100%; background: var(--bg); }
.leaflet-tile-pane { filter: brightness(0.75) contrast(1.1) saturate(0.3) sepia(0.15); }
.leaflet-control-zoom a { background: var(--surface) !important; color: var(--text) !important; border-color: var(--border) !important; }
.marker-cluster { background: rgba(212, 165, 116, 0.25) !important; }
.marker-cluster div { background: var(--gold-dark) !important; color: var(--bg) !important; font-family: var(--font-body) !important; font-weight: 700 !important; font-size: 13px !important; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; z-index: 1000; display: none; align-items: center; justify-content: center; padding: 20px; }
.modal-overlay.open { display: flex; }
.modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; } }
.modal-content { position: relative; width: 100%; max-width: 680px; max-height: 85vh; overflow-y: auto; background: var(--glass-bg); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); border: 1px solid var(--glass-border); border-radius: 16px; box-shadow: var(--shadow-lg), var(--shadow-gold); animation: modalIn 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
@keyframes modalIn { from { opacity: 0; transform: translateY(30px) scale(0.97); } }
.modal-close { position: absolute; top: 16px; right: 16px; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.05); color: var(--text-dim); font-size: 18px; z-index: 2; transition: all 0.2s; }
.modal-close:hover { background: rgba(255,255,255,0.1); color: var(--text); }
.modal-header { padding: 28px 28px 0; }
.modal-name { font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--cream); line-height: 1.15; margin-bottom: 4px; }
.modal-address { font-size: 0.85rem; color: var(--text-mid); margin-bottom: 6px; }
.modal-badges { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
.modal-badges .badge { font-size: 0.72rem; padding: 3px 10px; }
.modal-signals { padding: 0 28px 20px; }
.signal-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.signal-row { display: flex; align-items: center; gap: 10px; }
.signal-label { font-size: 0.75rem; color: var(--text-dim); width: 80px; flex-shrink: 0; }
.signal-bars { display: flex; gap: 3px; flex: 1; }
.signal-bar { height: 6px; flex: 1; border-radius: 3px; background: var(--surface); transition: background 0.3s; }
.signal-bar.filled { background: linear-gradient(135deg, var(--gold-dark), var(--gold)); }
.signal-bar.filled.high { background: linear-gradient(135deg, var(--green-dim), var(--green)); }
.modal-section { padding: 16px 28px; border-top: 1px solid var(--border); }
.modal-section-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-dim); margin-bottom: 10px; font-weight: 600; }
.modal-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.modal-detail-item { display: flex; align-items: flex-start; gap: 8px; }
.modal-detail-icon { font-size: 14px; width: 20px; text-align: center; flex-shrink: 0; color: var(--gold); }
.modal-detail-text { font-size: 0.82rem; color: var(--text-mid); line-height: 1.4; }
.modal-detail-text a { color: var(--gold); }
.modal-detail-text a:hover { text-decoration: underline; }
.modal-links { display: flex; gap: 8px; flex-wrap: wrap; }
.modal-link { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 500; background: var(--surface); border: 1px solid var(--border); color: var(--text-mid); transition: all 0.2s; }
.modal-link:hover { border-color: var(--border-gold); color: var(--gold); background: var(--surface-raised); }
.modal-map { height: 180px; border-radius: var(--radius-sm); overflow: hidden; margin-top: 8px; border: 1px solid var(--border); }
.modal-hours-text { font-size: 0.82rem; color: var(--text-mid); line-height: 1.6; white-space: pre-line; }
.modal-atmosphere-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.atmo-tag { padding: 4px 10px; border-radius: 14px; font-size: 0.75rem; background: var(--surface); border: 1px solid var(--border); color: var(--text-mid); }

/* Loading */
.loading-screen { position: fixed; inset: 0; z-index: 2000; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg); transition: opacity 0.5s; }
.loading-screen.hidden { opacity: 0; pointer-events: none; }
.loading-spinner { width: 48px; height: 48px; border: 3px solid var(--border); border-top-color: var(--gold); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-family: var(--font-display); font-size: 1.2rem; color: var(--gold); }

/* Responsive */
@media (max-width: 900px) {
  :root { --sidebar-w: 100%; --hero-h: 170px; }
  .main-layout { flex-direction: column; }
  .sidebar { width: 100%; min-width: 0; height: 50%; border-right: none; border-bottom: 1px solid var(--border); }
  .map-container { height: 50%; }
  .hero-content { padding: 0 20px; }
  .hero-title { font-size: 1.6rem; }
  .hero-stat-value { font-size: 1.4rem; }
  .search-box { flex: 1 1 200px; }
  .modal-overlay { align-items: flex-end; padding: 0; }
  .modal-content { max-height: 92vh; border-radius: 16px 16px 0 0; animation: modalSlideUp 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
  @keyframes modalSlideUp { from { transform: translateY(100%); } }
}
@media (max-width: 600px) {
  .toolbar { padding: 8px 12px; gap: 6px; }
  .filter-pills { gap: 4px; }
  .pill { padding: 5px 10px; font-size: 0.72rem; }
  .hero-stats { gap: 16px; }
}
</style>
</head>
<body>

<div class="loading-screen" id="loadingScreen">
  <div class="loading-spinner"></div>
  <div class="loading-text">{LOADING_TEXT}</div>
</div>

<section class="hero">
  <div class="hero-content">
    <h1 class="hero-title">{HERO_TITLE}</h1>
    <p class="hero-subtitle">{TAGLINE}</p>
    <div class="hero-stats">
      {HERO_STATS}
    </div>
  </div>
</section>

<div class="toolbar">
  <div class="search-box">
    <span class="search-icon">&#x1F50D;</span>
    <input type="text" id="searchInput" placeholder="Search name, address, vibe...">
  </div>
  <div class="filter-pills">
    {FILTER_PILLS}
  </div>
  <select class="sort-select" id="sortSelect">
    {SORT_OPTIONS}
  </select>
  <span class="results-count" id="resultsCount"></span>
</div>

<div class="main-layout">
  <div class="sidebar" id="sidebar">
    <div class="card-list" id="cardList"></div>
  </div>
  <div class="map-container">
    <div id="map"></div>
  </div>
</div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal-backdrop" id="modalBackdrop"></div>
  <div class="modal-content" id="modalContent"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js" crossorigin=""></script>
<script>
const state = {
  allShops: [], filtered: [], filters: new Set(), searchQuery: '', sortBy: 'rating',
  map: null, markers: null, markerMap: {}, modalMap: null, highlightedId: null,
};

async function loadData() {
  const resp = await fetch('{DATA_FILENAME}');
  if (!resp.ok) throw new Error(`Failed to load data: ${resp.status}`);
  const raw = await resp.json();
  return raw.map(normalize).filter(s => s.lat && s.lng);
}

function normalize(row) {
  const s = { ...row };
  // Common numeric coercion
  s.lat = parseFloat(s.lat) || 0;
  s.lng = parseFloat(s.lng) || 0;
  s.rating = parseFloat(s.rating) || 0;
  s.review_count = parseInt(s.review_count) || 0;
  s.quality_signal = parseInt(s.quality_signal) || 0;
  s.ambience_signal = parseInt(s.ambience_signal) || 0;
  s.value_signal = parseInt(s.value_signal) || 0;
  s.service_signal = parseInt(s.service_signal) || 0;
  s.crowdedness_signal = parseInt(s.crowdedness_signal) || 0;
  s.query_hit_count = parseInt(s.query_hit_count) || 0;

  // Common string normalization
  s.place_name = (s.place_name || '').trim();
  s.full_address = (s.full_address || '').trim();
  s.street_address = (s.street_address || '').trim();
  s.primary_category = (s.primary_category || '').trim();
  s.all_categories = (s.all_categories || '').trim();
  s.atmosphere = (s.atmosphere || '').trim();
  s.highlights = (s.highlights || '').trim();
  s.offerings = (s.offerings || '').trim();
  s.price_level = (s.price_level || '').trim();
  s.status = (s.status || 'open').toLowerCase();

  // Enrichment fields
  s.website_url = (s.website_url || s.website || '').trim();
  s.instagram_url = (s.instagram_url || '').trim();
  s.facebook_url = (s.facebook_url || '').trim();
  s.tiktok_url = (s.tiktok_url || '').trim();
  s.crawl_phone = (s.crawl_phone || '').trim();
  s.crawl_email = (s.crawl_email || '').trim();
  s.crawl_hours = (s.crawl_hours || '').trim();
  s.crawl_menu_url = (s.crawl_menu_url || '').trim();
  s.crawl_reservation_url = (s.crawl_reservation_url || '').trim();

  // Booleans
  s.borderline = s.borderline === true || s.borderline === 'true' || s.borderline === 'TRUE';
  s.sponsored = s.sponsored === true || s.sponsored === 'true' || s.sponsored === 'TRUE';

  // Common derived
  s.isHighRated = s.rating >= 4.5;
  s.isOpen = s.status === 'open';
  s.bestPhone = s.crawl_phone || (s.phone || '').trim() || '';

  // Category-specific normalization
  {NORMALIZE_FIELDS}

  // Search blob
  s._searchBlob = [
    s.place_name, s.full_address, s.primary_category,
    s.all_categories, s.atmosphere, s.highlights, s.offerings,
  ].join(' ').toLowerCase();

  // URL-safe slug for deep linking
  s._slug = s.place_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

  return s;
}

function applyFilters() {
  let shops = state.allShops.filter(s => s.isOpen && !s.borderline);

  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    shops = shops.filter(s => s._searchBlob.includes(q));
  }

  for (const f of state.filters) {
    switch (f) {
      case 'highrated': shops = shops.filter(s => s.isHighRated); break;
      {FILTER_LOGIC}
    }
  }

  switch (state.sortBy) {
    case 'rating':
      shops.sort((a, b) => b.rating - a.rating || b.review_count - a.review_count);
      break;
    case 'reviews':
      shops.sort((a, b) => b.review_count - a.review_count);
      break;
    case 'name':
      shops.sort((a, b) => a.place_name.localeCompare(b.place_name));
      break;
    {SORT_LOGIC}
  }

  state.filtered = shops;
  renderCards();
  renderMap();
  document.getElementById('resultsCount').textContent = `${shops.length} spots`;
}

function renderCards() {
  const list = document.getElementById('cardList');
  if (state.filtered.length === 0) {
    list.innerHTML = `<div class="card-list-empty"><div class="empty-icon">{EMPTY_ICON}</div><div>{EMPTY_TEXT}</div></div>`;
    return;
  }

  list.innerHTML = state.filtered.map((s, i) => {
    const badges = [];
    {CARD_BADGES}

    const signals = [];
    {CARD_SIGNALS}
    if (s.atmosphere) {
      s.atmosphere.split(',').map(a => a.trim()).filter(Boolean).slice(0, 2)
        .forEach(a => signals.push(`<span class="signal-tag">${escHtml(a)}</span>`));
    }

    return `
      <div class="shop-card ${({QUALITY_CHECK}) ? 'quality-highlight' : ''} ${s.place_id === state.highlightedId ? 'highlighted' : ''}"
           data-id="${s.place_id}" style="animation-delay: ${Math.min(i * 30, 600)}ms"
           onclick="openModal('${s.place_id}')">
        <div class="card-header">
          <div class="card-name">${escHtml(s.place_name)}</div>
          <div class="card-badges">${badges.join('')}</div>
        </div>
        <div class="card-address">${escHtml(s.street_address || s.full_address)}</div>
        <div class="card-meta">
          <span class="card-rating"><span class="star">&#x2605;</span> ${s.rating.toFixed(1)}</span>
          <span class="card-reviews">(${s.review_count.toLocaleString()})</span>
          ${s.price_level ? `<span class="card-price">${escHtml(s.price_level)}</span>` : ''}
          <span class="card-category">${escHtml(s.primary_category)}</span>
        </div>
        ${signals.length ? `<div class="card-signals">${signals.join('')}</div>` : ''}
      </div>`;
  }).join('');
}

function initMap() {
  state.map = L.map('map', { center: [{MAP_CENTER_LAT}, {MAP_CENTER_LNG}], zoom: {MAP_ZOOM}, zoomControl: true, attributionControl: false });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19, subdomains: 'abcd' }).addTo(state.map);
  L.control.attribution({ prefix: false }).addTo(state.map);
  state.map.attributionControl.addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>');

  state.markers = L.markerClusterGroup({
    maxClusterRadius: 45, spiderfyOnMaxZoom: true, showCoverageOnHover: false,
    iconCreateFunction: function(cluster) {
      const count = cluster.getChildCount();
      let size = count < 10 ? 36 : count < 30 ? 42 : 50;
      return L.divIcon({
        html: `<div style="width:${size}px;height:${size}px;line-height:${size}px;text-align:center;border-radius:50%;background:rgba(184,137,74,0.9);color:#0F0B08;font-weight:700;font-size:13px;font-family:Inter,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.3)">${count}</div>`,
        className: 'custom-cluster', iconSize: [size, size],
      });
    },
  });
  state.map.addLayer(state.markers);
}

function createMarkerIcon(shop) {
  const isQuality = {QUALITY_CHECK};
  const color = isQuality ? 'var(--gold)' : 'var(--amber, #C4843C)';
  const colorHex = isQuality ? '#D4A574' : '#C4843C';
  const glow = isQuality ? 'filter: drop-shadow(0 0 4px rgba(212,165,116,0.5));' : '';
  const symbol = isQuality
    ? `<polygon points="12,2 15,9 22,9 16,14 18,21 12,17 6,21 8,14 2,9 9,9" fill="${colorHex}"/>`
    : `<circle cx="12" cy="12" r="8" fill="${colorHex}" stroke="#1A1410" stroke-width="2"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" style="${glow}">${symbol}</svg>`;
  return L.divIcon({ html: svg, className: 'custom-marker', iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -12] });
}

function renderMap() {
  state.markers.clearLayers();
  state.markerMap = {};
  state.filtered.forEach(shop => {
    if (!shop.lat || !shop.lng) return;
    const marker = L.marker([shop.lat, shop.lng], { icon: createMarkerIcon(shop) });
    marker.bindPopup(`
      <div style="font-family:Inter,sans-serif;color:#1A1410;min-width:180px">
        <div style="font-weight:600;font-size:14px;margin-bottom:4px">${escHtml(shop.place_name)}</div>
        <div style="font-size:12px;color:#6B5344;margin-bottom:4px">${escHtml(shop.street_address)}</div>
        <div style="font-size:12px">
          <span style="color:#D4A574;font-weight:600">&#x2605; ${shop.rating.toFixed(1)}</span>
          <span style="color:#9B8B7E;margin-left:4px">(${shop.review_count})</span>
        </div>
      </div>`, { closeButton: false, className: 'custom-popup' });
    marker.on('click', () => { highlightCard(shop.place_id); openModal(shop.place_id); });
    marker.shopId = shop.place_id;
    state.markerMap[shop.place_id] = marker;
    state.markers.addLayer(marker);
  });
}

function highlightCard(placeId) {
  state.highlightedId = placeId;
  document.querySelectorAll('.shop-card').forEach(card => {
    card.classList.toggle('highlighted', card.dataset.id === placeId);
  });
  const card = document.querySelector(`.shop-card[data-id="${placeId}"]`);
  if (card) card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function panToShop(placeId) {
  const marker = state.markerMap[placeId];
  if (marker) { state.map.setView(marker.getLatLng(), 16, { animate: true }); marker.openPopup(); }
}

function openModal(placeId) {
  const shop = state.allShops.find(s => s.place_id === placeId);
  if (!shop) return;
  history.replaceState(null, '', `#shop=${shop._slug}`);
  const overlay = document.getElementById('modalOverlay');
  const content = document.getElementById('modalContent');

  const badges = [];
  {MODAL_BADGES}

  const signals = [{MODAL_SIGNALS}];
  const signalHtml = signals.map(sig => {
    const bars = Array.from({ length: sig.max }, (_, i) => {
      const filled = i < sig.val;
      const isHigh = filled && sig.val >= 2;
      return `<div class="signal-bar ${filled ? 'filled' : ''} ${isHigh ? 'high' : ''}"></div>`;
    }).join('');
    return `<div class="signal-row"><span class="signal-label">${sig.label}</span><div class="signal-bars">${bars}</div></div>`;
  }).join('');

  // Contact details
  const details = [];
  if (shop.bestPhone) details.push({ icon: '&#x1F4DE;', text: `<a href="tel:${shop.bestPhone}">${escHtml(shop.bestPhone)}</a>` });
  if (shop.crawl_email) details.push({ icon: '&#x2709;', text: `<a href="mailto:${shop.crawl_email}">${escHtml(shop.crawl_email)}</a>` });
  if (shop.price_level) details.push({ icon: '&#x1F4B0;', text: shop.price_level });
  if (shop.primary_category) details.push({ icon: '&#x1F4CD;', text: escHtml(shop.primary_category) });

  const detailsHtml = details.length ? `<div class="modal-section"><div class="modal-section-title">Details</div><div class="modal-detail-grid">${details.map(d => `<div class="modal-detail-item"><span class="modal-detail-icon">${d.icon}</span><span class="modal-detail-text">${d.text}</span></div>`).join('')}</div></div>` : '';

  // Links
  const links = [];
  if (shop.website_url) links.push({ icon: '&#x1F310;', label: 'Website', url: shop.website_url });
  if (shop.instagram_url) links.push({ icon: '&#x1F4F7;', label: 'Instagram', url: shop.instagram_url });
  if (shop.facebook_url) links.push({ icon: '&#x1F44D;', label: 'Facebook', url: shop.facebook_url });
  if (shop.tiktok_url) links.push({ icon: '&#x1F3B5;', label: 'TikTok', url: shop.tiktok_url });
  if (shop.google_maps_url) links.push({ icon: '&#x1F4CD;', label: 'Google Maps', url: shop.google_maps_url });
  if (shop.crawl_menu_url) links.push({ icon: '&#x1F4CB;', label: 'Menu', url: shop.crawl_menu_url });
  if (shop.crawl_reservation_url) links.push({ icon: '&#x1F4C5;', label: 'Reserve', url: shop.crawl_reservation_url });
  {MODAL_LINKS}

  const linksHtml = links.length ? `<div class="modal-section"><div class="modal-section-title">Links</div><div class="modal-links">${links.map(l => `<a class="modal-link" href="${escAttr(l.url)}" target="_blank" rel="noopener">${l.icon} ${l.label}</a>`).join('')}</div></div>` : '';

  const hoursHtml = shop.crawl_hours ? `<div class="modal-section"><div class="modal-section-title">Hours</div><div class="modal-hours-text">${escHtml(shop.crawl_hours).replace(/;/g, '\n').replace(/\|/g, '\n')}</div></div>` : '';

  const atmoTags = [];
  if (shop.atmosphere) shop.atmosphere.split(',').map(a => a.trim()).filter(Boolean).forEach(a => atmoTags.push(a));
  if (shop.highlights) shop.highlights.split(',').map(h => h.trim()).filter(Boolean).forEach(h => atmoTags.push(h));
  const atmoHtml = atmoTags.length ? `<div class="modal-section"><div class="modal-section-title">Atmosphere & Highlights</div><div class="modal-atmosphere-tags">${atmoTags.map(t => `<span class="atmo-tag">${escHtml(t)}</span>`).join('')}</div></div>` : '';

  content.innerHTML = `
    <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    <div class="modal-header">
      <div class="modal-name">${escHtml(shop.place_name)}</div>
      <div class="modal-address">${escHtml(shop.full_address)}</div>
      <div class="modal-badges">${badges.join('')}</div>
      <div class="card-meta" style="margin-bottom:4px">
        <span class="card-rating" style="font-size:1rem"><span class="star">&#x2605;</span> ${shop.rating.toFixed(1)}</span>
        <span class="card-reviews" style="font-size:0.85rem">(${shop.review_count.toLocaleString()} reviews)</span>
      </div>
    </div>
    <div class="modal-signals"><div class="signal-grid">${signalHtml}</div></div>
    ${detailsHtml}${linksHtml}${hoursHtml}${atmoHtml}
    <div class="modal-section"><div class="modal-section-title">Location</div><div class="modal-map" id="modalMapEl"></div></div>`;

  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  requestAnimationFrame(() => {
    if (state.modalMap) { state.modalMap.remove(); state.modalMap = null; }
    const mapEl = document.getElementById('modalMapEl');
    if (mapEl && shop.lat && shop.lng) {
      state.modalMap = L.map(mapEl, { center: [shop.lat, shop.lng], zoom: 16, zoomControl: false, dragging: false, scrollWheelZoom: false, attributionControl: false });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19, subdomains: 'abcd' }).addTo(state.modalMap);
      L.marker([shop.lat, shop.lng], { icon: createMarkerIcon(shop) }).addTo(state.modalMap);
    }
  });

  highlightCard(placeId);
  panToShop(placeId);
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
  history.replaceState(null, '', window.location.pathname);
  if (state.modalMap) { state.modalMap.remove(); state.modalMap = null; }
}

function animateCounter(el, target, duration = 1200, isDecimal = false) {
  const start = performance.now();
  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = isDecimal ? (target * ease).toFixed(1) : Math.round(target * ease);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function updateHeroStats() {
  // Implemented per-category in the generated webapp
  {HERO_STATS_JS}
}

function setupEvents() {
  const searchInput = document.getElementById('searchInput');
  let searchTimeout;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => { state.searchQuery = searchInput.value.trim(); applyFilters(); }, 200);
  });

  document.querySelectorAll('.pill[data-filter]').forEach(pill => {
    pill.addEventListener('click', () => {
      const filter = pill.dataset.filter;
      if (state.filters.has(filter)) { state.filters.delete(filter); pill.classList.remove('active'); }
      else { state.filters.add(filter); pill.classList.add('active'); }
      applyFilters();
    });
  });

  document.getElementById('sortSelect').addEventListener('change', (e) => { state.sortBy = e.target.value; applyFilters(); });
  document.getElementById('modalBackdrop').addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
  checkDeepLink();
  window.addEventListener('hashchange', checkDeepLink);
}

function checkDeepLink() {
  const match = window.location.hash.match(/^#shop=(.+)$/);
  if (match) {
    const shop = state.allShops.find(s => s._slug === match[1]);
    if (shop) setTimeout(() => openModal(shop.place_id), 300);
  }
}

function escHtml(str) { const div = document.createElement('div'); div.textContent = str || ''; return div.innerHTML; }
function escAttr(str) { return (str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

async function init() {
  try {
    initMap();
    state.allShops = await loadData();
    updateHeroStats();
    applyFilters();
    setupEvents();
    const loader = document.getElementById('loadingScreen');
    loader.classList.add('hidden');
    setTimeout(() => loader.remove(), 500);
  } catch (err) {
    console.error('Failed to initialize:', err);
    document.getElementById('loadingScreen').innerHTML = `
      <div style="text-align:center;color:var(--red);padding:40px">
        <div style="font-size:2rem;margin-bottom:12px">&#x26A0;</div>
        <div style="font-size:1rem;margin-bottom:8px">Failed to load data</div>
        <div style="font-size:0.8rem;color:var(--text-dim)">${escHtml(err.message)}</div>
        <div style="font-size:0.75rem;color:var(--text-dim);margin-top:12px">
          Make sure <code>{DATA_FILENAME}</code> is in the same directory.
        </div>
      </div>`;
  }
}

init();
</script>
</body>
</html>
````

## Category Customization Guide

When generating a webapp from this template, fill in these category-specific blocks:

### Hero Stats (HTML + JS)

**Coffee example:**
```html
<div class="hero-stat"><div class="hero-stat-value" data-counter="spots">0</div><div class="hero-stat-label">Coffee Spots</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="rating">0</div><div class="hero-stat-label">Avg Rating</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="roasters">0</div><div class="hero-stat-label">Roasters</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="wifi">0</div><div class="hero-stat-label">WiFi Spots</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="thirdwave">0</div><div class="hero-stat-label">Third Wave</div></div>
```

**Restaurant example:**
```html
<div class="hero-stat"><div class="hero-stat-value" data-counter="spots">0</div><div class="hero-stat-label">Restaurants</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="rating">0</div><div class="hero-stat-label">Avg Rating</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="finedining">0</div><div class="hero-stat-label">Fine Dining</div></div>
<div class="hero-stat"><div class="hero-stat-value" data-counter="outdoor">0</div><div class="hero-stat-label">Outdoor</div></div>
```

### Filter Pills (HTML)

Generate `<button class="pill" data-filter="filtername">Label</button>` elements based on category-relevant filters. Examples:
- Coffee: Third Wave, WiFi, Roasters, 4.5+, Work Friendly, Outdoor, $
- Restaurant: Fine Dining, Outdoor, Family, Delivery, 4.5+, $$$$
- Bar: Craft Cocktails, Beer, Wine, Late Night, Live Music, 4.5+
- Fitness: Classes, Personal Training, Equipment, Community, 4.5+

### Sort Options (HTML)

Generate `<option value="key">Sort: Label</option>` elements. Always include rating, reviews, and name. Add category-specific sorts:
- Coffee: Third Wave Score, Coffee Quality
- Restaurant: Cuisine Quality, Fine Dining
- Bar: Craft Score, Cocktail Focus
- Fitness: Specialty Score, Community

### Normalize Fields (JS)

Category-specific field coercion in the `normalize()` function. Example for coffee:
```javascript
s.third_wave_score = parseInt(s.third_wave_score) || 0;
s.coffee_quality_signal = parseInt(s.coffee_quality_signal) || 0;
s.work_friendly_signal = parseInt(s.work_friendly_signal) || 0;
s.wifi = (s.wifi || 'unknown').toLowerCase();
s.is_roaster = (s.is_roaster || 'no').toLowerCase();
s.outdoor_seating = (s.outdoor_seating || 'unknown').toLowerCase();
s.isThirdWave = s.third_wave_score >= 5;
s.isRoaster = s.is_roaster === 'yes' || s.is_roaster === 'likely';
s.hasWifi = s.wifi === 'yes';
s.isWorkFriendly = s.work_friendly_signal >= 2;
s.hasOutdoor = s.outdoor_seating === 'yes';
s.isCheap = s.price_level === '$';
```

### Modal Signals (JS)

Array of signal bar configs. Example for coffee:
```javascript
{ label: 'Coffee', val: shop.coffee_quality_signal, max: 3 },
{ label: 'Ambience', val: shop.ambience_signal, max: 3 },
{ label: 'Service', val: shop.service_signal, max: 3 },
{ label: 'Value', val: shop.value_signal, max: 3 },
{ label: 'Work Vibe', val: shop.work_friendly_signal, max: 3 },
{ label: 'Crowds', val: shop.crowdedness_signal, max: 3 },
```
