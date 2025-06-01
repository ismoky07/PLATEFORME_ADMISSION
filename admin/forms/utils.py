"""
Fonctions utilitaires pour l'application de candidature
"""

import streamlit as st
from datetime import datetime
import json

from config import STUDY_LEVELS, APP_CONFIG


def init_session_state():
    """Initialise les variables de session Streamlit"""
    if 'student_grades' not in st.session_state:
        st.session_state.student_grades = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}


def calculate_progress():
    """Calcule le pourcentage de progression du dossier"""
    progress = 0
    weights = APP_CONFIG["progress_weights"]
    
    # Informations personnelles (20%)
    if (st.session_state.get('nom') and 
        st.session_state.get('prenom') and 
        st.session_state.get('email') and 
        st.session_state.get('niveau_etude')):
        progress += weights["personal_info"]
    
    # Notes saisies (40%)
    valid_grades = get_valid_grades()
    if len(valid_grades) >= APP_CONFIG["min_grades_required"]:
        grade_progress = min(weights["grades"], (len(valid_grades) / 10) * weights["grades"])
        progress += grade_progress
    
    # Fichiers téléversés (40%)
    if st.session_state.get('niveau_etude'):
        required_files = len(STUDY_LEVELS[st.session_state.niveau_etude]['years'])
        uploaded_count = len(st.session_state.uploaded_files)
        if uploaded_count > 0:
            file_progress = min(weights["documents"], (uploaded_count / required_files) * weights["documents"])
            progress += file_progress
    
    return progress


def get_valid_grades():
    """Retourne la liste des notes valides (complètes)"""
    return [g for g in st.session_state.student_grades 
            if g.get('matiere') and g.get('note') is not None and 
            g.get('periode') and g.get('annee')]


def calculate_average():
    """Calcule la moyenne pondérée des notes"""
    valid_grades = get_valid_grades()
    
    if not valid_grades:
        return 0
    
    weighted_sum = sum(g['note'] * g['coefficient'] for g in valid_grades)
    total_coefficients = sum(g['coefficient'] for g in valid_grades)
    
    return round(weighted_sum / total_coefficients, 2) if total_coefficients > 0 else 0


def add_grade():
    """Ajoute une nouvelle note à la liste"""
    new_grade = {
        'id': len(st.session_state.student_grades),
        'matiere': '',
        'note': None,
        'coefficient': 1,
        'periode': '',
        'annee': ''
    }
    st.session_state.student_grades.append(new_grade)


def remove_grade(index):
    """Supprime une note de la liste"""
    if 0 <= index < len(st.session_state.student_grades):
        st.session_state.student_grades.pop(index)


def clear_all_grades():
    """Efface toutes les notes"""
    st.session_state.student_grades = []


def validate_submission(personal_data):
    """Valide si la candidature peut être soumise"""
    valid_grades = get_valid_grades()
    uploaded_count = len(st.session_state.uploaded_files)
    progress = calculate_progress()
    
    # Vérifications
    personal_complete = (
        personal_data.get('nom') and 
        personal_data.get('prenom') and 
        personal_data.get('email') and 
        personal_data.get('niveau_etude')
    )
    
    grades_sufficient = len(valid_grades) >= APP_CONFIG["min_grades_required"]
    files_uploaded = uploaded_count > 0
    progress_sufficient = progress >= APP_CONFIG["submission_threshold"]
    
    return {
        'can_submit': personal_complete and grades_sufficient and files_uploaded and progress_sufficient,
        'missing_items': get_missing_items(personal_complete, grades_sufficient, files_uploaded, len(valid_grades))
    }


def get_missing_items(personal_complete, grades_sufficient, files_uploaded, grade_count):
    """Retourne la liste des éléments manquants pour la soumission"""
    missing_items = []
    
    if not personal_complete:
        missing_items.append("Remplir toutes les informations personnelles")
    
    if not grades_sufficient:
        missing_items.append(f"Saisir au moins {APP_CONFIG['min_grades_required']} notes complètes (actuellement {grade_count})")
    
    if not files_uploaded:
        missing_items.append("Téléverser au moins un bulletin")
    
    return missing_items


def save_draft(personal_data):
    """Sauvegarde un brouillon de la candidature"""
    draft_data = {
        'personal_info': personal_data,
        'grades': st.session_state.student_grades,
        'files': list(st.session_state.uploaded_files.keys()),
        'timestamp': datetime.now().isoformat()
    }
    
    # En production, sauvegarder dans une base de données
    # Pour la démo, on utilise le session state
    st.session_state.draft_data = draft_data
    
    return draft_data


def create_submission_data(personal_data, config):
    """Crée les données de soumission finale"""
    valid_grades = get_valid_grades()
    uploaded_count = len(st.session_state.uploaded_files)
    average = calculate_average()
    
    return {
        'candidat': f"{personal_data['prenom']} {personal_data['nom']}",
        'email': personal_data['email'],
        'telephone': personal_data.get('telephone', ''),
        'niveau': config['name'],
        'bulletins': uploaded_count,
        'notes': len(valid_grades),
        'moyenne': average,
        'date_submission': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'grades_detail': valid_grades,
        'files_uploaded': list(st.session_state.uploaded_files.keys())
    }


def export_submission_json(submission_data):
    """Exporte les données de soumission en JSON"""
    return json.dumps(submission_data, indent=2, ensure_ascii=False)


def format_file_size(size_bytes):
    """Formate la taille d'un fichier en MB"""
    return size_bytes / 1024 / 1024


def get_file_upload_help_text():
    """Retourne le texte d'aide pour l'upload de fichiers"""
    file_types = ", ".join(APP_CONFIG["accepted_file_types"]).upper()
    max_size = APP_CONFIG["max_file_size_mb"]
    return f"Formats acceptés: {file_types} (max {max_size}MB)"