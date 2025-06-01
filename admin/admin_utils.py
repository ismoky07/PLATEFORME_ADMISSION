"""
Fonctions utilitaires pour l'interface d'administration
"""

import streamlit as st
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from admin_config import ADMIN_CONFIG, VALIDATION_STATUS, GRADE_PATTERNS, ANOMALY_TYPES


def init_admin_session():
    """Initialise les variables de session pour l'admin"""
    if 'admin_ocr_results' not in st.session_state:
        st.session_state.admin_ocr_results = {}
    if 'admin_comparisons' not in st.session_state:
        st.session_state.admin_comparisons = {}
    if 'admin_validations' not in st.session_state:
        st.session_state.admin_validations = {}


@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def load_candidatures() -> List[Dict[str, Any]]:
    """Charge toutes les candidatures disponibles"""
    candidatures = []
    candidatures_folder = ADMIN_CONFIG["candidatures_folder"]
    
    if not os.path.exists(candidatures_folder):
        return candidatures
    
    for folder_name in os.listdir(candidatures_folder):
        folder_path = os.path.join(candidatures_folder, folder_name)
        
        if os.path.isdir(folder_path):
            candidature = load_candidature_from_folder(folder_path, folder_name)
            if candidature:
                candidatures.append(candidature)
    
    # Trier par date de soumission (plus récent en premier)
    candidatures.sort(key=lambda x: x.get('date_submission', ''), reverse=True)
    
    return candidatures


def load_candidature_from_folder(folder_path: str, folder_name: str) -> Optional[Dict[str, Any]]:
    """Charge une candidature depuis son dossier"""
    try:
        # Charger le résumé JSON
        resume_path = os.path.join(folder_path, 'resume_candidature.json')
        
        if os.path.exists(resume_path):
            with open(resume_path, 'r', encoding='utf-8') as f:
                candidature = json.load(f)
        else:
            # Fallback : créer à partir du nom du dossier
            candidature = create_candidature_from_folder_name(folder_name)
        
        # Ajouter les métadonnées du dossier
        candidature['folder_path'] = folder_path
        candidature['folder_name'] = folder_name
        
        # Charger la liste des fichiers
        candidature['files'] = list_candidature_files(folder_path)
        
        # Charger le statut de validation s'il existe
        status_path = os.path.join(folder_path, 'validation_status.json')
        if os.path.exists(status_path):
            with open(status_path, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
                candidature.update(validation_data)
        else:
            candidature['status'] = 'en_attente'
            candidature['validation_date'] = None
            candidature['validator'] = None
            candidature['comments'] = ''
        
        return candidature
        
    except Exception as e:
        st.error(f"Erreur lors du chargement de {folder_name}: {str(e)}")
        return None


def create_candidature_from_folder_name(folder_name: str) -> Dict[str, Any]:
    """Crée une candidature basique à partir du nom du dossier"""
    parts = folder_name.split('_')
    
    if len(parts) >= 3:
        nom = parts[0]
        prenom = parts[1]
        date_str = '_'.join(parts[2:])
    else:
        nom = "Inconnu"
        prenom = "Inconnu" 
        date_str = datetime.now().isoformat()
    
    return {
        'candidat': {
            'nom': nom,
            'prenom': prenom,
            'email': 'non-renseigne@email.com',
            'niveau_etude': 'inconnu'
        },
        'soumission': {
            'date': date_str,
            'reference': f"FALLBACK_{folder_name}"
        }
    }


def list_candidature_files(folder_path: str) -> Dict[str, List[str]]:
    """Liste tous les fichiers d'une candidature"""
    files = {
        'pdf': [],
        'json': [],
        'images': [],
        'bulletins': [],
        'autres': []
    }
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path):
            ext = filename.lower().split('.')[-1]
            
            if ext == 'pdf':
                if 'candidature' in filename.lower():
                    files['pdf'].append(filename)
                else:
                    files['bulletins'].append(filename)
            elif ext == 'json':
                files['json'].append(filename)
            elif ext in ['jpg', 'jpeg', 'png']:
                files['images'].append(filename)
            else:
                files['autres'].append(filename)
    
    return files


def get_candidature_details(candidature: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les détails formatés d'une candidature"""
    
    # Informations du candidat
    if 'candidat' in candidature:
        candidat_info = candidature['candidat']
    else:
        # Fallback pour ancien format
        candidat_info = {
            'nom': candidature.get('nom', 'Inconnu'),
            'prenom': candidature.get('prenom', 'Inconnu'),
            'email': candidature.get('email', 'Non renseigné'),
            'niveau_etude': candidature.get('niveau_etude', 'Inconnu')
        }
    
    # Statistiques
    stats = candidature.get('statistiques', {})
    
    # Notes détaillées
    notes = candidature.get('notes', [])
    
    # Documents
    documents = candidature.get('documents', [])
    
    # Informations de soumission
    soumission = candidature.get('soumission', {})
    
    return {
        'candidat': candidat_info,
        'statistiques': stats,
        'notes': notes,
        'documents': documents,
        'soumission': soumission,
        'status': candidature.get('status', 'en_attente'),
        'validation_date': candidature.get('validation_date'),
        'validator': candidature.get('validator'),
        'comments': candidature.get('comments', ''),
        'folder_path': candidature.get('folder_path'),
        'files': candidature.get('files', {})
    }


def simulate_ocr_extraction(candidature: Dict[str, Any]) -> Dict[str, Any]:
    """Simule l'extraction OCR des notes depuis les bulletins"""
    
    # Pour la démonstration, on génère des notes OCR basées sur les notes saisies
    # avec quelques variations et erreurs simulées
    
    import random
    
    notes_saisies = candidature.get('notes', [])
    notes_ocr = []
    
    for note_saisie in notes_saisies:
        # Simuler l'extraction OCR avec des variations
        note_ocr = note_saisie.copy()
        
        # Ajouter du bruit à la note (simulation d'erreurs OCR)
        if random.random() < 0.3:  # 30% de chance d'erreur
            variation = random.uniform(-2, 2)
            note_ocr['note'] = max(0, min(20, note_saisie['note'] + variation))
            note_ocr['confidence'] = random.uniform(0.4, 0.8)  # Faible confiance
        else:
            note_ocr['confidence'] = random.uniform(0.8, 0.95)  # Bonne confiance
        
        # Parfois changer légèrement le nom de la matière
        if random.random() < 0.2:  # 20% de chance
            variations_matieres = {
                'Mathématiques': 'Maths',
                'Histoire-Géographie': 'Hist-Géo',
                'Physique-Chimie': 'Physique',
                'Anglais': 'LV1 Anglais'
            }
            matiere_originale = note_ocr['matiere']
            note_ocr['matiere'] = variations_matieres.get(matiere_originale, matiere_originale)
        
        # Ajouter métadonnées OCR
        note_ocr['source'] = 'OCR'
        note_ocr['extraction_date'] = datetime.now().isoformat()
        note_ocr['bulletin_source'] = f"bulletin_{note_saisie.get('annee', 'inconnu')}.pdf"
        
        notes_ocr.append(note_ocr)
    
    # Parfois ajouter des notes supplémentaires détectées par OCR
    if random.random() < 0.4:  # 40% de chance
        matieres_supplementaires = ['EPS', 'Vie de classe', 'Conduite', 'Assiduité']
        matiere_supp = random.choice(matieres_supplementaires)
        
        note_supplementaire = {
            'matiere': matiere_supp,
            'note': round(random.uniform(12, 18), 1),
            'coefficient': 1,
            'periode': random.choice(['1er trimestre', '2ème trimestre', '3ème trimestre']),
            'annee': random.choice(['2nde', '1ère', 'Terminale']),
            'confidence': random.uniform(0.7, 0.9),
            'source': 'OCR',
            'extraction_date': datetime.now().isoformat(),
            'bulletin_source': 'bulletin_supplementaire.pdf'
        }
        notes_ocr.append(note_supplementaire)
    
    # Résultat OCR
    ocr_result = {
        'notes_extraites': notes_ocr,
        'nombre_notes': len(notes_ocr),
        'confiance_moyenne': sum(n.get('confidence', 0.8) for n in notes_ocr) / len(notes_ocr) if notes_ocr else 0,
        'bulletins_traites': list(set(n.get('bulletin_source', '') for n in notes_ocr)),
        'extraction_date': datetime.now().isoformat(),
        'ocr_engine': 'Tesseract + EasyOCR (simulation)',
        'processing_time': random.uniform(2.5, 8.3)  # Secondes simulées
    }
    
    return ocr_result


def compare_notes_ocr_manual(notes_manuelles: List[Dict], notes_ocr: List[Dict], tolerance: float = 1.0) -> Dict[str, Any]:
    """Compare les notes saisies manuellement avec celles extraites par OCR"""
    
    comparisons = []
    anomalies = []
    
    # Créer un index des notes OCR par matière (approximative)
    ocr_index = {}
    for note_ocr in notes_ocr:
        matiere_key = normalize_subject_name(note_ocr['matiere'])
        ocr_index[matiere_key] = note_ocr
    
    # Comparer chaque note manuelle
    for note_manuelle in notes_manuelles:
        matiere_manual = normalize_subject_name(note_manuelle['matiere'])
        
        # Chercher correspondance dans OCR
        best_match = None
        best_similarity = 0
        
        for matiere_ocr, note_ocr in ocr_index.items():
            similarity = calculate_subject_similarity(matiere_manual, matiere_ocr)
            if similarity > best_similarity and similarity > 0.7:
                best_similarity = similarity
                best_match = note_ocr
        
        # Créer la comparaison
        comparison = {
            'matiere_manuelle': note_manuelle['matiere'],
            'note_manuelle': note_manuelle['note'],
            'coefficient_manuel': note_manuelle.get('coefficient', 1),
            'periode_manuelle': note_manuelle.get('periode', ''),
            'annee_manuelle': note_manuelle.get('annee', ''),
        }
        
        if best_match:
            comparison.update({
                'matiere_ocr': best_match['matiere'],
                'note_ocr': best_match['note'],
                'coefficient_ocr': best_match.get('coefficient', 1),
                'confidence_ocr': best_match.get('confidence', 0.8),
                'similarite_matiere': best_similarity,
                'ecart_note': abs(note_manuelle['note'] - best_match['note']),
                'statut': 'trouve'
            })
            
            # Détecter anomalies
            ecart = comparison['ecart_note']
            if ecart > tolerance:
                anomaly = {
                    'type': 'ecart_note_majeur',
                    'matiere': note_manuelle['matiere'],
                    'ecart': ecart,
                    'note_manuelle': note_manuelle['note'],
                    'note_ocr': best_match['note'],
                    'severity': 'high' if ecart > 2.0 else 'medium'
                }
                anomalies.append(anomaly)
                comparison['anomalie'] = True
            else:
                comparison['anomalie'] = False
                
        else:
            comparison.update({
                'matiere_ocr': None,
                'note_ocr': None,
                'coefficient_ocr': None,
                'confidence_ocr': None,
                'similarite_matiere': 0,
                'ecart_note': None,
                'statut': 'non_trouve',
                'anomalie': True
            })
            
            # Anomalie : note manuelle non trouvée dans OCR
            anomaly = {
                'type': 'note_manquante_ocr',
                'matiere': note_manuelle['matiere'],
                'note_manuelle': note_manuelle['note'],
                'severity': 'medium'
            }
            anomalies.append(anomaly)
        
        comparisons.append(comparison)
    
    # Détecter notes OCR supplémentaires (non saisies manuellement)
    matieres_manuelles = {normalize_subject_name(n['matiere']) for n in notes_manuelles}
    
    for note_ocr in notes_ocr:
        matiere_ocr = normalize_subject_name(note_ocr['matiere'])
        
        # Chercher si cette note OCR a une correspondance manuelle
        found_manual = False
        for matiere_manual in matieres_manuelles:
            if calculate_subject_similarity(matiere_ocr, matiere_manual) > 0.7:
                found_manual = True
                break
        
        if not found_manual:
            anomaly = {
                'type': 'note_supplementaire_ocr',
                'matiere': note_ocr['matiere'],
                'note_ocr': note_ocr['note'],
                'confidence_ocr': note_ocr.get('confidence', 0.8),
                'severity': 'medium'
            }
            anomalies.append(anomaly)
    
    # Statistiques de la comparaison
    total_comparisons = len(comparisons)
    matches_found = len([c for c in comparisons if c['statut'] == 'trouve'])
    anomalies_count = len([c for c in comparisons if c.get('anomalie', False)])
    
    average_confidence = sum(
        c.get('confidence_ocr', 0) for c in comparisons 
        if c.get('confidence_ocr') is not None
    ) / max(matches_found, 1)
    
    result = {
        'comparisons': comparisons,
        'anomalies': anomalies,
        'statistiques': {
            'total_notes_manuelles': total_comparisons,
            'correspondances_trouvees': matches_found,
            'notes_non_trouvees': total_comparisons - matches_found,
            'anomalies_detectees': len(anomalies),
            'taux_correspondance': matches_found / total_comparisons if total_comparisons > 0 else 0,
            'confiance_moyenne_ocr': average_confidence,
            'tolerance_utilisee': tolerance
        },
        'date_comparaison': datetime.now().isoformat()
    }
    
    return result


def normalize_subject_name(subject: str) -> str:
    """Normalise le nom d'une matière pour la comparaison"""
    if not subject:
        return ""
    
    # Convertir en minuscules et supprimer les accents
    normalized = subject.lower()
    
    # Supprimer la ponctuation et les espaces multiples
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remplacements courants
    replacements = {
        'mathematiques': 'maths',
        'histoire geographie': 'hist geo',
        'histoire geo': 'hist geo',
        'hist geographie': 'hist geo',
        'physique chimie': 'physique',
        'sciences physiques': 'physique',
        'sciences vie terre': 'svt',
        'sciences de la vie et de la terre': 'svt',
        'education physique': 'eps',
        'education physique et sportive': 'eps',
        'langue vivante 1': 'lv1',
        'langue vivante 2': 'lv2'
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized


def calculate_subject_similarity(subject1: str, subject2: str) -> float:
    """Calcule la similarité entre deux noms de matières"""
    
    norm1 = normalize_subject_name(subject1)
    norm2 = normalize_subject_name(subject2)
    
    if norm1 == norm2:
        return 1.0
    
    # Algorithme de Jaccard pour les mots
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 and not words2:
        return 1.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def save_validation_status(candidature: Dict[str, Any], status: str, validator: str, comments: str = ""):
    """Sauvegarde le statut de validation d'une candidature"""
    
    folder_path = candidature.get('folder_path')
    if not folder_path or not os.path.exists(folder_path):
        raise ValueError("Dossier de candidature introuvable")
    
    validation_data = {
        'status': status,
        'validation_date': datetime.now().isoformat(),
        'validator': validator,
        'comments': comments,
        'status_history': candidature.get('status_history', [])
    }
    
    # Ajouter à l'historique
    validation_data['status_history'].append({
        'status': status,
        'date': validation_data['validation_date'],
        'validator': validator,
        'comments': comments
    })
    
    # Sauvegarder
    status_path = os.path.join(folder_path, 'validation_status.json')
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(validation_data, f, indent=2, ensure_ascii=False)
    
    # Nettoyer le cache
    st.cache_data.clear()
    
    return validation_data


def export_comparison_to_dict(comparison_result: Dict[str, Any], candidature: Dict[str, Any]) -> Dict[str, Any]:
    """Exporte les résultats de comparaison vers un dictionnaire structuré"""
    
    export_data = {
        'candidature': {
            'nom': candidature.get('candidat', {}).get('nom', ''),
            'prenom': candidature.get('candidat', {}).get('prenom', ''),
            'email': candidature.get('candidat', {}).get('email', ''),
            'niveau': candidature.get('candidat', {}).get('niveau_etude', ''),
            'reference': candidature.get('soumission', {}).get('reference', ''),
            'date_candidature': candidature.get('soumission', {}).get('date', '')
        },
        'statistiques_globales': comparison_result.get('statistiques', {}),
        'comparaisons_detaillees': comparison_result.get('comparisons', []),
        'anomalies': comparison_result.get('anomalies', []),
        'export_date': datetime.now().isoformat()
    }
    
    return export_data