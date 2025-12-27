import json
from PyQt5.QtCore import QObject, pyqtSignal
from gradio_client import Client


class ModelWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, prompt: str, use_web_search: bool = False, max_length: int = 200, temperature: float = 0.7):
        super().__init__()
        self.prompt = prompt
        self.use_web_search = use_web_search
        self.max_length = max_length
        self.temperature = temperature
        self.space_name = "Drichdev/micro-btnet-user"

    def run(self):
        """
        Exécute la requête vers l'API Gradio
        """
        try:
            self.progress.emit("Connexion au modèle...")
            
            # Créer le client Gradio
            client = Client(self.space_name)
            
            if self.use_web_search:
                self.progress.emit("Recherche web activée...")
            else:
                self.progress.emit("Génération de la réponse...")
            
            # Appeler l'API
            result = client.predict(
                question=self.prompt,
                use_web_search=self.use_web_search,
                max_length=self.max_length,
                temperature=self.temperature,
                api_name="/answer_question"
            )
            
            # Émettre la réponse
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Erreur: {str(e)}")


# Exemple d'utilisation avec interface PyQt5
"""
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QCheckBox, QLabel

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistant IA")
        self.setGeometry(100, 100, 800, 600)
        
        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Zone de chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Status
        self.status_label = QLabel("Prêt")
        layout.addWidget(self.status_label)
        
        # Input
        self.input_box = QTextEdit()
        self.input_box.setMaximumHeight(100)
        self.input_box.setPlaceholderText("Posez votre question ici...")
        layout.addWidget(self.input_box)
        
        # Checkbox recherche web
        self.web_search_checkbox = QCheckBox("🌐 Activer la recherche web")
        layout.addWidget(self.web_search_checkbox)
        
        # Bouton envoyer
        self.send_button = QPushButton("Envoyer")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)
        
        self.thread = None
        self.worker = None
    
    def send_message(self):
        prompt = self.input_box.toPlainText().strip()
        if not prompt:
            return
        
        # Afficher le message de l'utilisateur
        self.chat_display.append(f"<b>Vous:</b> {prompt}")
        self.chat_display.append("")
        
        # Désactiver le bouton
        self.send_button.setEnabled(False)
        self.input_box.clear()
        
        # Créer le worker
        use_web = self.web_search_checkbox.isChecked()
        self.worker = ModelWorker(
            prompt=prompt,
            use_web_search=use_web,
            max_length=200,
            temperature=0.7
        )
        
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # Connexions
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup)
        
        # Démarrer
        self.thread.start()
    
    def on_response(self, text: str):
        self.chat_display.append(f"<b>Assistant:</b>")
        self.chat_display.append(text)
        self.chat_display.append("")
        self.status_label.setText("✅ Réponse reçue")
    
    def on_error(self, error: str):
        self.chat_display.append(f"<b style='color: red;'>Erreur:</b> {error}")
        self.chat_display.append("")
        self.status_label.setText("❌ Erreur")
    
    def on_progress(self, message: str):
        self.status_label.setText(message)
    
    def cleanup(self):
        self.send_button.setEnabled(True)
        self.status_label.setText("Prêt")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())
"""