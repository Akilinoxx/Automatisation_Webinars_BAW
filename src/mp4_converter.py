import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from utils.audio_processor import AudioProcessor
from gui.audio_chunks_view import AudioChunksView
import subprocess
import tempfile

# URL du webhook Make.com
# Remplacez cette URL par votre propre webhook Make.com
WEBHOOK_URL = "INSÉRER_URL_WEBHOOK_ICI"

class MP4ToMP3Converter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        # Faire en sorte que le frame principal prenne tout l'espace
        self.pack(fill='both', expand=True)
        
        # Configuration de la grille principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Créer un canvas et un scrollbar pour toute l'interface
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configurer le scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Faire en sorte que le frame interne prenne toute la largeur
        def configure_frame(e):
            self.canvas.itemconfig('frame', width=e.width)
        self.canvas.bind('<Configure>', configure_frame)
        
        # Créer la fenêtre du canvas avec le frame qui prend toute la largeur
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags='frame')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Permettre le scrolling avec la molette de la souris
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Placer le canvas et le scrollbar avec grid
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configuration de la grille du frame scrollable
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        
    def _on_mousewheel(self, event):
        """Gère le scrolling avec la molette de la souris"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_widgets(self):
        # Frame pour les paramètres de conversion
        params_frame = ttk.LabelFrame(self.scrollable_frame, text="Paramètres de conversion", padding="10")
        params_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        params_frame.grid_columnconfigure(1, weight=1)
        
        # Sélection du fichier d'entrée
        ttk.Label(params_frame, text="Fichier d'entrée :").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.input_file = tk.StringVar()
        input_entry = ttk.Entry(params_frame, textvariable=self.input_file, state='readonly')
        input_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(params_frame, text="Parcourir", command=self.select_input_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Options de conversion
        options_frame = ttk.LabelFrame(self.scrollable_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Qualité audio (remplace le bitrate technique)
        ttk.Label(options_frame, text="Qualité audio :").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        # Mapping des qualités aux valeurs de bitrate
        self.quality_mapping = {
            "Basse qualité (plus petit fichier)": "128k",
            "Qualité standard": "192k",
            "Haute qualité": "256k",
            "Qualité supérieure (plus grand fichier)": "320k"
        }
        
        # Créer la liste des qualités dans l'ordre
        quality_options = list(self.quality_mapping.keys())
        
        self.bitrate_var = tk.StringVar(value="192k")
        self.quality_var = tk.StringVar(value="Qualité standard")
        
        # Mettre à jour le bitrate lorsque la qualité change
        def update_bitrate(*args):
            selected_quality = self.quality_var.get()
            self.bitrate_var.set(self.quality_mapping[selected_quality])
        
        self.quality_var.trace_add("write", update_bitrate)
        
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, values=quality_options, state="readonly", width=30)
        quality_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Mode de découpage
        split_frame = ttk.LabelFrame(options_frame, text="Nombre de parties", padding="5")
        split_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # Options de découpage
        self.num_parts_var = tk.StringVar(value="2")
        ttk.Label(split_frame, text="Nombre de parties :").pack(side='left', padx=5)
        ttk.Entry(split_frame, textvariable=self.num_parts_var, width=10).pack(side='left', padx=5)
        
        # Barre de progression
        progress_frame = ttk.Frame(self.scrollable_frame)
        progress_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="")
        self.status_label.grid(row=1, column=0, sticky='w', padx=5)
        
        # Bouton de conversion
        self.convert_button = ttk.Button(self.scrollable_frame, text="Convertir", command=self.start_conversion, style="Accent.TButton")
        self.convert_button.grid(row=3, column=0, pady=10)
        
        # Frame pour les morceaux audio (initialement vide)
        self.chunks_container = ttk.Frame(self.scrollable_frame)
        self.chunks_container.grid(row=4, column=0, sticky='nsew', pady=10)
        self.chunks_container.grid_columnconfigure(0, weight=1)
        
        # Variable pour stocker la vue des morceaux
        self.chunks_view = None
        self.is_converting = False
        
    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier MP4",
            filetypes=[("Fichiers MP4", "*.mp4")]
        )
        if file_path:
            self.input_file.set(file_path)
            
    def update_progress(self, value, text):
        self.progress_var.set(value)
        self.status_label.config(text=text)
        self.update_idletasks()
        
    def start_conversion(self):
        if not self.input_file.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier MP4")
            return
            
        if self.is_converting:
            messagebox.showinfo("Info", "Conversion en cours...")
            return
            
        # Nettoyer la vue des morceaux précédente
        if self.chunks_view:
            self.chunks_view.destroy()
            self.chunks_view = None
            
        convert_thread = threading.Thread(target=self.convert_to_mp3)
        convert_thread.start()
        
    def convert_to_mp3(self):
        try:
            self.is_converting = True
            self.convert_button.config(state='disabled')
            self.update_progress(0, "Démarrage de la conversion...")
            
            input_path = self.input_file.get()
            output_filename = os.path.splitext(os.path.basename(input_path))[0] + '.mp3'
            
            # Utiliser un dossier temporaire pour la conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, output_filename)
                
                # Convertir directement avec ffmpeg
                self.update_progress(20, "Extraction de l'audio...")
                
                # Construire la commande ffmpeg
                cmd = [
                    AudioProcessor.get_ffmpeg_path(),
                    '-i', input_path,  # Fichier d'entrée
                    '-vn',  # Pas de vidéo
                    '-acodec', 'libmp3lame',  # Codec MP3
                    '-b:a', self.bitrate_var.get(),  # Bitrate
                    '-y',  # Écraser le fichier de sortie si existe
                    output_path
                ]
                
                # Exécuter ffmpeg
                try:
                    subprocess.run(cmd, capture_output=True, check=True)
                except subprocess.CalledProcessError as e:
                    raise Exception(f"Erreur lors de la conversion : {e.stderr}")
                
                self.update_progress(60, "Conversion terminée, découpage en cours...")
                
                # Le fichier original est toujours conservé
                # Nous avons supprimé l'option "conserver le fichier original"
                
                # Découper le fichier selon le mode choisi
                try:
                    num_parts = int(self.num_parts_var.get())
                    if num_parts < 1:
                        raise ValueError("Le nombre de parties doit être supérieur à 0")
                    chunks = AudioProcessor.split_audio(output_path, num_parts=num_parts)
                except ValueError as e:
                    messagebox.showerror("Erreur", str(e))
                    return
                
                # Afficher les morceaux
                self.update_progress(100, "Conversion terminée !")
                
                # Nettoyer la vue précédente si elle existe
                if self.chunks_view:
                    self.chunks_view.destroy()
                    self.chunks_view = None
                
                # S'assurer que le conteneur est vide
                for widget in self.chunks_container.winfo_children():
                    widget.destroy()
                
                # Créer la nouvelle vue des morceaux
                self.chunks_view = AudioChunksView(
                    self.chunks_container,
                    chunks,
                    WEBHOOK_URL,
                    num_parts=int(self.num_parts_var.get())  # Passer le nombre de morceaux choisi par l'utilisateur
                )
                self.chunks_view.pack(fill='both', expand=True)
                
                # Forcer la mise à jour de l'interface
                self.chunks_container.update_idletasks()
                
                messagebox.showinfo(
                    "Succès",
                    "Conversion terminée ! Les fichiers sont prêts à être envoyés au webhook."
                )
                
        except Exception as e:
            self.update_progress(0, "Erreur lors de la conversion")
            messagebox.showerror(
                "Erreur",
                f"Une erreur est survenue lors de la conversion :\n{str(e)}"
            )
            
        finally:
            self.is_converting = False
            self.convert_button.config(state='normal')
