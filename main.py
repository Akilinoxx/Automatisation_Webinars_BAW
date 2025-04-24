import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk
from src.mp4_converter import MP4ToMP3Converter
from gui.theme import ModernTheme
from gui.sidebar import Sidebar

class MainApplication:
    def __init__(self):
        # Définir les variables de configuration avant de créer la fenêtre principale
        # Cela permet d'optimiser le démarrage
        self.configure_tk_options()
        
        self.root = tk.Tk()
        self.root.title("BAW Marketing Tools")
        
        # Améliorer la résolution pour les écrans haute densité
        self.configure_high_dpi()
        
        # Définir l'icône de l'application
        self.set_app_icon()
        
        # Définir une taille minimale
        self.root.minsize(800, 600)
        
        # Faire en sorte que la fenêtre s'ouvre en grand
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Appliquer le thème moderne
        ModernTheme.apply_theme(self.root)
        
        # Configuration de la grille principale
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Création du notebook (onglets)
        self.notebook = ttk.Notebook(
            self.root,
            style="Custom.TNotebook"
        )
        self.notebook.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        # Création de la barre latérale
        self.sidebar = Sidebar(self.root, self.notebook)
        self.sidebar.grid(row=0, column=0, sticky='ns')
        
        # Onglet Automatisation Post Webinar
        webinar_frame = ttk.Frame(self.notebook, style="Card.TFrame", padding=20)
        self.notebook.add(webinar_frame, text="Automatisation Post Webinar")
        
        # Titre de la section
        title = ttk.Label(
            webinar_frame,
            text="Convertisseur MP4 vers MP3",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 20))
        
        # Ajout du convertisseur MP4
        converter = MP4ToMP3Converter(webinar_frame)
        converter.pack(expand=True, fill='both')
        

        
    def configure_high_dpi(self):
        """Configure l'application pour une meilleure résolution sur les écrans haute densité"""
        # Informer Windows que l'application est compatible DPI-aware
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # Valeur 1 pour le mode System DPI aware
        except:
            pass  # Ignorer si ce n'est pas sur Windows ou si la fonction n'est pas disponible
        
        # Définir un facteur d'échelle pour les polices et les éléments
        # Réduire le facteur d'échelle pour améliorer les performances
        self.root.tk.call('tk', 'scaling', 1.2)  # Valeur réduite pour un meilleur équilibre performance/qualité
    
    def set_app_icon(self):
        """Définit l'icône de l'application avec optimisation"""
        try:
            # Chemin vers le logo
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_baw.png")
            
            # Charger l'image avec PIL et la redimensionner immédiatement à une taille optimale pour l'icône
            # Une taille plus petite pour l'icône améliore les performances
            icon = Image.open(logo_path)
            icon_size = 32  # Taille standard pour les icônes Windows
            icon = icon.resize((icon_size, icon_size), Image.BICUBIC)
            
            # Convertir en format compatible avec Tkinter
            photo = ImageTk.PhotoImage(icon)
            
            # Définir l'icône de l'application
            self.root.iconphoto(False, photo)  # False = ne pas appliquer à toutes les fenêtres futures
            
            # Garder une référence pour éviter la collecte de déchets
            self.icon_photo = photo
        except Exception as e:
            print(f"Erreur lors du chargement de l'icône: {e}")
    
    def configure_tk_options(self):
        """Configure les options de Tkinter pour améliorer les performances"""
        # Désactiver le syncing avec le serveur X (améliore les performances sous Windows)
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
        
        # Réduire la fréquence de mise à jour des événements d'interface
        # Cela peut réduire la réactivité mais améliore les performances
        if hasattr(tk, 'set_tk_strictMotif'):
            tk.set_tk_strictMotif(True)
    
    def run(self):
        # Définir la priorité des événements pour améliorer les performances
        self.root.update_idletasks()
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()
