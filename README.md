# Drichsearch

Mini navigateur en PyQt5 avec panneau d’assistant IA (Gradio), recherche multi-moteurs et empaquetage macOS/Windows.

## Fonctionnalités
- Page d’accueil, sélection du moteur, barre de recherche et résultats via QWebEngineView.
- Mode « Personnalisé »: comparaison DuckDuckGo et Yahoo (scrapers dans `services/search.py`).
- Panneau de chat (droite) connecté à un modèle Gradio (`services/model.py`), avec loader et statuts.
- Résolution des chemins de ressources compatible PyInstaller (icônes, JSON de configuration).

## Prérequis
- Python 3.10 (recommandé) + venv.
- macOS: `sips`, `iconutil` (natifs) pour générer un `.icns` si besoin.
- Windows: un fichier `.ico` pour l’icône du bundle.

## Installation
```bash
git clone <link>
cd mybrowser
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Configuration
- Fichier des moteurs: `config/search_engines.json`
  Exemple minimal:
  ```json
  [
    {"name": "Personnalisé", "url": "custom", "logo": "assets/duckduckgo.svg"},
    {"name": "Google", "url": "https://www.google.com/search?q=", "logo": "assets/google.svg"},
    {"name": "Bing", "url": "https://www.bing.com/search?q=", "logo": "assets/bing.svg"}
  ]
  ```

- Icônes et assets: dossier `assets/`
  - `logo.svg` (utilisé par l’UI). Fallback `logo.png`.
  - `logo.icns` (macOS) et `logo.ico` (Windows) pour le bundle.
  - `loader.gif` (optionnel) pour l’animation pendant la génération.

## Modèle IA (Gradio)
Worker: `services/model.py` (Gradio Client, Espace par défaut: `Drichdev/micro-btnet-user`).
- Paramètres côté UI (voir `MainWindow._run_model_in_background`) : `use_web_search=True`, `max_length=200`, `temperature=0.7`.

## Lancement (développement)
```bash
python main.py
```

## Packaging / Build
Des scripts sont fournis dans `scripts/`.

### macOS (.app + .dmg)
```bash
chmod +x scripts/build_mac.sh
./scripts/build_mac.sh
```
Sorties:
- Application: `dist/Drichsearch.app`
- DMG: `dist/Drichsearch.dmg`

Si besoin d’un `.icns` et que vous avez un PNG: placez `assets/logo.png` (1024x1024 recommandé); le script générera `assets/logo.icns`.

Build manuel (alternative):
```bash
pyinstaller \
  --noconfirm \
  --windowed \
  --name Drichsearch \
  --icon assets/logo.icns \
  --add-data "assets:assets" \
  --add-data "config:config" \
  --collect-submodules PyQt5.QtWebEngine \
  --collect-data PyQt5.QtWebEngine \
  main.py
```

### Windows (.exe)
```bat
scripts\build_win.bat
```
Sortie: `dist\Drichsearch\Drichsearch.exe`

Build manuel (alternative):
```bat
pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name Drichsearch ^
  --icon assets\logo.ico ^
  --add-data "assets;assets" ^
  --add-data "config;config" ^
  --collect-submodules PyQt5.QtWebEngine ^
  --collect-data PyQt5.QtWebEngine ^
  main.py
```

## Chemins de ressources (PyInstaller)
`ui/window.py` utilise un helper pour résoudre les chemins en binaire:
```python
def _resource_path(self, *paths):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, *paths)
```
Utilisé pour:
- Icône d’application: `assets/logo.svg` (fallback `assets/logo.png`)
- Fichier de configuration: `config/search_engines.json`

Assurez-vous d’inclure `assets` et `config` via `--add-data`.

## Dépannage
- Page web vide après build: vérifier l’inclusion de QtWebEngine
  - `--collect-submodules PyQt5.QtWebEngine` et `--collect-data PyQt5.QtWebEngine`.
- `config/search_engines.json` introuvable dans l’app packagée:
  - Vérifier qu’il est bien en `dist/.../config/` et que l’accès passe par `_resource_path`.
- Icône bundle (macOS): `.icns` requis (génération possible via script mac).
- Icône bundle (Windows): `.ico` requis.
