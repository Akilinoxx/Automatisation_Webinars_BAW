# ===== IMPORTATION DES BIBLIOTHÈQUES =====
# requests : permet d'envoyer des requêtes HTTP vers des serveurs web
import requests

# os : permet de travailler avec les chemins de fichiers et les dossiers
import os

# typing : permet de spécifier les types de données attendus dans les fonctions
from typing import Optional, List, Tuple, Dict, Any

# tempfile : permet de créer des fichiers et dossiers temporaires
import tempfile

# Importer les fonctions de notre propre module file_splitter
# Le point (.) signifie "depuis le même package"
from .file_splitter import split_file, cleanup_chunks

# time : permet de faire des pauses dans l'exécution du programme
import time

# ===== CONSTANTES =====
# Limite de taille de fichier par morceau (en Mo)
# Cette constante définit la taille maximale de chaque morceau lorsqu'on découpe un fichier
# Les fichiers plus grands que cette taille seront découpés en plusieurs parties
MAX_CHUNK_SIZE_MB = 20

# ===== FONCTION PRINCIPALE D'ENVOI DE FICHIER AU WEBHOOK =====
def send_file_to_webhook(
    webhook_url: str,
    file_path: str,
    metadata: Dict[str, Any],
    progress_callback: Optional[callable] = None,
    max_retries: int = 3,
    retry_delay: int = 5
) -> tuple[bool, str]:
    """
    Envoie un fichier au webhook spécifié, en le découpant si nécessaire.
    Un webhook est une URL qui permet de recevoir des données depuis une application externe.
    
    Args:
        webhook_url: L'URL du webhook (adresse web où envoyer les données)
        file_path: Chemin vers le fichier à envoyer (où se trouve le fichier sur l'ordinateur)
        metadata: Métadonnées à envoyer avec le fichier (informations supplémentaires comme le titre, etc.)
        progress_callback: Fonction qui sera appelée pour mettre à jour la progression (optionnel)
        max_retries: Nombre maximum de tentatives en cas d'erreur (par défaut 3)
        retry_delay: Délai en secondes entre les tentatives (par défaut 5 secondes)
        
    Returns:
        tuple[bool, str]: Un tuple contenant:
            - Un booléen indiquant si l'envoi a réussi (True) ou échoué (False)
            - Un message décrivant le résultat ou l'erreur
    """
    # Utiliser try/except pour capturer toutes les erreurs possibles
    try:
        # Étape 1: Vérifier que le fichier existe avant d'essayer de l'envoyer
        if not os.path.exists(file_path):
            # Si le fichier n'existe pas, renvoyer une erreur immédiatement
            return False, f"Le fichier {file_path} n'existe pas"
        
        # Étape 2: Calculer la taille du fichier en mégaoctets (Mo)
        # os.path.getsize renvoie la taille en octets, donc on divise par 1024*1024 pour avoir des Mo
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Étape 3: Découper le fichier en morceaux si nécessaire
        # On utilise la fonction split_file de notre module file_splitter
        # Cette fonction renvoie une liste de tuples (chemin_du_morceau, numéro_du_morceau)
        chunks = split_file(file_path, MAX_CHUNK_SIZE_MB)
        
        # Compter le nombre total de morceaux
        total_chunks = len(chunks)
        
        # Utiliser un autre bloc try/except pour gérer les erreurs spécifiques à l'envoi
        # Cela permet de toujours nettoyer les fichiers temporaires, même en cas d'erreur
        try:
            # Étape 4: Envoyer chaque morceau un par un
            # On parcourt la liste des morceaux (chunks) avec une boucle for
            for chunk_path, chunk_num in chunks:
                # Étape 4.1: Mettre à jour l'interface utilisateur avec la progression
                # Si une fonction de callback a été fournie...
                if progress_callback:
                    # Calculer le pourcentage de progression (0-100%)
                    # On soustrait 1 du numéro du morceau car on commence à 0%
                    progress = (chunk_num - 1) / total_chunks * 100
                    
                    # Appeler la fonction de callback avec le pourcentage et un message
                    progress_callback(
                        progress,  # Pourcentage de progression
                        f"Envoi de la partie {chunk_num}/{total_chunks} au webhook..."  # Message
                    )
                
                # Étape 4.2: Préparer les métadonnées pour ce morceau spécifique
                # D'abord, copier les métadonnées de base pour ne pas modifier l'original
                chunk_metadata = metadata.copy()
                
                # Ajouter des informations spécifiques à ce morceau
                chunk_metadata.update({
                    'total_parts': total_chunks,      # Nombre total de morceaux
                    'part_number': chunk_num,        # Numéro de ce morceau
                    'total_size_mb': f"{file_size_mb:.1f}",  # Taille totale avec 1 décimale
                    'is_multipart': total_chunks > 1,  # Indique si le fichier est en plusieurs parties
                    'original_filename': os.path.basename(file_path)  # Nom du fichier original
                })
                
                # Étape 4.3: Préparer le fichier pour l'envoi
                # Ouvrir le fichier en mode binaire ('rb' = read binary)
                with open(chunk_path, 'rb') as f:
                    # Créer un dictionnaire pour le format attendu par requests.post
                    # La clé 'file' est le nom du paramètre attendu par le serveur
                    files = {
                        'file': (
                            os.path.basename(chunk_path),  # Nom du fichier à envoyer
                            f,                            # Contenu du fichier (objet fichier ouvert)
                            'audio/mpeg'                  # Type MIME du fichier (format audio MP3)
                        )
                    }
                    
                    # Étape 4.4: Tentatives d'envoi avec système de réessai
                    # Boucle pour essayer plusieurs fois en cas d'échec
                    for attempt in range(max_retries):
                        try:
                            # Envoyer la requête POST au webhook
                            # - webhook_url: l'adresse où envoyer les données
                            # - files: le fichier à envoyer
                            # - data: les métadonnées à envoyer avec le fichier
                            # - timeout: temps maximum d'attente (30 secondes)
                            response = requests.post(
                                webhook_url,
                                files=files,
                                data=chunk_metadata,
                                timeout=30
                            )
                            
                            # Étape 4.5: Vérifier le résultat de la requête
                            
                            # Si le code de statut est 200, cela signifie que tout s'est bien passé
                            # 200 est le code standard pour "OK" en HTTP
                            if response.status_code == 200:
                                # Sortir de la boucle des tentatives et passer au morceau suivant
                                break
                                
                            # Si erreur 520 (erreur spécifique à Cloudflare), on peut réessayer
                            if response.status_code == 520:
                                # Vérifier s'il nous reste des tentatives
                                if attempt < max_retries - 1:
                                    # Attendre le délai spécifié avant de réessayer
                                    time.sleep(retry_delay)
                                    # Continuer avec la prochaine itération de la boucle
                                    continue
                                else:
                                    # Si on a épuisé toutes les tentatives, renvoyer une erreur
                                    return False, f"Erreur Cloudflare (520) après {max_retries} tentatives"
                                    
                            # Étape 4.6: Gérer les autres types d'erreurs HTTP
                            # Pour les autres codes d'erreur, créer un message d'erreur détaillé
                            error_msg = (
                                f"Erreur HTTP {response.status_code}"  # Code d'erreur HTTP
                                # Ajouter le texte de la réponse s'il y en a un
                                f"{f' - {response.text}' if response.text else ''}"
                            )
                            # Renvoyer l'échec avec le message d'erreur
                            return False, error_msg
                            
                        # Étape 4.7: Gérer les différents types d'exceptions
                        
                        # Gérer les erreurs de timeout (délai d'attente dépassé)
                        except requests.Timeout:
                            # Vérifier s'il nous reste des tentatives
                            if attempt < max_retries - 1:
                                # Attendre avant de réessayer
                                time.sleep(retry_delay)
                                continue  # Passer à la tentative suivante
                            # Si on a épuisé toutes les tentatives
                            return False, "Timeout lors de l'envoi"
                            
                        # Gérer les erreurs de requête (problèmes réseau, DNS, etc.)
                        except requests.RequestException as e:
                            # Vérifier s'il nous reste des tentatives
                            if attempt < max_retries - 1:
                                # Attendre avant de réessayer
                                time.sleep(retry_delay)
                                continue  # Passer à la tentative suivante
                            # Si on a épuisé toutes les tentatives
                            return False, f"Erreur réseau lors de l'envoi : {str(e)}"
                            
                        # Gérer toutes les autres erreurs imprévues
                        except Exception as e:
                            # Pour les autres types d'erreurs, on ne réessaie pas
                            # car ce sont probablement des erreurs qui ne se résoudront pas en réessayant
                            return False, f"Erreur lors de l'envoi : {str(e)}"
                            
                    # Étape 4.8: Gérer le cas où toutes les tentatives ont échoué
                    # Cette partie s'exécute si la boucle for se termine normalement (sans break)
                    # ce qui signifie que toutes les tentatives ont échoué
                    else:
                        return False, "Erreur lors de l'envoi"
                    
            # Étape 5: Finaliser l'envoi après avoir envoyé tous les morceaux
            
            # Mettre à jour la progression à 100% pour indiquer que tout est terminé
            if progress_callback:
                progress_callback(100, "Envoi terminé !")
                
            # Renvoyer un message de succès avec le nombre de parties envoyées
            return True, f"Fichier envoyé avec succès en {total_chunks} partie(s)"
            
        # Étape 6: Nettoyer les fichiers temporaires
        # Le bloc 'finally' s'exécute toujours, que l'envoi ait réussi ou échoué
        finally:
            # Nettoyer les fichiers temporaires si le fichier a été découpé en plusieurs parties
            # Si total_chunks > 1, cela signifie que nous avons créé des fichiers temporaires
            if total_chunks > 1:
                # Appeler la fonction de nettoyage pour supprimer tous les fichiers temporaires
                cleanup_chunks(chunks)
            
    # Étape 7: Gérer les erreurs globales (en dehors de la boucle d'envoi)
    # Ces gestionnaires d'exceptions attrapent les erreurs qui pourraient se produire
    # avant même de commencer à envoyer les morceaux
    
    # Gérer les erreurs de timeout
    except requests.Timeout:
        return False, "Le délai d'attente a été dépassé lors de l'envoi"
    
    # Gérer les erreurs de requête (problèmes réseau, DNS, etc.)
    except requests.RequestException as e:
        return False, f"Erreur réseau lors de l'envoi : {str(e)}"
    
    # Gérer toutes les autres erreurs imprévues
    except Exception as e:
        return False, f"Erreur lors de l'envoi : {str(e)}"


# ===== FONCTION D'ENVOI DU NOMBRE DE PARTIES AU WEBHOOK =====
def send_parts_count_to_webhook(webhook_url: str, parts_count: int) -> tuple[bool, str]:
    """
    Envoie le nombre de parties choisi par l'utilisateur au webhook spécifié.
    Cette fonction est utilisée pour informer le serveur du nombre de parties à attendre.
    
    Args:
        webhook_url: L'URL du webhook (adresse web où envoyer les données)
        parts_count: Le nombre de parties choisi par l'utilisateur (combien de morceaux)
        
    Returns:
        tuple[bool, str]: Un tuple contenant:
            - Un booléen indiquant si l'envoi a réussi (True) ou échoué (False)
            - Un message décrivant le résultat ou l'erreur
    """
    # Utiliser try/except pour capturer toutes les erreurs possibles
    try:
        # Étape 1: Envoyer une requête POST au webhook avec le nombre de parties
        # - webhook_url: l'adresse où envoyer les données
        # - json: les données à envoyer au format JSON
        # - timeout: temps maximum d'attente (30 secondes)
        response = requests.post(
            webhook_url,
            json={'parts_count': parts_count},  # Envoyer un objet JSON simple
            timeout=30
        )
        
        # Étape 2: Vérifier le résultat de la requête
        # Si le code de statut est 200, cela signifie que tout s'est bien passé
        if response.status_code == 200:
            return True, "Nombre de parties envoyé avec succès"
        else:
            # Pour les autres codes, créer un message d'erreur détaillé
            return False, f"Erreur HTTP {response.status_code}{f' - {response.text}' if response.text else ''}"
            
    # Étape 3: Gérer les erreurs de requête (timeout, problèmes réseau, etc.)
    except requests.exceptions.RequestException as e:
        return False, f"Erreur lors de l'envoi : {str(e)}"
