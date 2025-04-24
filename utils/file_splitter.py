# ===== IMPORTATION DES BIBLIOTHÈQUES =====
# os : permet de travailler avec les chemins de fichiers et les dossiers
import os

# math : fournit des fonctions mathématiques comme l'arrondi au supérieur (ceil)
import math

# typing : permet de spécifier les types de données attendus dans les fonctions
from typing import List, Tuple

# tempfile : permet de créer des fichiers et dossiers temporaires qui seront automatiquement supprimés
import tempfile

# shutil : fournit des fonctions de haut niveau pour copier et déplacer des fichiers
import shutil

# time : permet de travailler avec le temps, notamment d'obtenir l'heure actuelle
import time

# uuid : permet de générer des identifiants uniques universels
import uuid

# ===== FONCTION PRINCIPALE DE DÉCOUPAGE DE FICHIERS =====
def split_file(file_path: str, max_chunk_size_mb: int = 20) -> List[Tuple[str, int]]:
    """
    Découpe un fichier en plusieurs morceaux de taille maximale spécifiée.
    Par exemple, si on a un fichier de 50 Mo et qu'on veut des morceaux de 20 Mo maximum,
    on obtiendra 3 fichiers (20 Mo + 20 Mo + 10 Mo).
    
    Args:
        file_path: Chemin vers le fichier à découper (où se trouve le fichier)
        max_chunk_size_mb: Taille maximale de chaque morceau en Mo (par défaut 20 Mo)
        
    Returns:
        List[Tuple[str, int]]: Liste de tuples contenant pour chaque morceau:
            - le chemin vers le fichier créé
            - son numéro (1, 2, 3, etc.)
    """
    # Étape 1: Convertir la taille maximale de Mo en octets (bytes)
    # 1 Mo = 1024 Ko, 1 Ko = 1024 octets, donc 1 Mo = 1024 * 1024 octets
    chunk_size = max_chunk_size_mb * 1024 * 1024
    
    # Étape 2: Obtenir la taille du fichier à découper en octets
    file_size = os.path.getsize(file_path)
    
    # Étape 3: Calculer le nombre de morceaux nécessaires
    # math.ceil arrondit au nombre entier supérieur
    # Par exemple, si le fichier fait 25 Mo et qu'on veut des morceaux de 10 Mo,
    # 25 / 10 = 2.5, arrondi à 3 morceaux
    num_chunks = math.ceil(file_size / chunk_size)
    
    # Étape 4: Cas spécial - Si le fichier est déjà assez petit
    # Si le fichier est plus petit que la taille maximale, on fait juste une copie
    if num_chunks <= 1:
        # Créer un dossier temporaire pour stocker la copie
        temp_dir = tempfile.mkdtemp()  # Ce dossier sera automatiquement supprimé plus tard
        
        # Ajouter un identifiant unique au nom du fichier pour éviter les conflits
        # On extrait d'abord le nom de base et l'extension du fichier original
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        
        # Créer un identifiant unique composé du timestamp actuel et d'un UUID court
        unique_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Construire le nouveau nom de fichier avec l'identifiant unique
        new_filename = f"{base_name}_{unique_id}{ext}"
        
        # Créer le chemin complet pour le nouveau fichier
        output_path = os.path.join(temp_dir, new_filename)
        
        # Copier le fichier original vers le nouveau chemin
        shutil.copy2(file_path, output_path)  # copy2 préserve les métadonnées du fichier
        
        # Renvoyer une liste avec un seul élément: le chemin du fichier copié et son numéro (1)
        return [(output_path, 1)]
    
    # Étape 5: Cas général - Le fichier doit être découpé en plusieurs morceaux
    # Préparer une liste vide pour stocker les informations sur chaque morceau
    chunks = []
    
    # Créer un dossier temporaire pour stocker tous les morceaux
    temp_dir = tempfile.mkdtemp()
    
    # Utiliser try/except pour s'assurer de nettoyer les fichiers temporaires en cas d'erreur
    try:
        # Ouvrir le fichier en mode binaire ('rb' = read binary)
        # Le mode binaire est nécessaire car on traite potentiellement des fichiers non-texte
        with open(file_path, 'rb') as source:  # 'with' ferme automatiquement le fichier à la fin
            # Pour chaque morceau à créer...
            for chunk_num in range(num_chunks):
                # Étape 6: Créer un nom de fichier unique pour ce morceau
                # D'abord, extraire le nom de base du fichier original sans l'extension
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Créer un identifiant unique pour ce morceau spécifique
                # Cela garantit que même si on traite plusieurs fichiers avec le même nom,
                # les morceaux auront des noms différents
                unique_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
                
                # Construire le chemin complet pour ce morceau
                # Le format sera: nom_original_part1of3_identifiant.mp3
                chunk_path = os.path.join(
                    temp_dir,  # Dossier temporaire
                    f"{base_name}_part{chunk_num + 1}of{num_chunks}_{unique_id}.mp3"
                )
                
                # Étape 7: Lire et écrire le morceau
                # Ouvrir le fichier de destination en mode écriture binaire ('wb' = write binary)
                with open(chunk_path, 'wb') as chunk:
                    # Lire exactement chunk_size octets du fichier source
                    # Pour le dernier morceau, il peut y avoir moins de données que chunk_size
                    chunk_data = source.read(chunk_size)
                    
                    # Vérifier qu'on a bien des données à écrire
                    if chunk_data:  # Si chunk_data n'est pas vide...
                        # Écrire les données dans le fichier de destination
                        chunk.write(chunk_data)
                        
                        # Ajouter les informations de ce morceau à notre liste
                        # (chemin du fichier, numéro du morceau)
                        chunks.append((chunk_path, chunk_num + 1))
        
        # Étape 8: Renvoyer la liste des morceaux créés
        return chunks
        
    # Étape 9: En cas d'erreur, nettoyer les fichiers temporaires
    except Exception as e:
        # Appeler la fonction de nettoyage pour supprimer tous les morceaux créés
        cleanup_chunks(chunks)
        
        # Propager l'erreur pour que l'appelant sache ce qui s'est passé
        # 'raise e' renvoie l'erreur originale avec sa trace d'appel
        raise e

# ===== FONCTION DE NETTOYAGE DES FICHIERS TEMPORAIRES =====
def cleanup_chunks(chunks: List[Tuple[str, int]]):
    """
    Nettoie les fichiers temporaires créés lors du découpage.
    Cette fonction s'assure que tous les fichiers temporaires sont supprimés
    pour ne pas encombrer le disque dur de l'utilisateur.
    
    Args:
        chunks: Liste des morceaux à nettoyer (liste de tuples contenant le chemin et le numéro)
    """
    # Étape 1: Vérifier si la liste est vide
    if not chunks:  # Si la liste est vide...
        return  # ...ne rien faire et terminer la fonction
        
    # Étape 2: Récupérer le dossier temporaire à partir du premier morceau
    # Tous les morceaux sont dans le même dossier temporaire
    # chunks[0][0] signifie: premier élément de la liste, puis premier élément du tuple (le chemin)
    temp_dir = os.path.dirname(chunks[0][0])  # dirname extrait le dossier d'un chemin complet
    
    # Étape 3: Supprimer chaque fichier un par un
    for chunk_path, _ in chunks:  # Pour chaque tuple (chemin, numéro) dans la liste...
        # Le _ signifie qu'on ignore le deuxième élément du tuple (le numéro)
        try:
            # Vérifier si le fichier existe avant d'essayer de le supprimer
            if os.path.exists(chunk_path):
                # Supprimer le fichier
                os.remove(chunk_path)
                # Afficher un message de confirmation (utile pour le débogage)
                print(f"Fichier temporaire supprimé : {chunk_path}")
        except Exception as e:  # Si une erreur se produit...
            # Afficher un message d'erreur mais continuer avec les autres fichiers
            print(f"Erreur lors de la suppression du fichier {chunk_path}: {str(e)}")
    
    # Étape 4: Supprimer tous les autres fichiers qui pourraient être dans le dossier temporaire
    # Il pourrait y avoir des fichiers qui n'ont pas été inclus dans notre liste chunks
    try:
        # Vérifier si le dossier existe toujours
        if os.path.exists(temp_dir):
            # Lister tous les fichiers dans le dossier
            for filename in os.listdir(temp_dir):  # os.listdir renvoie tous les fichiers et dossiers
                # Construire le chemin complet pour chaque élément
                file_path = os.path.join(temp_dir, filename)
                try:
                    # Vérifier si c'est un fichier (pas un sous-dossier)
                    if os.path.isfile(file_path):
                        # Supprimer le fichier
                        os.remove(file_path)
                        # Afficher un message de confirmation
                        print(f"Fichier supplémentaire supprimé : {file_path}")
                except Exception as e:  # Si une erreur se produit pour un fichier spécifique...
                    # Afficher l'erreur mais continuer avec les autres fichiers
                    print(f"Erreur lors de la suppression du fichier supplémentaire {file_path}: {str(e)}")
    except Exception as e:  # Si une erreur se produit lors du listage des fichiers...
        # Afficher l'erreur mais continuer
        print(f"Erreur lors du nettoyage du dossier temporaire: {str(e)}")
    
    # Étape 5: Essayer de supprimer le dossier temporaire lui-même
    # Note: on ne peut supprimer un dossier que s'il est vide
    try:
        # Vérifier si le dossier existe toujours
        if os.path.exists(temp_dir):
            # Supprimer le dossier
            os.rmdir(temp_dir)  # rmdir ne fonctionne que si le dossier est vide
            # Afficher un message de confirmation
            print(f"Dossier temporaire supprimé : {temp_dir}")
    except Exception as e:  # Si une erreur se produit...
        # Afficher l'erreur (le dossier n'est peut-être pas vide)
        print(f"Erreur lors de la suppression du dossier temporaire {temp_dir}: {str(e)}")
