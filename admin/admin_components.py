"""
Composants d'interface pour l'administration
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from admin_config import VALIDATION_STATUS, ADMIN_MESSAGES, ANOMALY_TYPES
from admin_utils import (
    get_candidature_details, simulate_ocr_extraction, 
    compare_notes_ocr_manual, save_validation_status,
    export_comparison_to_dict
)


def render_admin_header():
    """Rendu de l'en-tête d'administration"""
    st.markdown("""
    <div class="admin-header">
        <h1>👨‍🏫 Interface Administration</h1>
        <p>Vérification et validation des candidatures</p>
    </div>
    """, unsafe_allow_html=True)


def render_candidatures_list(candidatures):
    """Rendu de la liste des candidatures"""
    
    if not candidatures:
        st.info(ADMIN_MESSAGES["no_candidatures"])
        return
    
    # Préparer les données pour le tableau
    data = []
    for i, candidature in enumerate(candidatures):
        details = get_candidature_details(candidature)
        
        status_info = VALIDATION_STATUS.get(details['status'], VALIDATION_STATUS['en_attente'])
        
        data.append({
            'Index': i,
            'Candidat': f"{details['candidat']['prenom']} {details['candidat']['nom']}",
            'Email': details['candidat']['email'],
            'Niveau': details['candidat']['niveau_etude'],
            'Notes': details['statistiques'].get('nombre_notes', 0),
            'Moyenne': f"{details['statistiques'].get('moyenne_generale', 0)}/20",
            'Documents': details['statistiques'].get('nombre_documents', 0),
            'Date candidature': details['soumission'].get('date', '')[:10] if details['soumission'].get('date') else '',
            'Statut': f"{status_info['icon']} {status_info['name']}",
            'Validateur': details.get('validator', ''),
            'Date validation': details.get('validation_date', '')[:10] if details.get('validation_date') else ''
        })
    
    df = pd.DataFrame(data)
    
    # Configuration des colonnes
    column_config = {
        'Index': st.column_config.NumberColumn('ID', width="small"),
        'Candidat': st.column_config.TextColumn('Candidat', width="medium"),
        'Email': st.column_config.TextColumn('Email', width="medium"),
        'Niveau': st.column_config.TextColumn('Niveau', width="small"),
        'Notes': st.column_config.NumberColumn('Notes', width="small"),
        'Moyenne': st.column_config.TextColumn('Moyenne', width="small"),
        'Documents': st.column_config.NumberColumn('Docs', width="small"),
        'Date candidature': st.column_config.DateColumn('Date candidature', width="medium"),
        'Statut': st.column_config.TextColumn('Statut', width="medium"),
        'Validateur': st.column_config.TextColumn('Validateur', width="medium"),
        'Date validation': st.column_config.DateColumn('Date validation', width="medium")
    }
    
    # Affichage du tableau avec sélection
    event = st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Actions rapides sur la sélection
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        candidature = candidatures[selected_idx]
        
        st.markdown("### Actions rapides")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Examiner", key=f"examine_{selected_idx}"):
                st.session_state.selected_candidature = selected_idx
                st.session_state.view_mode = "🔍 Détail candidature"
                st.rerun()
        
        with col2:
            if st.button("✅ Valider", key=f"validate_{selected_idx}"):
                save_validation_status(candidature, 'validee', 'Admin', 'Validation rapide')
                st.success("Candidature validée !")
                st.rerun()
        
        with col3:
            if st.button("❌ Rejeter", key=f"reject_{selected_idx}"):
                save_validation_status(candidature, 'rejetee', 'Admin', 'Rejet rapide')
                st.error("Candidature rejetée !")
                st.rerun()
        
        with col4:
            if st.button("📊 Export Excel", key=f"export_{selected_idx}"):
                from admin_excel import export_candidature_excel
                excel_data = export_candidature_excel(candidature)
                st.download_button(
                    label="💾 Télécharger",
                    data=excel_data,
                    file_name=f"candidature_{candidature.get('candidat', {}).get('nom', 'inconnu')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


def render_candidature_details(candidature):
    """Rendu des détails d'une candidature"""
    details = get_candidature_details(candidature)
    
    # Informations du candidat
    st.subheader("👤 Informations du Candidat")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Nom :** {details['candidat']['nom']}  
        **Prénom :** {details['candidat']['prenom']}  
        **Email :** {details['candidat']['email']}  
        **Téléphone :** {details['candidat'].get('telephone', 'Non renseigné')}
        """)
    
    with col2:
        st.markdown(f"""
        **Niveau d'étude :** {details['candidat']['niveau_etude']}  
        **Référence :** {details['soumission'].get('reference', 'N/A')}  
        **Date candidature :** {details['soumission'].get('date', 'N/A')[:16] if details['soumission'].get('date') else 'N/A'}  
        **Statut actuel :** {VALIDATION_STATUS.get(details['status'], VALIDATION_STATUS['en_attente'])['name']}
        """)
    
    # Statistiques
    st.subheader("📊 Statistiques")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric(
            "Notes saisies", 
            details['statistiques'].get('nombre_notes', 0)
        )
    
    with col_stat2:
        st.metric(
            "Moyenne générale", 
            f"{details['statistiques'].get('moyenne_generale', 0)}/20"
        )
    
    with col_stat3:
        st.metric(
            "Documents téléversés", 
            details['statistiques'].get('nombre_documents', 0)
        )
    
    # Notes détaillées
    if details['notes']:
        st.subheader("📝 Notes Saisies")
        
        df_notes = pd.DataFrame(details['notes'])
        
        # Reformater pour affichage
        if not df_notes.empty:
            df_display = df_notes[['matiere', 'note', 'coefficient', 'periode', 'annee']].copy()
            df_display.columns = ['Matière', 'Note (/20)', 'Coefficient', 'Période', 'Année']
            
            st.dataframe(df_display, use_container_width=True)
    
    # Documents téléversés
    st.subheader("📄 Documents Téléversés")
    
    if details['files']:
        for file_type, files in details['files'].items():
            if files:
                st.markdown(f"**{file_type.upper()} :**")
                for file_name in files:
                    file_path = os.path.join(details['folder_path'], file_name)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                        
                        col_file1, col_file2 = st.columns([3, 1])
                        with col_file1:
                            st.markdown(f"- {file_name} ({file_size:.1f} MB)")
                        with col_file2:
                            if st.button("📥", key=f"download_{file_name}"):
                                with open(file_path, "rb") as f:
                                    st.download_button(
                                        label=f"Télécharger {file_name}",
                                        data=f.read(),
                                        file_name=file_name,
                                        key=f"dl_btn_{file_name}"
                                    )
    else:
        st.info("Aucun fichier trouvé")
    
    # Historique de validation
    if details.get('validator') or details.get('comments'):
        st.subheader("📋 Historique de Validation")
        
        st.markdown(f"""
        **Validateur :** {details.get('validator', 'N/A')}  
        **Date de validation :** {details.get('validation_date', 'N/A')[:16] if details.get('validation_date') else 'N/A'}  
        **Commentaires :** {details.get('comments', 'Aucun commentaire')}
        """)


def render_ocr_section(candidature):
    """Rendu de la section OCR"""
    st.subheader("🔍 Extraction OCR des Bulletins")
    
    details = get_candidature_details(candidature)
    
    # Paramètres OCR
    col_ocr1, col_ocr2 = st.columns(2)
    
    with col_ocr1:
        ocr_engine = st.selectbox(
            "Moteur OCR",
            ["Tesseract", "PaddleOCR", "EasyOCR", "Combo (tous)"],
            key="ocr_engine"
        )
        
        confidence_threshold = st.slider(
            "Seuil de confiance",
            0.0, 1.0, 0.7,
            key="confidence_threshold"
        )
    
    with col_ocr2:
        preprocess_options = st.multiselect(
            "Prétraitement",
            ["Amélioration contraste", "Débruitage", "Redressement", "Redimensionnement"],
            default=["Amélioration contraste", "Débruitage"],
            key="preprocess_options"
        )
    
    # Lancer l'OCR
    if st.button("🚀 Lancer l'extraction OCR", type="primary"):
        
        with st.spinner("Traitement OCR en cours..."):
            # Simuler le temps de traitement
            import time
            time.sleep(2)
            
            # Simulation de l'extraction OCR
            ocr_result = simulate_ocr_extraction(candidature)
            
            # Sauvegarder dans la session
            candidature_key = f"ocr_{candidature.get('folder_name', 'unknown')}"
            st.session_state.admin_ocr_results[candidature_key] = ocr_result
        
        st.success("Extraction OCR terminée !")
    
    # Afficher les résultats OCR s'ils existent
    candidature_key = f"ocr_{candidature.get('folder_name', 'unknown')}"
    
    if candidature_key in st.session_state.admin_ocr_results:
        ocr_result = st.session_state.admin_ocr_results[candidature_key]
        
        st.subheader("📊 Résultats de l'Extraction")
        
        # Statistiques OCR
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Notes extraites", ocr_result['nombre_notes'])
        
        with col_stat2:
            st.metric("Confiance moyenne", f"{ocr_result['confiance_moyenne']:.1%}")
        
        with col_stat3:
            st.metric("Bulletins traités", len(ocr_result['bulletins_traites']))
        
        with col_stat4:
            st.metric("Temps traitement", f"{ocr_result['processing_time']:.1f}s")
        
        # Tableau des notes extraites
        st.subheader("📝 Notes Extraites par OCR")
        
        df_ocr = pd.DataFrame(ocr_result['notes_extraites'])
        
        if not df_ocr.empty:
            # Formatage pour affichage
            df_display = df_ocr[['matiere', 'note', 'coefficient', 'periode', 'annee', 'confidence']].copy()
            df_display.columns = ['Matière', 'Note (/20)', 'Coefficient', 'Période', 'Année', 'Confiance']
            df_display['Confiance'] = df_display['Confiance'].apply(lambda x: f"{x:.1%}")
            
            # Coloration selon la confiance
            def color_confidence(val):
                conf_val = float(val.strip('%')) / 100
                if conf_val >= 0.8:
                    return 'background-color: #d4edda'  # Vert
                elif conf_val >= 0.6:
                    return 'background-color: #fff3cd'  # Jaune
                else:
                    return 'background-color: #f8d7da'  # Rouge
            
            styled_df = df_display.style.applymap(color_confidence, subset=['Confiance'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Légende
            st.markdown("""
            **Légende confiance :** 
            🟢 Élevée (≥80%) | 🟡 Moyenne (60-80%) | 🔴 Faible (<60%)
            """)
        else:
            st.warning("Aucune note n'a pu être extraite")


def render_comparison_section(candidature):
    """Rendu de la section de comparaison"""
    st.subheader("⚖️ Comparaison OCR vs Saisie Manuelle")
    
    # Vérifier que l'OCR a été faite
    candidature_key = f"ocr_{candidature.get('folder_name', 'unknown')}"
    
    if candidature_key not in st.session_state.admin_ocr_results:
        st.warning("⚠️ Veuillez d'abord effectuer l'extraction OCR dans l'onglet précédent.")
        return
    
    ocr_result = st.session_state.admin_ocr_results[candidature_key]
    details = get_candidature_details(candidature)
    
    # Paramètres de comparaison
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        tolerance = st.selectbox(
            "Tolérance d'écart (points)",
            [0, 0.5, 1.0, 2.0],
            index=2,
            key="tolerance_comparison"
        )
    
    with col_comp2:
        similarity_threshold = st.slider(
            "Seuil de similarité matières",
            0.0, 1.0, 0.7,
            key="similarity_threshold"
        )
    
    # Lancer la comparaison
    if st.button("🔄 Comparer les notes", type="primary"):
        
        with st.spinner("Comparaison en cours..."):
            # Effectuer la comparaison
            comparison_result = compare_notes_ocr_manual(
                details['notes'],
                ocr_result['notes_extraites'],
                tolerance=tolerance
            )
            
            # Sauvegarder dans la session
            comparison_key = f"comp_{candidature.get('folder_name', 'unknown')}"
            st.session_state.admin_comparisons[comparison_key] = comparison_result
        
        st.success("Comparaison terminée !")
    
    # Afficher les résultats de comparaison
    comparison_key = f"comp_{candidature.get('folder_name', 'unknown')}"
    
    if comparison_key in st.session_state.admin_comparisons:
        comparison_result = st.session_state.admin_comparisons[comparison_key]
        
        # Statistiques de comparaison
        st.subheader("📈 Statistiques de la Comparaison")
        
        stats = comparison_result['statistiques']
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Correspondances trouvées", stats['correspondances_trouvees'])
        
        with col_stat2:
            st.metric("Taux de correspondance", f"{stats['taux_correspondance']:.1%}")
        
        with col_stat3:
            st.metric("Anomalies détectées", stats['anomalies_detectees'])
        
        with col_stat4:
            st.metric("Confiance OCR moy.", f"{stats['confiance_moyenne_ocr']:.1%}")
        
        # Détail des comparaisons
        st.subheader("🔍 Détail des Comparaisons")
        
        df_comp = pd.DataFrame(comparison_result['comparisons'])
        
        if not df_comp.empty:
            # Sélectionner et renommer les colonnes pour affichage
            columns_display = [
                'matiere_manuelle', 'note_manuelle', 'matiere_ocr', 'note_ocr', 
                'ecart_note', 'confidence_ocr', 'statut', 'anomalie'
            ]
            
            df_display = df_comp[columns_display].copy()
            df_display.columns = [
                'Matière Saisie', 'Note Saisie', 'Matière OCR', 'Note OCR', 
                'Écart', 'Confiance OCR', 'Statut', 'Anomalie'
            ]
            
            # Formatage
            df_display['Note Saisie'] = df_display['Note Saisie'].apply(lambda x: f"{x}/20")
            df_display['Note OCR'] = df_display['Note OCR'].apply(
                lambda x: f"{x}/20" if x is not None else "N/A"
            )
            df_display['Écart'] = df_display['Écart'].apply(
                lambda x: f"{x:.1f}" if x is not None else "N/A"
            )
            df_display['Confiance OCR'] = df_display['Confiance OCR'].apply(
                lambda x: f"{x:.1%}" if x is not None else "N/A"
            )
            df_display['Anomalie'] = df_display['Anomalie'].apply(
                lambda x: "⚠️ Oui" if x else "✅ Non"
            )
            
            # Coloration des lignes avec anomalies
            def highlight_anomalies(row):
                if row['Anomalie'] == "⚠️ Oui":
                    return ['background-color: #fff3cd'] * len(row)
                return [''] * len(row)
            
            styled_df = df_display.style.apply(highlight_anomalies, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        
        # Anomalies détectées
        if comparison_result['anomalies']:
            st.subheader("⚠️ Anomalies Détectées")
            
            for i, anomaly in enumerate(comparison_result['anomalies']):
                severity_colors = {
                    'high': '🔴',
                    'medium': '🟡', 
                    'low': '🟢'
                }
                
                severity_icon = severity_colors.get(anomaly['severity'], '🔵')
                anomaly_info = ANOMALY_TYPES.get(anomaly['type'], {})
                
                with st.expander(f"{severity_icon} {anomaly_info.get('name', anomaly['type'])}", expanded=True):
                    st.markdown(f"**Matière :** {anomaly['matiere']}")
                    
                    if 'note_manuelle' in anomaly:
                        st.markdown(f"**Note saisie :** {anomaly['note_manuelle']}/20")
                    
                    if 'note_ocr' in anomaly:
                        st.markdown(f"**Note OCR :** {anomaly['note_ocr']}/20")
                    
                    if 'ecart' in anomaly:
                        st.markdown(f"**Écart :** {anomaly['ecart']:.1f} points")
                    
                    st.markdown(f"**Description :** {anomaly_info.get('description', 'Anomalie détectée')}")


def render_validation_section(candidature):
    """Rendu de la section de validation"""
    st.subheader("✅ Validation de la Candidature")
    
    details = get_candidature_details(candidature)
    current_status = details['status']
    
    # Affichage du statut actuel
    status_info = VALIDATION_STATUS.get(current_status, VALIDATION_STATUS['en_attente'])
    
    st.markdown(f"""
    **Statut actuel :** {status_info['icon']} {status_info['name']}  
    **Validateur :** {details.get('validator', 'Aucun')}  
    **Date de validation :** {details.get('validation_date', 'N/A')[:16] if details.get('validation_date') else 'N/A'}
    """)
    
    if details.get('comments'):
        st.markdown(f"**Commentaires :** {details['comments']}")
    
    st.markdown("---")
    
    # Formulaire de validation
    st.markdown("### 📝 Nouvelle Validation")
    
    col_val1, col_val2 = st.columns(2)
    
    with col_val1:
        new_status = st.selectbox(
            "Nouveau statut",
            list(VALIDATION_STATUS.keys()),
            format_func=lambda x: f"{VALIDATION_STATUS[x]['icon']} {VALIDATION_STATUS[x]['name']}",
            index=list(VALIDATION_STATUS.keys()).index(current_status),
            key="new_status"
        )
    
    with col_val2:
        validator_name = st.text_input(
            "Nom du validateur",
            value="Admin",
            key="validator_name"
        )
    
    comments = st.text_area(
        "Commentaires",
        placeholder="Commentaires sur la validation...",
        key="validation_comments"
    )
    
    # Récapitulatif avant validation
    if new_status != current_status:
        new_status_info = VALIDATION_STATUS[new_status]
        
        st.markdown(f"""
        ### 📋 Récapitulatif de la validation
        
        **Candidat :** {details['candidat']['prenom']} {details['candidat']['nom']}  
        **Changement de statut :** {status_info['icon']} {status_info['name']} → {new_status_info['icon']} {new_status_info['name']}  
        **Validateur :** {validator_name}  
        **Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)
        
        if comments:
            st.markdown(f"**Commentaires :** {comments}")
    
    # Boutons de validation
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("✅ Valider la candidature", type="primary", disabled=(new_status != 'validee')):
            save_validation_status(candidature, 'validee', validator_name, comments)
            st.success("🎉 Candidature validée avec succès !")
            st.balloons()
            
            # Envoyer notification (simulation)
            st.info("📧 Email de confirmation envoyé au candidat")
            
            # Nettoyer le cache
            st.cache_data.clear()
            st.rerun()
    
    with col_btn2:
        if st.button("❌ Rejeter la candidature", disabled=(new_status != 'rejetee')):
            if comments.strip():
                save_validation_status(candidature, 'rejetee', validator_name, comments)
                st.error("❌ Candidature rejetée")
                
                # Envoyer notification (simulation)
                st.info("📧 Email de notification envoyé au candidat")
                
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("⚠️ Veuillez ajouter un commentaire pour justifier le rejet")
    
    with col_btn3:
        if st.button("💾 Sauvegarder le statut"):
            save_validation_status(candidature, new_status, validator_name, comments)
            st.success("💾 Statut sauvegardé")
            st.cache_data.clear()
            st.rerun()
    
    # Export des résultats de validation
    st.markdown("---")
    st.markdown("### 📊 Export des Résultats")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        if st.button("📄 Générer rapport PDF"):
            st.info("🔄 Génération du rapport PDF en cours...")
            # Ici, on intégrerait la génération du rapport PDF
    
    with col_export2:
        # Export Excel de la candidature avec comparaison
        comparison_key = f"comp_{candidature.get('folder_name', 'unknown')}"
        
        if comparison_key in st.session_state.admin_comparisons:
            if st.button("📊 Export Excel complet"):
                from admin_excel import export_complete_analysis_excel
                
                excel_data = export_complete_analysis_excel(
                    candidature,
                    st.session_state.admin_comparisons[comparison_key]
                )
                
                filename = f"analyse_complete_{details['candidat']['nom']}_{details['candidat']['prenom']}.xlsx"
                
                st.download_button(
                    label="💾 Télécharger l'analyse Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("💡 Effectuez d'abord une comparaison OCR pour l'export complet")