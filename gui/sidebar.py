import tkinter as tk
from tkinter import ttk, PhotoImage
from PIL import Image, ImageTk
import os
from gui.theme import ModernTheme

class Sidebar(ttk.Frame):
    def __init__(self, master, notebook):
        super().__init__(master)
        self.notebook = notebook
        self.configure(style="Card.TFrame")
        
        # Style
        self.style = ttk.Style()
        self.style.configure("Sidebar.TFrame",
            background=ModernTheme.SIDEBAR_COLOR
        )
        
        self.style.configure("SidebarButton.TButton",
            background=ModernTheme.SIDEBAR_COLOR,
            foreground="white",
            font=('Segoe UI', 10),
            padding=10,
            relief="flat"
        )
        
        self.style.map("SidebarButton.TButton",
            background=[('active', ModernTheme.PRIMARY_COLOR)],
            foreground=[('active', 'white')]
        )
        
        # Initialiser le cache des images
        self._logo_cache = []
        self._resize_after_id = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Logo
        logo_frame = ttk.Frame(self, style="Sidebar.TFrame")
        logo_frame.pack(fill='x', pady=(20, 30))
        
        # Charger et redimensionner le logo
        self.logo_image = self.load_and_resize_logo()
        
        # Afficher le logo
        logo_label = ttk.Label(
            logo_frame,
            image=self.logo_image,
            background=ModernTheme.SIDEBAR_COLOR
        )
        logo_label.pack(pady=10)
        
        # Lier l'événement de redimensionnement
        self.master.bind("<Configure>", self.on_window_resize)
        
        # Boutons de navigation
        self.buttons = []
        pages = [
            ("🎥 Post Webinar", 0)
        ]
        
        for text, index in pages:
            btn = ttk.Button(
                self,
                text=text,
                style="SidebarButton.TButton",
                command=lambda i=index: self.switch_page(i)
            )
            btn.pack(fill='x', padx=5, pady=2)
            self.buttons.append(btn)
        
        # Séparateur
        ttk.Separator(self).pack(fill='x', pady=20)
        
        # Version
        version_label = ttk.Label(
            self,
            text="v1.0.0",
            foreground="white",
            background=ModernTheme.SIDEBAR_COLOR
        )
        version_label.pack(side='bottom', pady=10)
        
    def switch_page(self, index):
        # Vérifier que l'index est valide avant de changer de page
        if index < len(self.notebook.tabs()):
            self.notebook.select(index)
    
    def load_and_resize_logo(self, width=150):
        """Charge et redimensionne le logo en fonction de la largeur spécifiée"""
        # Si l'image originale n'est pas encore chargée, la charger une seule fois
        if not hasattr(self, '_original_logo'):
            # Chemin vers le logo
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logo_baw.png")
            # Charger l'image avec PIL une seule fois
            self._original_logo = Image.open(logo_path)
            # Calculer et stocker le ratio une seule fois
            self._logo_ratio = self._original_logo.width / self._original_logo.height
        
        # Vérifier si nous avons déjà une version mise en cache de cette taille
        cache_key = f"logo_{width}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        # Calculer la hauteur proportionnelle
        height = int(width / self._logo_ratio)
        
        # Redimensionner l'image avec une haute qualité mais plus rapide que LANCZOS
        resized_img = self._original_logo.resize((width, height), Image.BICUBIC)
        
        # Convertir en PhotoImage pour Tkinter
        photo_img = ImageTk.PhotoImage(resized_img)
        
        # Mettre en cache cette taille (limiter à 3 tailles différentes pour éviter la fuite de mémoire)
        self._clear_old_cache()
        setattr(self, cache_key, photo_img)
        
        return photo_img
    
    def on_window_resize(self, event=None):
        """Redimensionne le logo en fonction de la taille de la fenêtre, mais avec limitation"""
        # Vérifier si suffisamment de temps s'est écoulé depuis le dernier redimensionnement
        current_time = self.master.after_idle(lambda: None)  # Obtient un ID unique basé sur le temps
        
        # Si un redimensionnement est déjà prévu, annuler
        if hasattr(self, '_resize_after_id') and self._resize_after_id:
            self.master.after_cancel(self._resize_after_id)
            
        # Programmer un redimensionnement après un délai (débouncing)
        self._resize_after_id = self.master.after(150, self._delayed_resize)
        
    def _delayed_resize(self):
        """Exécute le redimensionnement après un délai pour éviter les appels fréquents"""
        # Réinitialiser l'ID
        self._resize_after_id = None
        
        # Obtenir la largeur actuelle de la sidebar
        sidebar_width = self.winfo_width()
        
        # Ne pas redimensionner si la largeur est trop petite ou nulle
        if sidebar_width < 50:
            return
            
        # Arrondir la largeur au multiple de 10 le plus proche pour réduire le nombre de redimensionnements
        new_width = int(sidebar_width * 0.8)
        new_width = round(new_width / 10) * 10
        
        # Redimensionner le logo seulement si nécessaire
        if not hasattr(self, '_last_width') or self._last_width != new_width:
            self._last_width = new_width
            self.logo_image = self.load_and_resize_logo(width=new_width)
            
            # Mettre à jour l'image dans tous les widgets qui l'utilisent
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Label) and hasattr(child, 'cget') and child.cget('image'):
                            child.configure(image=self.logo_image)
    
    def _clear_old_cache(self):
        """Limite le nombre d'images en cache pour éviter les fuites de mémoire"""
        # Trouver tous les attributs qui sont des images mises en cache
        cache_attrs = [attr for attr in dir(self) if attr.startswith('logo_') and not attr.startswith('_')]
        
        # Garder seulement les 3 dernières tailles
        if len(cache_attrs) > 3:
            # Trier par taille (extraire le nombre de logo_XXX)
            sorted_attrs = sorted(cache_attrs, key=lambda x: int(x.split('_')[1]))
            
            # Supprimer les plus anciennes (plus petites tailles)
            for attr in sorted_attrs[:-3]:
                delattr(self, attr)
