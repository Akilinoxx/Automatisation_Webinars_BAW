# ===== IMPORTATION DES BIBLIOTHÈQUES =====
# tkinter : bibliothèque standard pour créer des interfaces graphiques en Python
import tkinter as tk

# ttk : module de tkinter qui fournit des widgets avec un style plus moderne
from tkinter import ttk

# os : permet de travailler avec les chemins de fichiers et les dossiers
import os

# typing : permet de spécifier les types de données attendus dans les fonctions
from typing import List, Tuple

# pygame : bibliothèque pour créer des jeux et gérer le son et les images
# Ici, on l'utilise uniquement pour la lecture audio
import pygame

# Importer les fonctions de notre propre module webhook
# Ces fonctions permettent d'envoyer des fichiers et des données à un service web
from utils.webhook import send_file_to_webhook, send_parts_count_to_webhook

# threading : permet d'exécuter des tâches en parallèle (en arrière-plan)
# Utile pour ne pas bloquer l'interface utilisateur pendant des opérations longues
import threading

# time : permet de travailler avec le temps, notamment de faire des pauses
import time

# ===== CONSTANTES =====
# URL du webhook pour l'envoi du nombre de parties
# Un webhook est une URL qui permet de recevoir des données depuis une application externe
# Cette URL spécifique est utilisée pour informer le service Make.com du nombre de parties choisi
# Remplacez cette URL par votre propre webhook Make.com
PARTS_COUNT_WEBHOOK_URL = "INSÉRER_URL_WEBHOOK_ICI"

# ===== DÉFINITION DE LA CLASSE PRINCIPALE =====
# Cette classe représente la vue qui affiche et gère les morceaux audio
# Elle hérite de ttk.Frame, ce qui signifie qu'elle est un conteneur d'éléments d'interface
class AudioChunksView(ttk.Frame):
    # Le constructeur de la classe, appelé lorsqu'on crée une nouvelle instance
    def __init__(self, master, chunks: List[Tuple[str, int, float]], webhook_url: str, num_parts: int = None):
        # Afficher un message de débogage pour suivre l'exécution
        print("Initialisation de AudioChunksView")
        
        # Appeler le constructeur de la classe parente (ttk.Frame)
        # 'master' est le widget parent qui contiendra cette vue
        super().__init__(master)
        
        # Stocker les paramètres reçus comme attributs de l'instance
        # 'chunks' est une liste de tuples contenant pour chaque morceau:
        # - le chemin vers le fichier
        # - son numéro
        # - sa durée en secondes
        self.chunks = chunks
        
        # L'URL du webhook où envoyer les fichiers audio
        self.webhook_url = webhook_url
        
        # Variable pour suivre le lecteur audio actuellement actif
        self.current_player = None
        
        # Nombre de morceaux choisi par l'utilisateur (peut être différent du nombre réel de morceaux)
        self.num_parts = num_parts
        
        # Afficher le nombre de morceaux reçus pour le débogage
        print(f"Nombre de morceaux reçus : {len(chunks)}")
        
        # Initialiser le module de son de pygame pour pouvoir lire les fichiers audio
        pygame.mixer.init()
        
        # Appeler la méthode qui va créer tous les éléments de l'interface
        self.create_widgets()
        
        # Confirmer que les widgets ont été créés
        print("Widgets créés")
        
    # Méthode pour créer tous les éléments de l'interface utilisateur
    def create_widgets(self):
        # Afficher un message de débogage
        print("Création des widgets")
        
        # ===== CONFIGURATION DE LA DISPOSITION GÉNÉRALE =====
        # Configurer la grille principale pour qu'elle s'adapte à la taille de la fenêtre
        # weight=1 signifie que la colonne/ligne s'étendra proportionnellement
        self.grid_columnconfigure(0, weight=1)  # La colonne 0 s'étendra horizontalement
        self.grid_rowconfigure(1, weight=1)     # La ligne 1 s'étendra verticalement
        
        # ===== SECTION ACTIONS (EN HAUT) =====
        # Créer un cadre pour contenir les contrôles d'action (statut et bouton d'envoi)
        actions_frame = ttk.Frame(self)  # Un Frame est un conteneur simple
        
        # Placer ce cadre dans la grille principale
        # sticky='ew' signifie que le cadre s'étendra de gauche à droite (east-west)
        # padx et pady ajoutent une marge autour du cadre
        actions_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Configurer la colonne 0 du cadre d'actions pour qu'elle s'étende
        actions_frame.grid_columnconfigure(0, weight=1)
        
        # Créer une étiquette pour afficher le statut des opérations
        self.status_label = ttk.Label(
            actions_frame,           # Parent: le cadre d'actions
            text="Prêt à envoyer",    # Texte initial
            anchor='w'               # Alignement du texte à gauche (west)
        )
        # Placer l'étiquette dans le cadre d'actions
        # sticky='ew' permet à l'étiquette de s'étendre horizontalement
        self.status_label.grid(row=0, column=0, sticky='ew')
        
        # Créer un bouton pour envoyer tous les morceaux
        self.send_button = ttk.Button(
            actions_frame,              # Parent: le cadre d'actions
            text="Envoyer au webhook",   # Texte du bouton
            command=self.send_all_chunks,  # Fonction à appeler quand on clique
            style="Accent.TButton"      # Style visuel du bouton (accentué)
        )
        # Placer le bouton à droite de l'étiquette de statut
        # padx=(5, 0) ajoute une marge de 5 pixels à gauche du bouton
        self.send_button.grid(row=0, column=1, padx=(5, 0))
        
        # ===== SECTION LISTE DES MORCEAUX (AU MILIEU) =====
        # Créer un cadre avec titre pour contenir la liste des morceaux
        list_frame = ttk.LabelFrame(self, text="Morceaux audio", padding=10)
        
        # Placer ce cadre dans la grille principale, sous le cadre d'actions
        # sticky='nsew' signifie que le cadre s'étendra dans toutes les directions
        # (north-south-east-west)
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configurer la grille du cadre de liste pour qu'elle s'adapte à la taille
        list_frame.grid_columnconfigure(0, weight=1)  # La colonne 0 s'étendra
        list_frame.grid_rowconfigure(0, weight=1)     # La ligne 0 s'étendra
        
        # ===== SYSTÈME DE DÉFILEMENT (SCROLLING) =====
        # Créer un canvas qui servira de zone défilante
        # Un canvas est un widget qui peut contenir d'autres widgets et permet le défilement
        canvas = tk.Canvas(list_frame)
        
        # Créer une barre de défilement verticale
        scrollbar = ttk.Scrollbar(
            list_frame,              # Parent: le cadre de liste
            orient="vertical",        # Orientation verticale
            command=canvas.yview      # Lier la barre au défilement vertical du canvas
        )
        
        # Créer un cadre qui contiendra les widgets des morceaux
        # Ce cadre sera placé à l'intérieur du canvas
        self.scrollable_frame = ttk.Frame(canvas)
        
        # Configurer le défilement: quand la taille du cadre change, mettre à jour
        # la région de défilement du canvas
        self.scrollable_frame.bind(
            "<Configure>",  # Événement: quand la configuration du widget change
            # Fonction lambda qui met à jour la région de défilement
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Créer une fenêtre dans le canvas qui affichera le cadre défilable
        # (0, 0) sont les coordonnées, anchor="nw" signifie que le point d'ancrage
        # est le coin supérieur gauche (north-west)
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Lier la position de la barre de défilement à la vue du canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Placer le canvas et la barre de défilement dans le cadre de liste
        # Le canvas s'étend dans toutes les directions
        canvas.grid(row=0, column=0, sticky='nsew')
        # La barre de défilement s'étend verticalement (north-south)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # ===== AJOUT DES MORCEAUX À L'INTERFACE =====
        print("Ajout des morceaux à l'interface")
        
        # Parcourir tous les morceaux et créer un cadre pour chacun
        for path, num, duration in self.chunks:
            # Afficher un message de débogage
            print(f"Ajout du morceau {num}")
            # Créer un cadre pour ce morceau avec ses contrôles
            self.create_chunk_frame(path, num, duration)
        
    # Méthode pour créer l'interface d'un morceau audio individuel
    def create_chunk_frame(self, path: str, num: int, duration: float):
        """Crée un cadre pour afficher un morceau audio avec ses contrôles"""
        # ===== CADRE PRINCIPAL DU MORCEAU =====
        # Créer un cadre pour contenir tous les éléments d'un morceau
        chunk_frame = ttk.Frame(self.scrollable_frame)  # Parent: le cadre défilable
        
        # Configurer le cadre pour qu'il s'étende horizontalement
        # fill='x' signifie que le cadre s'étendra horizontalement
        # padx et pady ajoutent des marges autour du cadre
        chunk_frame.pack(fill='x', padx=5, pady=2)
        
        # Configurer la colonne du milieu (celle qui contient le nom du fichier)
        # pour qu'elle s'étende et prenne tout l'espace disponible
        chunk_frame.grid_columnconfigure(1, weight=1)
        
        # ===== SECTION INFORMATIONS (À GAUCHE) =====
        # Créer un cadre pour les informations sur le morceau (numéro et durée)
        info_frame = ttk.Frame(chunk_frame)
        
        # Placer ce cadre à gauche du cadre principal
        # sticky='w' signifie que le cadre sera aligné à gauche (west)
        # padx=(0, 10) ajoute une marge de 10 pixels à droite du cadre
        info_frame.grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        # Créer une étiquette pour afficher le numéro de la partie
        name_label = ttk.Label(
            info_frame,                    # Parent: le cadre d'informations
            text=f"Partie {num}",          # Texte: "Partie 1", "Partie 2", etc.
            font=('TkDefaultFont', 10, 'bold')  # Police en gras pour mettre en évidence
        )
        # Placer l'étiquette en haut du cadre d'informations, alignée à gauche
        name_label.pack(anchor='w')
        
        # Créer une étiquette pour afficher la durée du morceau
        duration_label = ttk.Label(
            info_frame,                         # Parent: le cadre d'informations
            text=f"Durée: {int(duration)} secondes"  # Texte: durée arrondie en secondes
        )
        # Placer l'étiquette sous l'étiquette du nom, alignée à gauche
        duration_label.pack(anchor='w')
        
        # ===== SECTION NOM DU FICHIER (AU MILIEU) =====
        # Créer une étiquette pour afficher le nom du fichier
        file_label = ttk.Label(
            chunk_frame,                    # Parent: le cadre principal du morceau
            text=os.path.basename(path),    # Texte: juste le nom du fichier, sans le chemin
            anchor='w'                      # Alignement du texte à gauche
        )
        # Placer l'étiquette au milieu du cadre principal
        # sticky='ew' permet à l'étiquette de s'étendre horizontalement
        file_label.grid(row=0, column=1, sticky='ew')
        
        # ===== SECTION CONTRÔLES AUDIO (À DROITE) =====
        # Créer un cadre pour les boutons de contrôle audio (lecture et arrêt)
        controls_frame = ttk.Frame(chunk_frame)
        
        # Placer ce cadre à droite du cadre principal
        # sticky='e' signifie que le cadre sera aligné à droite (east)
        controls_frame.grid(row=0, column=2, sticky='e')
        
        # Créer un bouton de lecture
        play_button = ttk.Button(
            controls_frame,                 # Parent: le cadre de contrôles
            text="▶️",                    # Texte: icône de lecture (triangle)
            width=3,                        # Largeur fixe pour uniformité
            # Fonction à appeler quand on clique: jouer ce morceau spécifique
            # Lambda est utilisé pour créer une fonction qui capture la variable 'path'
            command=lambda: self.play_audio(path)
        )
        # Placer le bouton à gauche dans le cadre de contrôles
        # side='left' place le widget à gauche des autres widgets dans le même conteneur
        # padx ajoute une marge horizontale autour du bouton
        play_button.pack(side='left', padx=2)
        
        # Créer un bouton d'arrêt
        stop_button = ttk.Button(
            controls_frame,                 # Parent: le cadre de contrôles
            text="⏹️",                    # Texte: icône d'arrêt (carré)
            width=3,                        # Largeur fixe pour uniformité
            command=self.stop_audio         # Fonction à appeler: arrêter la lecture
        )
        # Placer le bouton à droite du bouton de lecture
        stop_button.pack(side='left', padx=2)
        
    # Méthode pour envoyer tous les morceaux audio au webhook
    def send_all_chunks(self):
        """Envoie tous les morceaux au webhook"""
        # ===== FONCTION INTERNE POUR L'ENVOI EN ARRIÈRE-PLAN =====
        # Cette fonction sera exécutée dans un thread séparé pour ne pas bloquer l'interface
        def send_in_thread():
            # Désactiver le bouton d'envoi pendant l'opération pour éviter les envois multiples
            self.send_button.config(state='disabled')
            
            # Calculer le nombre total de morceaux à envoyer
            total_chunks = len(self.chunks)
            
            # ===== GÉNÉRATION D'UN IDENTIFIANT UNIQUE =====
            # Importer les modules nécessaires ici pour éviter de les charger si on n'utilise pas cette fonction
            import uuid
            import time
            
            # Créer un identifiant unique composé du timestamp actuel et d'un UUID court
            # Cela permet d'identifier de manière unique cette session d'envoi
            # et d'éviter que des fichiers de sessions précédentes soient traités par erreur
            session_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            # ===== ENVOI DE CHAQUE MORCEAU =====
            # Parcourir tous les morceaux un par un
            for path, num, duration in self.chunks:
                # Mettre à jour l'étiquette de statut pour informer l'utilisateur
                self.status_label.config(
                    text=f"Envoi du morceau {num}/{total_chunks}..."
                )
                # Forcer la mise à jour de l'interface pour que le changement soit visible immédiatement
                self.update_idletasks()
                
                # ===== VÉRIFICATION DE L'EXISTENCE DU FICHIER =====
                # Vérifier que le fichier existe toujours avant d'essayer de l'envoyer
                # (il pourrait avoir été supprimé entre-temps)
                if not os.path.exists(path):
                    # Afficher un message d'erreur si le fichier n'existe plus
                    self.status_label.config(
                        text=f"Erreur: Le fichier {os.path.basename(path)} n'existe plus"
                    )
                    # Réactiver le bouton d'envoi pour permettre à l'utilisateur de réessayer
                    self.send_button.config(state='normal')
                    return  # Arrêter l'envoi
                
                # ===== PRÉPARATION DES MÉTADONNÉES =====
                # Créer un dictionnaire avec toutes les informations sur ce morceau
                # Ces informations seront envoyées avec le fichier au webhook
                metadata = {
                    'part_number': num,                    # Numéro de ce morceau
                    'total_parts': total_chunks,          # Nombre total de morceaux
                    'duration_seconds': duration,          # Durée en secondes
                    'filename': os.path.basename(path),    # Nom du fichier
                    'user_selected_parts': self.num_parts,  # Nombre de parties choisi par l'utilisateur
                    'session_id': session_id,              # Identifiant unique de cette session
                    'timestamp': int(time.time())          # Horodatage actuel
                }
                
                # ===== AFFICHAGE D'INFORMATIONS DE DÉBOGAGE =====
                # Ces informations sont utiles pour comprendre ce qui se passe
                print(f"Envoi du fichier: {path}")
                print(f"Métadonnées: {metadata}")
                
                # ===== ENVOI DU FICHIER AU WEBHOOK =====
                # Appeler la fonction qui envoie le fichier au webhook
                # Elle renvoie un booléen indiquant le succès et un message
                success, message = send_file_to_webhook(
                    self.webhook_url,  # URL du webhook
                    path,               # Chemin du fichier à envoyer
                    metadata           # Métadonnées à envoyer avec le fichier
                )
                
                # ===== GESTION DES ERREURS =====
                # Si l'envoi a échoué, afficher un message d'erreur et arrêter
                if not success:
                    self.status_label.config(
                        text=f"Erreur lors de l'envoi du morceau {num}: {message}"
                    )
                    # Réactiver le bouton d'envoi
                    self.send_button.config(state='normal')
                    return  # Arrêter l'envoi
            
            # ===== FINALISATION DE L'ENVOI =====
            # Si on arrive ici, c'est que tous les morceaux ont été envoyés avec succès
            self.status_label.config(text="Tous les morceaux ont été envoyés !")
            # Réactiver le bouton d'envoi
            self.send_button.config(state='normal')
            
            # ===== ENVOI DU NOMBRE DE PARTIES CHOISI =====
            # Fonction interne pour envoyer le nombre de parties après un délai
            def send_parts_count():
                # Attendre 30 secondes avant d'envoyer le nombre de parties
                # Cela laisse le temps au serveur de traiter les fichiers audio
                time.sleep(30)
                
                # Vérifier que le nombre de parties est défini
                if self.num_parts is not None:
                    # Envoyer le nombre de parties au webhook spécifique
                    success, message = send_parts_count_to_webhook(
                        PARTS_COUNT_WEBHOOK_URL,  # URL du webhook pour le nombre de parties
                        self.num_parts             # Nombre de parties choisi par l'utilisateur
                    )
                    
                    # Mettre à jour le statut en fonction du résultat
                    if success:
                        self.status_label.config(
                            text="Nombre de parties envoyé au webhook"
                        )
                    else:
                        self.status_label.config(
                            text=f"Erreur lors de l'envoi du nombre de parties : {message}"
                        )
            
            # Lancer l'envoi du nombre de parties dans un thread séparé
            # daemon=True signifie que ce thread s'arrêtera automatiquement quand le programme principal se terminera
            threading.Thread(target=send_parts_count, daemon=True).start()
        
        # ===== LANCEMENT DE L'ENVOI =====
        # Lancer l'envoi dans un thread séparé pour ne pas bloquer l'interface
        # L'utilisateur pourra continuer à utiliser l'application pendant l'envoi
        threading.Thread(target=send_in_thread, daemon=True).start()
        
    # Méthode pour jouer un fichier audio
    def play_audio(self, path: str):
        """Joue un fichier audio"""
        # ===== LECTURE AUDIO =====
        # D'abord arrêter toute lecture en cours pour éviter la superposition des sons
        self.stop_audio()
        
        # Charger le fichier audio dans le lecteur pygame
        # pygame.mixer.music est le module de pygame qui gère la lecture audio
        pygame.mixer.music.load(path)
        
        # Démarrer la lecture du fichier audio
        # Sans paramètres, play() joue le fichier une seule fois
        pygame.mixer.music.play()
        
    # Méthode pour arrêter la lecture audio
    def stop_audio(self):
        """Arrête la lecture audio"""
        # Arrêter immédiatement toute lecture audio en cours
        # Cette fonction est appelée soit directement par le bouton d'arrêt,
        # soit avant de jouer un nouveau fichier
        pygame.mixer.music.stop()
        
    # Méthode pour nettoyer les ressources lors de la fermeture de l'application
    def destroy(self):
        """Nettoie les ressources lors de la fermeture"""
        # ===== NETTOYAGE DES RESSOURCES =====
        # Arrêter toute lecture audio en cours
        self.stop_audio()
        
        # Fermer proprement le module audio de pygame
        # Cela libère les ressources audio utilisées par l'application
        pygame.mixer.quit()
        
        # Appeler la méthode destroy de la classe parente (ttk.Frame)
        # pour s'assurer que toutes les ressources sont correctement libérées
        super().destroy()
