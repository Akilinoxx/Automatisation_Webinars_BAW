from tkinter import ttk
import tkinter as tk

class ModernTheme:
    # Couleurs
    PRIMARY_COLOR = "#2196F3"  # Bleu
    SECONDARY_COLOR = "#FFC107"  # Jaune
    BACKGROUND_COLOR = "#FAFAFA"  # Blanc cassé
    SIDEBAR_COLOR = "#1976D2"  # Bleu foncé
    TEXT_COLOR = "#212121"  # Gris foncé
    ACCENT_COLOR = "#FF4081"  # Rose
    
    @staticmethod
    def apply_theme(root):
        style = ttk.Style()
        style.theme_use('clam')  # Base theme
        
        # Configuration générale
        style.configure(".",
            background=ModernTheme.BACKGROUND_COLOR,
            foreground=ModernTheme.TEXT_COLOR,
            font=('Segoe UI', 10)
        )
        
        # Boutons
        style.configure("Accent.TButton",
            background=ModernTheme.PRIMARY_COLOR,
            foreground="white",
            padding=10,
            font=('Segoe UI', 10, 'bold')
        )
        
        style.map("Accent.TButton",
            background=[('active', ModernTheme.ACCENT_COLOR)],
            foreground=[('active', 'white')]
        )
        
        # Labels
        style.configure("Title.TLabel",
            font=('Segoe UI', 16, 'bold'),
            foreground=ModernTheme.PRIMARY_COLOR
        )
        
        # Frames
        style.configure("Card.TFrame",
            background="white",
            relief="flat",
            borderwidth=1
        )
        
        # Notebook (onglets)
        style.configure("Custom.TNotebook",
            background=ModernTheme.BACKGROUND_COLOR,
            tabmargins=[2, 5, 2, 0]
        )
        
        style.configure("Custom.TNotebook.Tab",
            background=ModernTheme.BACKGROUND_COLOR,
            foreground=ModernTheme.TEXT_COLOR,
            padding=[15, 5],
            font=('Segoe UI', 10)
        )
        
        style.map("Custom.TNotebook.Tab",
            background=[("selected", "white")],
            foreground=[("selected", ModernTheme.PRIMARY_COLOR)],
            expand=[("selected", [1, 1, 1, 0])]
        )
        
        # Progress Bar
        style.configure("Custom.Horizontal.TProgressbar",
            background=ModernTheme.PRIMARY_COLOR,
            troughcolor=ModernTheme.BACKGROUND_COLOR,
            borderwidth=0,
            thickness=10
        )
