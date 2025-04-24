# ===== IMPORTATION DES BIBLIOTHÈQUES =====
# os : permet de travailler avec les chemins de fichiers et les dossiers
import os

# math : fournit des fonctions mathématiques comme l'arrondi au supérieur (ceil)
import math

# typing : permet de spécifier les types de données attendus dans les fonctions
from typing import List, Tuple

# tempfile : permet de créer des fichiers et dossiers temporaires qui seront automatiquement supprimés
import tempfile

# subprocess : permet d'exécuter des commandes externes comme ffmpeg
import subprocess

# json : permet de travailler avec des données au format JSON (JavaScript Object Notation)
import json

# sys : fournit des variables et fonctions liées au système d'exploitation
import sys

# ===== DÉFINITION DE LA CLASSE PRINCIPALE =====
# Une classe est comme une boîte qui contient des outils (fonctions) et des données
class AudioProcessor:
    # @staticmethod signifie que cette fonction appartient à la classe mais n'a pas besoin
    # d'une instance spécifique de la classe pour fonctionner
    @staticmethod
    def get_ffmpeg_path():
        """Retourne le chemin vers l'exécutable ffmpeg qui est utilisé pour manipuler les fichiers audio et vidéo"""
        
        # Étape 1: Essayer de trouver ffmpeg dans le dossier 'bin' de notre application
        # __file__ représente le chemin de ce fichier Python actuel
        # os.path.dirname remonte d'un niveau dans l'arborescence des dossiers
        # Donc on remonte de deux niveaux pour arriver à la racine du projet
        local_ffmpeg = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # Remonte au dossier racine du projet
            "bin",                                       # Va dans le sous-dossier 'bin'
            "ffmpeg.exe"                               # Cherche le fichier ffmpeg.exe
        )
        
        # Étape 2: Vérifier si le fichier existe à cet emplacement
        if os.path.exists(local_ffmpeg):  # Si le fichier existe...
            return local_ffmpeg           # ...on renvoie son chemin
            
        # Étape 3: Si ffmpeg n'est pas dans notre dossier 'bin', on le cherche dans le système
        try:  # On utilise try/except pour gérer les erreurs potentielles
            # Vérifier quel système d'exploitation est utilisé
            if sys.platform == "win32":  # Si c'est Windows...
                # La commande 'where' de Windows cherche un programme dans le PATH
                result = subprocess.run(
                    "where ffmpeg",          # Commande à exécuter
                    capture_output=True,     # Capturer la sortie de la commande
                    text=True,               # Convertir la sortie en texte
                    shell=True               # Exécuter via l'interpréteur de commandes
                )
            else:  # Si c'est Linux, macOS ou autre...
                # La commande 'which' sur Unix cherche un programme dans le PATH
                result = subprocess.run(
                    "which ffmpeg",           # Commande à exécuter
                    capture_output=True,     # Capturer la sortie de la commande
                    text=True,               # Convertir la sortie en texte
                    shell=True               # Exécuter via l'interpréteur de commandes
                )
                
            # Vérifier si la commande a réussi (code de retour 0 = succès)
            if result.returncode == 0:  # Si ffmpeg a été trouvé dans le PATH...
                # On prend la première ligne de la sortie, qui contient le chemin vers ffmpeg
                # strip() enlève les espaces inutiles, split('\n') sépare les lignes
                return result.stdout.strip().split('\n')[0]
        except:  # Si une erreur se produit pendant la recherche...
            pass  # ...on ne fait rien et on continue
            
        # Si on arrive ici, c'est qu'on n'a pas trouvé ffmpeg
        # On lève une exception pour signaler l'erreur
        raise FileNotFoundError(
            "ffmpeg n'a pas été trouvé. Veuillez l'installer dans le dossier bin/"
        )
    
    # Encore une méthode statique qui appartient à la classe mais pas à une instance spécifique
    @staticmethod
    def get_ffprobe_path():
        """Retourne le chemin vers ffprobe, un outil qui permet d'analyser les fichiers multimédia"""
        
        # Étape 1: Essayer de trouver ffprobe dans le dossier 'bin' de notre application
        # La stratégie est similaire à celle utilisée pour ffmpeg
        local_ffprobe = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # Remonte au dossier racine du projet
            "bin",                                       # Va dans le sous-dossier 'bin'
            "ffprobe.exe"                              # Cherche le fichier ffprobe.exe
        )
        
        # Étape 2: Vérifier si le fichier existe à cet emplacement
        if os.path.exists(local_ffprobe):  # Si le fichier existe...
            return local_ffprobe           # ...on renvoie son chemin
            
        # Étape 3: Si ffprobe n'est pas trouvé directement, on essaie de le trouver à côté de ffmpeg
        # (généralement, ffmpeg et ffprobe sont installés dans le même dossier)
        try:
            # On récupère d'abord le chemin vers ffmpeg
            ffmpeg_path = AudioProcessor.get_ffmpeg_path()
            
            # On remplace 'ffmpeg.exe' par 'ffprobe.exe' dans le chemin
            ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
            
            # On vérifie si ffprobe existe à cet emplacement
            if os.path.exists(ffprobe_path):
                return ffprobe_path  # Si oui, on renvoie son chemin
        except:  # Si une erreur se produit...
            pass  # ...on ne fait rien et on continue
            
        # Si on arrive ici, c'est qu'on n'a pas trouvé ffprobe
        # On lève une exception pour signaler l'erreur
        raise FileNotFoundError(
            "ffprobe n'a pas été trouvé. Veuillez l'installer dans le dossier bin/"
        )
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """
        Obtient la durée d'un fichier audio en secondes en utilisant ffprobe.
        
        Args:
            file_path: Le chemin vers le fichier audio dont on veut connaître la durée
            
        Returns:
            float: La durée du fichier audio en secondes
        """
        # Étape 1: Récupérer le chemin vers ffprobe
        ffprobe_path = AudioProcessor.get_ffprobe_path()
        
        # Étape 2: Préparer la commande ffprobe à exécuter
        # Cette commande va analyser le fichier audio et extraire sa durée
        cmd = [
            ffprobe_path,                    # Chemin vers l'exécutable ffprobe
            '-v', 'error',                   # N'afficher que les erreurs (mode silencieux)
            '-show_entries', 'format=duration',  # Extraire uniquement la durée
            '-of', 'json',                  # Format de sortie: JSON (facile à traiter)
            file_path                        # Chemin du fichier à analyser
        ]
        
        # Étape 3: Exécuter la commande et traiter le résultat
        try:
            # Exécuter la commande ffprobe
            result = subprocess.run(
                cmd,                  # La commande à exécuter
                capture_output=True,  # Capturer la sortie
                text=True,            # Convertir la sortie en texte
                check=True            # Lever une exception si la commande échoue
            )
            
            # Convertir la sortie JSON en dictionnaire Python
            data = json.loads(result.stdout)
            
            # Extraire la durée et la convertir en nombre décimal
            return float(data['format']['duration'])
            
        # Étape 4: Gérer les erreurs potentielles
        except subprocess.CalledProcessError as e:  # Si ffprobe renvoie une erreur
            raise Exception(f"Erreur ffprobe : {e.stderr}")
        except Exception as e:  # Pour toute autre erreur
            raise Exception(f"Erreur lors de la lecture de la durée : {str(e)}")
    
    @staticmethod
    def compress_mp3(input_path: str, output_path: str = None, bitrate="128k") -> str:
        """
        Compresse un fichier MP3 avec un bitrate spécifique.
        Le bitrate détermine la qualité et la taille du fichier audio: 
        plus il est élevé, meilleure est la qualité mais plus le fichier est volumineux.
        
        Args:
            input_path: Chemin du fichier MP3 d'entrée (le fichier à compresser)
            output_path: Chemin du fichier MP3 de sortie (où sauvegarder le résultat, optionnel)
            bitrate: Bitrate cible (par défaut 128k, où k = kilo bits par seconde)
            
        Returns:
            str: Chemin du fichier compressé (pour pouvoir le retrouver après)
        """
        # Étape 1: Si aucun chemin de sortie n'est spécifié, en créer un automatiquement
        if output_path is None:
            # Récupérer le dossier du fichier d'entrée
            base_dir = os.path.dirname(input_path)
            
            # Récupérer le nom du fichier sans son extension
            filename = os.path.splitext(os.path.basename(input_path))[0]
            
            # Créer un nouveau chemin avec "_compressed" ajouté au nom
            output_path = os.path.join(base_dir, f"{filename}_compressed.mp3")
            
        # Étape 2: Préparer la commande ffmpeg pour compresser le fichier
        ffmpeg_path = AudioProcessor.get_ffmpeg_path()  # Obtenir le chemin vers ffmpeg
        cmd = [
            ffmpeg_path,                # Chemin vers l'exécutable ffmpeg
            '-i', input_path,           # Fichier d'entrée (-i = input)
            '-codec:a', 'libmp3lame',   # Utiliser le codec MP3 LAME pour l'audio
            '-b:a', bitrate,            # Définir le bitrate audio (-b:a = bitrate audio)
            '-y',                       # Écraser le fichier de sortie si il existe déjà
            output_path                 # Chemin du fichier de sortie
        ]
        
        # Étape 3: Exécuter la commande et gérer les résultats
        try:
            # Exécuter ffmpeg pour compresser le fichier
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Si tout s'est bien passé, renvoyer le chemin du fichier compressé
            return output_path
            
        # Étape 4: Gérer les erreurs potentielles
        except subprocess.CalledProcessError as e:  # Si ffmpeg renvoie une erreur
            raise Exception(f"Erreur ffmpeg : {e.stderr}")
        except Exception as e:  # Pour toute autre erreur
            raise Exception(f"Erreur lors de la compression : {str(e)}")
    
    @staticmethod
    def split_audio(file_path: str, num_parts: int) -> List[Tuple[str, int, float]]:
        """
        Découpe un fichier audio en morceaux de durée égale.
        Par exemple, si on a un fichier de 10 minutes et qu'on veut 5 parties,
        on obtiendra 5 fichiers de 2 minutes chacun.
        
        Args:
            file_path: Chemin du fichier audio à découper
            num_parts: Nombre de parties souhaitées (combien de morceaux on veut)
            
        Returns:
            List[Tuple[str, int, float]]: Liste contenant pour chaque morceau:
                - le chemin vers le fichier créé
                - son numéro (1, 2, 3, etc.)
                - sa durée en secondes
        """
        # Étape 1: Obtenir la durée totale du fichier audio
        total_duration = AudioProcessor.get_audio_duration(file_path)
        
        # Étape 2: Calculer la durée que devra avoir chaque partie
        # Par exemple, si le fichier dure 10 minutes et qu'on veut 5 parties,
        # chaque partie durera 2 minutes
        duration_per_part = total_duration / num_parts
        
        # Étape 3: Préparer les variables pour stocker les résultats
        chunks = []  # Liste qui contiendra les informations sur chaque morceau
        
        # Créer un dossier temporaire pour stocker les morceaux
        # Ce dossier sera automatiquement supprimé quand le programme se terminera
        temp_dir = tempfile.mkdtemp()
        
        # Récupérer le chemin vers ffmpeg
        ffmpeg_path = AudioProcessor.get_ffmpeg_path()
        
        # Étape 4: Découper le fichier en morceaux
        try:
            # Pour chaque partie que nous voulons créer...
            for i in range(num_parts):
                # Calculer le temps de début de ce morceau (en secondes)
                start_sec = i * duration_per_part
                
                # Calculer le temps de fin de ce morceau
                # Pour le dernier morceau, on va jusqu'à la fin du fichier pour éviter les erreurs d'arrondi
                end_sec = (i + 1) * duration_per_part if i < num_parts - 1 else total_duration
                
                # Calculer la durée de ce morceau
                duration = end_sec - start_sec
                
                # Étape 5: Créer le nom du fichier pour ce morceau
                chunk_path = os.path.join(
                    temp_dir,           # Dossier temporaire
                    f"{i+1}.mp3"        # Nom du fichier (1.mp3, 2.mp3, etc.)
                )
                
                # Étape 6: Préparer la commande ffmpeg pour extraire ce segment
                cmd = [
                    ffmpeg_path,              # Chemin vers l'exécutable ffmpeg
                    '-i', file_path,          # Fichier d'entrée
                    '-ss', str(start_sec),    # Temps de début (-ss = start seconds)
                    '-t', str(duration),      # Durée à extraire (-t = time duration)
                    '-acodec', 'copy',         # Copier l'audio sans le réencoder (plus rapide)
                    '-y',                      # Écraser le fichier s'il existe
                    chunk_path                 # Chemin du fichier de sortie
                ]
                
                # Étape 7: Exécuter la commande pour ce morceau
                try:
                    subprocess.run(cmd, capture_output=True, check=True)
                    
                    # Ajouter les informations de ce morceau à notre liste
                    chunks.append((chunk_path, i + 1, duration))
                    
                except subprocess.CalledProcessError as e:  # Si ffmpeg renvoie une erreur
                    raise Exception(f"Erreur lors du découpage du morceau {i+1}: {e.stderr}")
                    
            # Étape 8: Renvoyer la liste des morceaux créés
            return chunks
            
        # Étape 9: En cas d'erreur, nettoyer les fichiers temporaires avant de propager l'erreur
        except Exception as e:
            # Extraire juste les chemins des fichiers de notre liste de morceaux
            # et les passer à la fonction de nettoyage
            AudioProcessor.cleanup_chunks([c[0] for c in chunks])
            
            # Propager l'erreur pour que l'appelant sache ce qui s'est passé
            raise e

    @staticmethod
    def cleanup_chunks(chunk_paths: List[str]):
        """
        Nettoie les fichiers temporaires créés lors du découpage audio.
        Cette fonction s'assure que tous les fichiers temporaires sont supprimés
        pour ne pas encombrer le disque dur de l'utilisateur.
        
        Args:
            chunk_paths: Liste des chemins vers les fichiers à supprimer
        """
        # Étape 1: Vérifier si la liste est vide
        if not chunk_paths:  # Si la liste est vide...
            return  # ...ne rien faire et terminer la fonction
            
        # Étape 2: Récupérer le dossier temporaire à partir du premier fichier
        # Tous les fichiers sont dans le même dossier temporaire
        temp_dir = os.path.dirname(chunk_paths[0])
        
        # Étape 3: Supprimer chaque fichier un par un
        for path in chunk_paths:  # Pour chaque chemin de fichier dans la liste...
            try:
                # Vérifier si le fichier existe avant d'essayer de le supprimer
                if os.path.exists(path):
                    # Supprimer le fichier
                    os.remove(path)
                    print(f"Fichier temporaire supprimé: {path}")  # Message de débogage
            except Exception as e:  # Si une erreur se produit...
                # On ignore l'erreur et on continue avec les autres fichiers
                print(f"Erreur lors de la suppression du fichier {path}: {str(e)}")  
                pass
                
        # Étape 4: Essayer de supprimer le dossier temporaire lui-même
        # Note: on ne peut supprimer un dossier que s'il est vide
        try:
            # Vérifier si le dossier existe toujours
            if os.path.exists(temp_dir):
                # Supprimer le dossier
                os.rmdir(temp_dir)
                print(f"Dossier temporaire supprimé: {temp_dir}")  # Message de débogage
        except Exception as e:  # Si une erreur se produit...
            # On ignore l'erreur (le dossier n'est peut-être pas vide)
            print(f"Erreur lors de la suppression du dossier {temp_dir}: {str(e)}")
            pass
