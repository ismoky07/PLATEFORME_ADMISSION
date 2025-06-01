"""
Application Streamlit - Formulaire de Candidature Étudiant
Fichier principal
"""

import streamlit as st
from datetime import datetime
import json
import os

from config import STUDY_LEVELS
from utils import init_session_state, calculate_progress, calculate_average
from components import render_personal_info, render_grades_section, render_documents_section, render_summary_section
from styles import apply_custom_styles

# Configuration de la page
st.set_page_config(
    page_title="Saisie des Notes - Candidature",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Fonction principale de l'application"""
    
    # Application des styles CSS
    apply_custom_styles()
    
    # Créer le dossier candidatures s'il n'existe pas
    os.makedirs("candidatures", exist_ok=True)
    
    # Initialisation des variables de session
    init_session_state()
    
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>📝 Saisie des Notes - Candidature</h1>
        <p>Complétez votre dossier en saisissant vos notes et en téléversant vos bulletins</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Section 1: Informations Personnelles
    personal_data = render_personal_info()
    
    # Continuer seulement si un niveau d'étude est sélectionné
    if personal_data.get('niveau_etude'):
        config = STUDY_LEVELS[personal_data['niveau_etude']]
        
        # Section 2: Saisie des notes
        render_grades_section(config)
        
        # Section 3: Téléversement des bulletins
        render_documents_section(config)
        
        # Section 4: Résumé et soumission
        render_summary_section(config, personal_data)
    
    else:
        st.info("👆 Veuillez d'abord sélectionner votre niveau d'étude pour continuer.")

if __name__ == "__main__":
    main()