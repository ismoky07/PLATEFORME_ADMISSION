"""
Composants d'interface pour l'application Streamlit
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from config import STUDY_LEVELS, MESSAGES, APP_CONFIG
from utils import (
    add_grade, remove_grade, clear_all_grades, calculate_progress, 
    calculate_average, get_valid_grades, validate_submission,
    save_draft, create_submission_data, export_submission_json,
    format_file_size, get_file_upload_help_text
)
from pdf_generator import (
    create_candidate_folder, generate_candidate_pdf, 
    save_uploaded_files, create_submission_summary
)


def render_personal_info():
    """Rendu de la section des informations personnelles"""
    st.markdown("""
    <div class="section-header">
        <h2>1️⃣ Informations Personnelles</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nom = st.text_input("Nom *", key="nom", placeholder="Votre nom")
    
    with col2:
        prenom = st.text_input("Prénom *", key="prenom", placeholder="Votre prénom")
    
    with col3:
        niveau_etude = st.selectbox(
            "Niveau d'étude *", 
            [""] + list(STUDY_LEVELS.keys()),
            format_func=lambda x: "Sélectionnez votre niveau" if x == "" else STUDY_LEVELS[x]["name"],
            key="niveau_etude"
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        email = st.text_input("Email *", key="email", placeholder="votre.email@exemple.com")
    
    with col5:
        telephone = st.text_input("Téléphone", key="telephone", placeholder="06 12 34 56 78")
    
    return {
        'nom': nom,
        'prenom': prenom,
        'niveau_etude': niveau_etude,
        'email': email,
        'telephone': telephone
    }


def render_grades_section(config):
    """Rendu de la section de saisie des notes"""
    st.markdown("""
    <div class="section-header">
        <h2>2️⃣ Saisie de vos Notes</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="alert-info">
        {MESSAGES['info']['grades_instruction']}
    </div>
    """, unsafe_allow_html=True)
    
    # Boutons de gestion des notes
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("➕ Ajouter une note"):
            add_grade()
            st.rerun()
    
    with col_btn2:
        if st.button("🗑️ Effacer tout"):
            clear_all_grades()
            st.rerun()
    
    # Affichage du tableau des notes
    if st.session_state.student_grades:
        render_grades_table(config)
    else:
        st.info(MESSAGES['info']['add_grades'])


def render_grades_table(config):
    """Rendu du tableau de saisie des notes"""
    st.markdown("### Vos notes")
    
    # En-têtes du tableau
    col_headers = st.columns([3, 2, 2, 2, 2, 1])
    headers = ["Matière *", "Note (/20) *", "Coefficient *", "Période *", "Année/Niveau *", "Action"]
    
    for i, header in enumerate(headers):
        col_headers[i].markdown(f"**{header}**")
    
    # Lignes des notes
    for i, grade in enumerate(st.session_state.student_grades):
        cols = st.columns([3, 2, 2, 2, 2, 1])
        
        with cols[0]:
            grade['matiere'] = st.text_input(
                f"Matière {i}", 
                value=grade.get('matiere', ''),
                placeholder="Nom de la matière",
                key=f"matiere_{i}",
                label_visibility="collapsed"
            )
        
        with cols[1]:
            grade['note'] = st.number_input(
                f"Note {i}",
                min_value=0.0,
                max_value=20.0,
                step=0.1,
                value=grade.get('note', 0.0) if grade.get('note') is not None else 0.0,
                key=f"note_{i}",
                label_visibility="collapsed"
            )
        
        with cols[2]:
            grade['coefficient'] = st.number_input(
                f"Coefficient {i}",
                min_value=1,
                max_value=10,
                value=grade.get('coefficient', 1),
                key=f"coeff_{i}",
                label_visibility="collapsed"
            )
        
        with cols[3]:
            periode_index = 0
            if grade.get('periode') and grade['periode'] in config["periods"]:
                periode_index = config["periods"].index(grade['periode']) + 1
            
            grade['periode'] = st.selectbox(
                f"Période {i}",
                [""] + config["periods"],
                index=periode_index,
                key=f"periode_{i}",
                label_visibility="collapsed"
            )
        
        with cols[4]:
            annee_index = 0
            if grade.get('annee') and grade['annee'] in config["years"]:
                annee_index = config["years"].index(grade['annee']) + 1
            
            grade['annee'] = st.selectbox(
                f"Année {i}",
                [""] + config["years"],
                index=annee_index,
                key=f"annee_{i}",
                label_visibility="collapsed"
            )
        
        with cols[5]:
            if st.button("🗑️", key=f"remove_{i}"):
                remove_grade(i)
                st.rerun()


def render_documents_section(config):
    """Rendu de la section de téléversement des bulletins"""
    st.markdown("""
    <div class="section-header">
        <h2>3️⃣ Téléversement des Bulletins</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="alert-info">
        {MESSAGES['info']['documents_instruction']}
    </div>
    """, unsafe_allow_html=True)
    
    # Upload des fichiers pour chaque année
    for year in config["years"]:
        st.markdown(f"**📅 {year}**")
        
        uploaded_file = st.file_uploader(
            f"Bulletin de {year}",
            type=APP_CONFIG["accepted_file_types"],
            key=f"file_{year}",
            help=get_file_upload_help_text()
        )
        
        if uploaded_file:
            st.session_state.uploaded_files[year] = uploaded_file
            file_size = format_file_size(uploaded_file.size)
            st.success(MESSAGES['success']['file_uploaded'].format(
                filename=uploaded_file.name, 
                size=file_size
            ))
        
        st.markdown("---")


def render_summary_section(config, personal_data):
    """Rendu de la section de résumé et soumission"""
    st.markdown("""
    <div class="section-header">
        <h2>4️⃣ Résumé de votre Dossier</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Calcul des statistiques
    valid_grades = get_valid_grades()
    uploaded_count = len(st.session_state.uploaded_files)
    average = calculate_average()
    progress = calculate_progress()
    
    # Affichage des statistiques
    render_statistics(uploaded_count, len(valid_grades), average)
    
    # Barre de progression
    render_progress_bar(progress)
    
    # Tableau récapitulatif des notes
    if valid_grades:
        render_grades_summary(valid_grades)
    
    # Boutons d'action
    render_action_buttons(config, personal_data, progress)


def render_statistics(uploaded_count, grades_count, average):
    """Rendu des cartes de statistiques"""
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{uploaded_count}</div>
            <div class="stat-label">Bulletins téléversés</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{grades_count}</div>
            <div class="stat-label">Notes saisies</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{average}/20</div>
            <div class="stat-label">Moyenne générale</div>
        </div>
        """, unsafe_allow_html=True)


def render_progress_bar(progress):
    """Rendu de la barre de progression"""
    st.markdown(f"""
    <div class="progress-text">
        Progression du dossier: {progress:.0f}% complété
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress / 100)


def render_grades_summary(valid_grades):
    """Rendu du tableau récapitulatif des notes"""
    st.markdown("### 📊 Répartition de vos notes")
    
    df_grades = pd.DataFrame([
        {
            'Matière': g['matiere'],
            'Note': f"{g['note']}/20",
            'Coefficient': g['coefficient'],
            'Période': g['periode'],
            'Année': g['annee']
        }
        for g in valid_grades
    ])
    
    st.dataframe(df_grades, use_container_width=True)


def render_action_buttons(config, personal_data, progress):
    """Rendu des boutons d'action (sauvegarde et soumission)"""
    st.markdown("---")
    
    col_action1, col_action2 = st.columns(2)
    
    with col_action1:
        if st.button("💾 Sauvegarder le brouillon", use_container_width=True):
            save_draft(personal_data)
            st.success(MESSAGES['success']['draft_saved'])
    
    with col_action2:
        validation = validate_submission(personal_data)
        
        if st.button("✅ Soumettre la Candidature", 
                    disabled=not validation['can_submit'], 
                    use_container_width=True,
                    type="primary"):
            
            if validation['can_submit']:
                render_submission_success(config, personal_data)
            else:
                st.error(MESSAGES['error']['complete_required_fields'])
    
    # Affichage des éléments manquants
    if not validation['can_submit'] and progress < APP_CONFIG['submission_threshold']:
        render_missing_items(validation['missing_items'])


def render_submission_success(config, personal_data):
    """Rendu du message de succès de soumission avec création de dossier et PDF"""
    
    try:
        # 1. Créer le dossier candidat
        folder_path = create_candidate_folder(personal_data['nom'], personal_data['prenom'])
        st.success(f"📁 Dossier créé : {folder_path}")
        
        # 2. Sauvegarder les fichiers téléversés
        if st.session_state.uploaded_files:
            with st.spinner("💾 Sauvegarde des fichiers téléversés..."):
                saved_files = save_uploaded_files(st.session_state.uploaded_files, folder_path)
            st.success(f"📄 {len(saved_files)} fichier(s) sauvegardé(s)")
        
        # 3. Générer le PDF
        with st.spinner("📄 Génération du PDF en cours..."):
            pdf_path = generate_candidate_pdf(
                personal_data, 
                st.session_state.student_grades, 
                st.session_state.uploaded_files,
                folder_path
            )
        st.success(f"📄 PDF généré : {os.path.basename(pdf_path)}")
        
        # 4. Créer le résumé JSON
        summary_path, summary = create_submission_summary(
            personal_data,
            st.session_state.student_grades,
            st.session_state.uploaded_files,
            folder_path
        )
        
        # 5. Animation de succès
        st.balloons()
        
        # 6. Message de confirmation
        st.markdown(f"""
        <div class="alert-success">
            <h3>{MESSAGES['success']['submission_success']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 7. Informations du dossier créé
        st.markdown("### 📂 Dossier créé")
        st.info(f"**Emplacement :** `{folder_path}`")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Fichiers générés :**")
            st.write("- Candidature PDF")
            st.write("- Résumé JSON")
            for file_info in saved_files if 'saved_files' in locals() else []:
                st.write(f"- {file_info['original_name']}")
        
        with col2:
            st.markdown("**📊 Statistiques :**")
            st.write(f"- **Notes :** {summary['statistiques']['nombre_notes']}")
            st.write(f"- **Moyenne :** {summary['statistiques']['moyenne_generale']}/20")
            st.write(f"- **Documents :** {summary['statistiques']['nombre_documents']}")
            st.write(f"- **Référence :** {summary['soumission']['reference']}")
        
        # 8. Récapitulatif détaillé
        st.markdown("### 📋 Récapitulatif détaillé")
        submission_data = create_submission_data(personal_data, config)
        
        st.markdown(f"""
        - **Candidat :** {submission_data['candidat']}
        - **Email :** {submission_data['email']}
        - **Niveau :** {submission_data['niveau']}
        - **Date :** {submission_data['date_submission']}
        
        Votre dossier complet a été créé et sera examiné par l'administration.
        Vous recevrez une confirmation par email.
        """)
        
        # 9. Boutons de téléchargement
        st.markdown("### 💾 Téléchargements")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            # Télécharger le PDF
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Télécharger le PDF",
                        data=pdf_file.read(),
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        with col_dl2:
            # Télécharger le résumé JSON
            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding='utf-8') as json_file:
                    st.download_button(
                        label="📊 Télécharger JSON",
                        data=json_file.read(),
                        file_name=os.path.basename(summary_path),
                        mime="application/json",
                        use_container_width=True
                    )
        
        with col_dl3:
            # Télécharger le récapitulatif original (pour compatibilité)
            recap_json = export_submission_json(submission_data)
            filename = f"candidature_{personal_data['prenom']}_{personal_data['nom']}_{datetime.now().strftime('%Y%m%d')}.json"
            
            st.download_button(
                label="📥 Récapitulatif simple",
                data=recap_json,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )
        
        # 10. Instructions pour la suite
        st.markdown("### ℹ️ Prochaines étapes")
        st.info("""
        1. **Conservez** le dossier généré comme preuve de votre candidature
        2. **Vérifiez** votre email pour la confirmation de réception
        3. **Attendez** le traitement par l'administration (délai : 5-10 jours ouvrés)
        4. **Contactez-nous** si vous n'avez pas de nouvelles sous 15 jours
        """)
        
        # Nettoyer les données de session après soumission réussie
        st.session_state.student_grades = []
        st.session_state.uploaded_files = {}
        if 'draft_data' in st.session_state:
            del st.session_state.draft_data
            
    except Exception as e:
        st.error(f"❌ Erreur lors de la création du dossier : {str(e)}")
        st.error("Veuillez réessayer ou contacter l'administration.")
        
        # En cas d'erreur, proposer au moins le téléchargement JSON
        st.markdown("### 📥 Téléchargement de secours")
        submission_data = create_submission_data(personal_data, config)
        recap_json = export_submission_json(submission_data)
        filename = f"candidature_secours_{personal_data['prenom']}_{personal_data['nom']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        st.download_button(
            label="💾 Télécharger les données (JSON)",
            data=recap_json,
            file_name=filename,
            mime="application/json"
        )


def render_missing_items(missing_items):
    """Rendu de la liste des éléments manquants"""
    st.markdown("### ℹ️ Pour soumettre votre candidature :")
    for item in missing_items:
        st.markdown(f"- {item}")