import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from services.search import scrape_duckduckgo, scrape_yahoo, generate_results_html
from services.model import ModelWorker
from PyQt5.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QStackedWidget,
    QTextEdit,
    QSplitter,
    QLabel,
)
from PyQt5.QtGui import QIcon, QFont, QMovie
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSignal, QThread
from PyQt5.QtWebEngineWidgets import QWebEngineView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My browser")
        self.setGeometry(500, 300, 1200, 700)
        
        # Définir le logo de l'application (support PyInstaller via _MEIPASS)
        svg_path = self._resource_path("assets", "logo.svg")
        png_path = self._resource_path("assets", "logo.png")
        app_icon = QIcon(svg_path)
        if app_icon.isNull() and os.path.exists(png_path):
            app_icon = QIcon(png_path)
        self.setWindowIcon(app_icon)

        self.stack = QStackedWidget()  # Stack pour changer de page
        self.setCentralWidget(self.stack)

        self.init_ui()

    def init_ui(self):
        # Charger les moteurs de recherche depuis le JSON
        search_engines = self.load_search_engines()
        if not search_engines:
            QMessageBox.critical(self, "Erreur", "Aucun moteur de recherche trouvé.")
            return

        # Page d'accueil
        self.home_page = QWidget()
        home_layout = QVBoxLayout()
        self.home_page.setLayout(home_layout)
        home_layout.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(self.home_page)

        # Menu déroulant pour les moteurs de recherche
        self.search_engine_selector = QComboBox()
        for engine in search_engines:
            logo_path = engine.get("logo", "")
            if os.path.exists(logo_path):
                icon = QIcon(logo_path)
            else:
                icon = QIcon()
            self.search_engine_selector.addItem(icon, engine["name"], engine["url"])
        home_layout.addWidget(self.search_engine_selector, alignment=Qt.AlignCenter)

        # Barre de recherche + bouton
        search_layout = QHBoxLayout()
        search_layout.setAlignment(Qt.AlignCenter)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher")
        self.search_bar.setFont(QFont("Arial", 14))
        self.search_bar.setFixedWidth(400)
        self.search_bar.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_bar)

        search_button = QPushButton(QIcon("assets/search.svg"), "")
        search_button.setFixedSize(40, 40)
        search_button.clicked.connect(self.search)
        search_layout.addWidget(search_button)

        home_layout.addLayout(search_layout)

        # Page de résultats
        self.results_page = QWidget()
        results_layout = QVBoxLayout()
        self.results_page.setLayout(results_layout)

        # Barre de navigation pour la page de résultats
        nav_layout = QHBoxLayout()

        # Bouton précédent
        prev_button = QPushButton(QIcon("assets/precedent.svg"), "")
        prev_button.setFixedSize(40, 40)
        prev_button.clicked.connect(self.go_back)
        nav_layout.addWidget(prev_button)

        # Bouton next
        next_button = QPushButton(QIcon("assets/next.svg"), "")
        next_button.setFixedSize(40, 40)
        next_button.clicked.connect(self.go_forward)
        nav_layout.addWidget(next_button)

        # Input de recherche modifiable
        self.results_search_bar = QLineEdit()
        self.results_search_bar.setPlaceholderText("Rechercher")
        self.results_search_bar.setFont(QFont("Arial", 12))
        self.results_search_bar.returnPressed.connect(self.search_from_results)
        nav_layout.addWidget(self.results_search_bar)

        # Bouton reload
        reload_button = QPushButton(QIcon("assets/reload.svg"), "")
        reload_button.setFixedSize(40, 40)
        reload_button.clicked.connect(self.reload_page)
        nav_layout.addWidget(reload_button)

        results_layout.addLayout(nav_layout)

        splitter = QSplitter(Qt.Horizontal)
        self.results_view = QWebEngineView()
        splitter.addWidget(self.results_view)

        self.model_panel = QWidget()
        model_layout = QVBoxLayout()
        self.model_panel.setLayout(model_layout)

        self.model_history = QTextEdit()
        self.model_history.setReadOnly(True)
        model_layout.addWidget(self.model_history)

        # Loader (spinner) pour la génération du modèle
        self.model_loader = QLabel()
        self.model_loader.setAlignment(Qt.AlignCenter)
        loader_path = os.path.join("assets", "loader.gif")
        if os.path.exists(loader_path):
            self._loader_movie = QMovie(loader_path)
            self.model_loader.setMovie(self._loader_movie)
        else:
            self._loader_movie = None
            self.model_loader.setText("⏳ Génération en cours...")
        self.model_loader.setVisible(False)
        model_layout.addWidget(self.model_loader)

        model_input_layout = QHBoxLayout()
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Demander au modèle...")
        self.model_input.returnPressed.connect(self.on_model_prompt_send)
        send_btn = QPushButton(QIcon("assets/send.svg"), "")
        send_btn.setFixedSize(40, 40)
        send_btn.clicked.connect(self.on_model_prompt_send)
        model_input_layout.addWidget(self.model_input)
        model_input_layout.addWidget(send_btn)
        model_layout.addLayout(model_input_layout)

        splitter.addWidget(self.model_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        results_layout.addWidget(splitter)

        self.stack.addWidget(self.results_page)

    def search(self):
        """
        Méthode déclenchée lors d'une recherche.
        Utilise le moteur sélectionné ou le mode Personnalisé (DuckDuckGo + Yahoo).
        """
        query = self.search_bar.text().strip()
        selected_engine = self.search_engine_selector.currentData()
        selected_name = self.search_engine_selector.currentText()

        if query:
            try:
                self.results_search_bar.setText(query)
                self.results_search_bar.setEnabled(False)
                self.results_search_bar.setPlaceholderText("Chargement...")
                
                # Si "Personnalisé" est sélectionné, scraper DuckDuckGo et Yahoo
                if selected_engine == "custom":
                    ddg_results = scrape_duckduckgo(query)
                    yahoo_results = scrape_yahoo(query)
                    html = generate_results_html(ddg_results, yahoo_results, "DuckDuckGo", "Yahoo")
                else:
                    # Sinon, utiliser le moteur sélectionné
                    search_url = f"{selected_engine}{query}"
                    self.results_view.setUrl(QUrl(search_url))
                    self.stack.setCurrentWidget(self.results_page)
                    self.results_search_bar.setEnabled(True)
                    self.results_search_bar.setPlaceholderText("Rechercher")
                    return
                
                # Afficher les résultats personnalisés
                self.results_view.setHtml(html)
                self.stack.setCurrentWidget(self.results_page)
                
                self.results_search_bar.setEnabled(True)
                self.results_search_bar.setPlaceholderText("Rechercher")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")
                self.results_search_bar.setEnabled(True)
                self.results_search_bar.setPlaceholderText("Rechercher")
        else:
            QMessageBox.warning(self, "Attention", "Le champ de recherche est vide.")

    def search_from_results(self):
        """
        Méthode pour chercher depuis la page de résultats.
        """
        query = self.results_search_bar.text().strip()
        self.search_bar.setText(query)
        self.search()

    def append_model_message(self, role, text):
        self.model_history.append(f"<b>{role}:</b> {text}")

    def on_model_prompt_send(self):
        prompt = self.model_input.text().strip()
        if not prompt:
            return
        self.model_input.setEnabled(False)
        self.append_model_message("Vous", prompt)
        self.model_input.clear()
        self._run_model_in_background(prompt)

    def _run_model_in_background(self, prompt):
        self._model_thread = QThread()
        # Utilise le worker basé sur votre Espace Gradio (voir services/model.py)
        self._worker = ModelWorker(
            prompt=prompt,
            use_web_search=True,
            max_length=200,
            temperature=0.7
        )
        self._worker.moveToThread(self._model_thread)
        self._model_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_model_response)
        self._worker.error.connect(self._on_model_error)
        # Optionnel: écoute des messages de progression du worker
        if hasattr(self._worker, "progress"):
            self._worker.progress.connect(self._on_model_progress)
        self._worker.finished.connect(self._model_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._model_thread.finished.connect(self._model_thread.deleteLater)

        # Afficher le loader
        self.model_loader.setVisible(True)
        if self._loader_movie is not None:
            self._loader_movie.start()
        self._model_thread.start()

    def _on_model_response(self, text):
        # Masquer le loader
        if self._loader_movie is not None:
            self._loader_movie.stop()
        self.model_loader.setVisible(False)

        formatted = self._format_model_text(text)
        self.append_model_message("Modèle", formatted)
        self.model_input.setEnabled(True)

    def _on_model_error(self, err):
        # Masquer le loader
        if self._loader_movie is not None:
            self._loader_movie.stop()
        self.model_loader.setVisible(False)
        QMessageBox.critical(self, "Erreur", err)
        self.model_input.setEnabled(True)

    def _on_model_progress(self, msg):
        # Affiche les status dans l'historique pour feedback utilisateur
        self.append_model_message("Statut", msg)

    def _format_model_text(self, text: str) -> str:
        """
        Formate le texte du modèle pour un rendu plus lisible dans QTextEdit (HTML).
        - Convertit les URLs // en https://
        - Ajoute des retours à la ligne entre les éléments de résultats
        - Transforme l'en-tête des résultats de recherche
        """
        if not text:
            return ""

        # Normaliser les URLs commençant par //
        text = re.sub(r"\(//", "(https://", text)
        text = re.sub(r'\shref=\"//', ' href="https://', text)

        # Titre des résultats de recherche
        text = text.replace("🔍 **Résultats de recherche :**", "<h3>🔍 Résultats de recherche</h3>")

        # Insérer des sauts de ligne avant les items numérotés en gras **1. ...**, **2. ...**
        text = re.sub(r"\*\*(\d+\.)\s*", r"<br><b>\1 </b>", text)

        # Remplacer les doubles espaces sans signification (collages) par un espace simple
        text = re.sub(r"(?<!\S)([A-Za-zÀ-ÿ])(?=\S)", r"\1", text)  # minimal

        return text

    def scrape_duckduckgo(self, query):
        """
        Scrape les résultats de DuckDuckGo avec la bibli duckduckgo-search.
        """
        try:
            results = []
            # Utiliser la bibli duckduckgo-search
            with DDGS() as ddgs:
                ddg_results = ddgs.text(query, max_results=5)
                print(f"DuckDuckGo: {len(list(ddg_results))} résultats trouvés")
                # Réinitialiser le générateur
                with DDGS() as ddgs:
                    for result in ddgs.text(query, max_results=5):
                        try:
                            results.append({
                                'title': result.get('title', ''),
                                'link': result.get('href', ''),
                                'snippet': result.get('body', '')
                            })
                            print(f"  - {result.get('title', '')[:50]}...")
                        except Exception as e:
                            print(f"Erreur parsing DDG result: {e}")
                            continue
            print(f"DuckDuckGo: {len(results)} résultats parsés")
            return results
        except Exception as e:
            print(f"Erreur DuckDuckGo: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_yahoo(self, query):
        """
        Scrape les résultats de Yahoo.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            url = f"https://search.yahoo.com/search?p={query}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            print(f"Yahoo: HTML reçu, taille: {len(response.content)}")
            # Chercher les résultats dans les divs avec classe 'algo'
            search_items = soup.find_all('div', class_='algo')
            print(f"Yahoo: {len(search_items)} résultats trouvés")
            for item in search_items[:5]:
                try:
                    # Lien et titre
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue
                    link = link_elem.get('href', '')
                    if not link.startswith('http'):
                        continue
                    title = link_elem.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue
                    # Description
                    description = ""
                    desc_elem = item.find('div', class_='compText')
                    if not desc_elem:
                        desc_elem = item.find(['p', 'div'])
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    results.append({
                        'title': title,
                        'link': link,
                        'snippet': description[:200] if description else "Pas de description"
                    })
                    print(f"  - {title[:50]}...")
                except Exception as e:
                    print(f"Erreur parsing Yahoo item: {e}")
                    continue
            print(f"Yahoo: {len(results)} résultats parsés")
            return results
        except Exception as e:
            print(f"Erreur Yahoo: {e}")
            import traceback
            traceback.print_exc()
            return []

    def generate_results_html(self, first_results, second_results, first_name="DuckDuckGo", second_name="Yahoo"):
        """
        Génère le HTML avec les résultats en deux colonnes.
        """
        second_name = "Yahoo"
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    display: flex;
                    gap: 20px;
                }
                .column {
                    flex: 1;
                    background-color: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .column h2 {
                    border-bottom: 2px solid #4285F4;
                    padding-bottom: 10px;
                    margin-top: 0;
                }
                .bing h2 {
                    border-bottom: 2px solid #7B0099;
                }
                .ddg h2 {
                    border-bottom: 2px solid #DE5833;
                }
                .result {
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                }
                .result:last-child {
                    border-bottom: none;
                }
                .result a {
                    color: #1a0dab;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 18px;
                    display: block;
                    margin-bottom: 5px;
                }
                .result a:hover {
                    text-decoration: underline;
                }
                .result p {
                    color: #545454;
                    margin: 5px 0;
                    line-height: 1.6;
                }
                .url {
                    color: #006621;
                    font-size: 14px;
                }
                .no-results {
                    color: #999;
                    font-style: italic;
                    padding: 20px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="column ddg">
                    <!-- <h2>""" + first_name + """</h2> -->
        """
        # Ajouter les résultats du premier moteur
        if first_results:
            for result in first_results:
                html += f"""
                    <div class=\"result\">
                        <a href=\"javascript:void(0)\" onclick=\"openLink('{result['link']}'); return false;\">{result['title']}</a>
                        <p class=\"url\">{result['link'][:70]}...</p>
                        <p>{result['snippet'][:150]}...</p>
                    </div>
                """
        else:
            html += "<div class='no-results'>Aucun résultat trouvé</div>"
        html += """
                </div>
                <div class=\"column yahoo\">
                    <!-- <h2>""" + second_name + """</h2> -->
        """
        # Ajouter les résultats du deuxième moteur
        if second_results:
            for result in second_results:
                html += f"""
                    <div class=\"result\">
                        <a href=\"javascript:void(0)\" onclick=\"openLink('{result['link']}'); return false;\">{result['title']}</a>
                        <p class=\"url\">{result['link'][:70]}...</p>
                        <p>{result['snippet'][:150]}...</p>
                    </div>
                """
        else:
            html += "<div class='no-results'>Aucun résultat trouvé</div>"
        html += """
                </div>
            </div>
            <script>
                function openLink(url) {
                    window.location.href = url;
                }
            </script>
        </body>
        </html>
        """
        return html

    def reload_page(self):
        """
        Relance la recherche actuelle.
        """
        query = self.results_search_bar.text().strip()
        if query:
            self.search()

    def go_back(self):
        """
        Retour à la page précédente dans l'historique du navigateur.
        """
        self.results_view.back()

    def go_forward(self):
        """
        Aller à la page suivante dans l'historique du navigateur.
        """
        self.results_view.forward()

    def load_search_engines(self):
        """
        Charge la liste des moteurs de recherche depuis un fichier JSON.
        Retourne la liste vide en cas d'echec.
        """
        json_path = self._resource_path("config", "search_engines.json")
        try:
            if not os.path.exists(json_path):
                QMessageBox.critical(self, "Erreur", f"Le fichier {json_path} est introuvable.")
                return []
            with open(json_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Erreur", "Erreur json format.")
            return []
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")
            return []

    def _resource_path(self, *paths: str) -> str:
        """
        Résout un chemin de ressource compatible exécution normale et binaire PyInstaller.
        Utilise sys._MEIPASS quand présent.
        """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_path, *paths)

class LegacyModelWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt, token):
        super().__init__()
        self.prompt = prompt
        self.token = token

    def run(self):
        try:
            url = "https://api-inference.huggingface.co/models/microsoft/bitnet-b1.58-2B-4T"
            headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
            payload = {"inputs": self.prompt, "parameters": {"max_new_tokens": 128, "temperature": 0.7}}
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 503:
                info = r.json()
                self.error.emit(info.get("error", "Le modèle est en cours de chargement. Réessayez plus tard."))
                return
            if r.status_code >= 400:
                self.error.emit(f"Erreur API ({r.status_code})")
                return
            data = r.json()
            if isinstance(data, list) and data and "generated_text" in data[0]:
                text = data[0]["generated_text"]
            elif isinstance(data, dict) and "generated_text" in data:
                text = data["generated_text"]
            else:
                text = json.dumps(data)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))
        pass

    def reload_page(self):
        """
        Relance la recherche actuelle.
        """
        query = self.results_search_bar.text().strip()
        if query:
            self.search()

    def go_back(self):
        """
        Retour à la page précédente dans l'historique du navigateur.
        """
        self.results_view.back()

    def go_forward(self):
        """
        Aller à la page suivante dans l'historique du navigateur.
        """
        self.results_view.forward()

    def load_search_engines(self):
        """
        Charge la liste des moteurs de recherche depuis un fichier JSON.
        Retourne la liste vide en cas d'echec.
        """
        json_path = os.path.join("config", "search_engines.json")
        try:
            if not os.path.exists(json_path):
                QMessageBox.critical(self, "Erreur", f"Le fichier {json_path} est introuvable.")
                return []

            with open(json_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Erreur", "Erreur json format.")
            return []
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")
            return []