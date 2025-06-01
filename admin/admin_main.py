"""
Application Streamlit - Interface Administration
Vérification des candidatures et comparaison OCR
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import traceback

from admin_config import ADMIN_CONFIG, VALIDATION_STATUS
from admin_utils import load_candidatures, get_candidature_details, init_admin_session
from admin_components import (
    render_admin_header, render_candidatures_list, render_candidature_details,
    render_ocr_section, render_comparison_section, render_validation_section
)
from admin_styles import apply_admin_styles
from admin_auth import (
    require_authentication, show_user_info, check_permission,
    show_user_management, show_activity_logs
)

# Import agent OCR
try:
    from agentOCR.agent import (
        verifier_bulletins_scolaires,
        get_verification_status,
        detecter_bulletins_scolaires,
        ResultatVerification
    )
    AGENT_OCR_AVAILABLE = True
except ImportError:
    AGENT_OCR_AVAILABLE = False

st.set_page_config(
    page_title="Administration - Vérification des Candidatures",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Fonction principale de l'interface administration"""
    apply_admin_styles()
    require_authentication()
    init_admin_session()
    render_admin_header()
    
    with st.sidebar:
        st.title("🎯 Navigation")
        show_user_info()
        
        candidatures = load_candidatures()
        st.metric("Total candidatures", len(candidatures))
        
        if AGENT_OCR_AVAILABLE:
            st.success("🤖 Agent OCR: Actif")
        else:
            st.warning("🤖 Agent OCR: Inactif")
        
        # Filtres
        st.subheader("Filtres")
        status_filter = st.selectbox(
            "Statut",
            ["Tous"] + list(VALIDATION_STATUS.keys()),
            key="status_filter"
        )
        
        niveau_filter = st.selectbox(
            "Niveau d'étude", 
            ["Tous", "Baccalauréat", "Licence", "Master"],
            key="niveau_filter"
        )
        
        # Mode d'affichage
        st.subheader("Mode")
        view_modes = ["📋 Liste des candidatures", "🔍 Détail candidature", "📊 Tableau de bord"]
        
        if check_permission("manage_users"):
            view_modes.append("👥 Gestion utilisateurs")
        
        if check_permission("view_all"):
            view_modes.append("📋 Logs d'activité")
        
        view_mode = st.radio("Affichage", view_modes, key="view_mode")
    
    # Contenu principal
    if view_mode == "📋 Liste des candidatures":
        render_candidatures_overview(candidatures, status_filter, niveau_filter)
    elif view_mode == "🔍 Détail candidature":
        render_candidature_examination(candidatures)
    elif view_mode == "📊 Tableau de bord":
        render_admin_dashboard(candidatures)
    elif view_mode == "👥 Gestion utilisateurs":
        show_user_management()
    elif view_mode == "📋 Logs d'activité":
        show_activity_logs()

def render_candidatures_overview(candidatures, status_filter, niveau_filter):
    """Vue d'ensemble des candidatures"""
    st.header("📋 Liste des Candidatures")
    
    if not check_permission("view_all") and not check_permission("view_assigned"):
        st.error("🚫 Accès refusé.")
        return
    
    # Filtrage
    filtered_candidatures = candidatures.copy()
    
    if status_filter != "Tous":
        filtered_candidatures = [
            c for c in filtered_candidatures 
            if c.get('status', 'en_attente') == status_filter
        ]
    
    if niveau_filter != "Tous":
        filtered_candidatures = [
            c for c in filtered_candidatures 
            if c.get('niveau', '') == niveau_filter
        ]
    
    if not filtered_candidatures:
        st.info("Aucune candidature trouvée avec ces filtres.")
        return
    
    if AGENT_OCR_AVAILABLE:
        render_candidatures_list_enhanced(filtered_candidatures)
    else:
        render_candidatures_list(filtered_candidatures)

def render_candidatures_list_enhanced(candidatures):
    """Liste des candidatures avec statut de vérification bulletins"""
    for candidature in candidatures:
        candidat_brut = candidature.get('candidat', 'Candidat Inconnu')
        
        # Conversion sécurisée du nom
        if isinstance(candidat_brut, dict):
            candidat_nom = candidat_brut.get('nom', candidat_brut.get('name', 'Candidat Inconnu'))
        elif isinstance(candidat_brut, (list, tuple)):
            candidat_nom = str(candidat_brut[0]) if candidat_brut else 'Candidat Inconnu'
        else:
            candidat_nom = str(candidat_brut) if candidat_brut else 'Candidat Inconnu'
        
        niveau = candidature.get('niveau', 'Non spécifié')
        
        with st.expander(f"👤 {candidat_nom} - {niveau}", expanded=False):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**Email:** {candidature.get('email', 'N/A')}")
                date_submission = candidature.get('date_submission', 'Date inconnue')
                if isinstance(date_submission, str) and len(date_submission) >= 10:
                    st.write(f"**Date:** {date_submission[:10]}")
                else:
                    st.write(f"**Date:** {date_submission}")
                st.write(f"**Statut:** {candidature.get('status', 'en_attente')}")
            
            with col2:
                if AGENT_OCR_AVAILABLE:
                    try:
                        dossier = get_candidature_folder_path(candidature)
                        if dossier.exists():
                            detection = detecter_bulletins_scolaires(dossier)
                            if detection["bulletins_detectes"]:
                                st.success("🎓 Bulletins détectés")
                            else:
                                st.info("📄 Pas de bulletins")
                        else:
                            st.warning("📂 Dossier introuvable")
                    except Exception:
                        st.error("❌ Erreur détection")
                else:
                    st.info("🤖 Agent OCR inactif")
            
            with col3:
                if AGENT_OCR_AVAILABLE:
                    try:
                        dossier = get_candidature_folder_path(candidature)
                        if dossier.exists():
                            status = get_verification_status(dossier)
                            if status["verifie"]:
                                if status["concordance"]:
                                    st.success("✅ Honnête")
                                else:
                                    st.error(f"❌ {status['nb_discordances']} mensonge(s)")
                            else:
                                st.info("⏳ Non vérifié")
                        else:
                            st.warning("❓ N/A")
                    except Exception:
                        st.error("❌ Erreur")
                else:
                    st.info("⏳ Non disponible")
            
            with col4:
                candidat_safe = candidat_nom.replace(' ', '_').replace('/', '_')
                button_key = f"examine_{candidat_safe}_{hash(str(candidature)) % 10000}"
                
                if st.button(f"🔍 Examiner", key=button_key):
                    st.session_state.selected_candidature_direct = candidature
                    st.session_state.view_mode = "🔍 Détail candidature"
                    st.rerun()

def render_candidature_examination(candidatures):
    """Examen détaillé d'une candidature"""
    st.header("🔍 Examen de Candidature")
    
    if not check_permission("view_all") and not check_permission("view_assigned"):
        st.error("🚫 Accès refusé.")
        return
    
    if not candidatures:
        st.warning("Aucune candidature disponible.")
        return
    
    # Préparation des options
    candidature_options = []
    for c in candidatures:
        candidat = c.get('candidat', 'Candidat Inconnu')
        niveau = c.get('niveau', 'Non spécifié')
        date_submission = c.get('date_submission', 'Date inconnue')
        
        if isinstance(date_submission, str) and len(date_submission) >= 10:
            date_display = date_submission[:10]
        else:
            date_display = str(date_submission)
        
        candidature_options.append(f"{candidat} - {niveau} ({date_display})")
    
    # Gestion sélection directe
    selected_idx = 0
    if 'selected_candidature_direct' in st.session_state:
        candidature_directe = st.session_state.selected_candidature_direct
        candidat_direct = candidature_directe.get('candidat', '')
        
        for i, c in enumerate(candidatures):
            if c.get('candidat', '') == candidat_direct:
                selected_idx = i
                break
        del st.session_state.selected_candidature_direct
    
    selected_idx = st.selectbox(
        "Sélectionner une candidature",
        range(len(candidature_options)),
        format_func=lambda x: candidature_options[x],
        key="selected_candidature",
        index=selected_idx
    )
    
    if selected_idx is not None:
        candidature = candidatures[selected_idx]
        
        # Détection bulletins
        if AGENT_OCR_AVAILABLE:
            try:
                dossier_candidature = get_candidature_folder_path(candidature)
                detection_bulletins = detecter_bulletins_scolaires(dossier_candidature)
                
                if detection_bulletins["bulletins_detectes"] and detection_bulletins["formulaire_detecte"]:
                    st.success(f"🎓 **Bulletins scolaires détectés** - Vérification automatique disponible!")
                    
                    status_verif = get_verification_status(dossier_candidature)
                    if status_verif["verifie"]:
                        if status_verif["concordance"]:
                            st.success(f"✅ **Déjà vérifié** - Candidat honnête")
                        else:
                            st.error(f"❌ **Déjà vérifié** - {status_verif['nb_discordances']} mensonge(s)")
                    else:
                        st.info("⏳ **Vérification non effectuée**")
                        
            except Exception as e:
                st.warning(f"⚠️ Erreur détection bulletins: {str(e)}")
        
        # Onglets
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Détails", "🔍 OCR & Extraction", "⚖️ Comparaison", "✅ Validation"])
        
        with tab1:
            render_candidature_details(candidature)
        
        with tab2:
            if check_permission("view_all"):
                if AGENT_OCR_AVAILABLE:
                    render_ocr_section_enhanced(candidature)
                else:
                    render_ocr_section(candidature)
            else:
                st.warning("🚫 Permission OCR requise.")
        
        with tab3:
            if check_permission("view_all"):
                render_comparison_section(candidature)
                if AGENT_OCR_AVAILABLE:
                    render_comparison_bulletins_section(candidature)
            else:
                st.warning("🚫 Permission comparaison requise.")
        
        with tab4:
            if check_permission("validate") or check_permission("reject"):
                render_validation_section(candidature)
            else:
                st.warning("🚫 Permission validation/rejet requise.")

def render_admin_dashboard(candidatures):
    """Tableau de bord administrateur"""
    st.header("📊 Tableau de Bord Administration")
    
    if not check_permission("view_all"):
        st.error("🚫 Accès refusé.")
        return
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    total_candidatures = len(candidatures)
    en_attente = len([c for c in candidatures if c.get('status', 'en_attente') == 'en_attente'])
    validees = len([c for c in candidatures if c.get('status') == 'validee'])
    rejetees = len([c for c in candidatures if c.get('status') == 'rejetee'])
    
    with col1:
        st.metric("Total candidatures", total_candidatures)
    with col2:
        st.metric("En attente", en_attente)
    with col3:
        st.metric("Validées", validees)
    with col4:
        st.metric("Rejetées", rejetees)
    
    # Statistiques bulletins
    if AGENT_OCR_AVAILABLE:
        render_bulletins_statistics(candidatures)
    
    # Graphiques
    if candidatures:
        try:
            import pandas as pd
            import plotly.express as px
            
            # Répartition par niveau
            st.subheader("📈 Répartition par Niveau d'Étude")
            niveaux = [c.get('niveau', 'Non spécifié') for c in candidatures]
            df_niveau = pd.DataFrame({'niveau': niveaux})
            
            if not df_niveau.empty:
                niveau_counts = df_niveau['niveau'].value_counts()
                fig_niveau = px.pie(
                    values=niveau_counts.values,
                    names=niveau_counts.index,
                    title="Candidatures par Niveau"
                )
                st.plotly_chart(fig_niveau, use_container_width=True)
            
        except ImportError:
            st.warning("📊 Plotly non disponible.")
        
        # Actions rapides
        st.subheader("⚡ Actions Rapides")
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button("🔄 Actualiser les données", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col_action2:
            if check_permission("system_config"):
                if st.button("🧹 Nettoyer les fichiers temp", use_container_width=True):
                    cleanup_temp_files()
                    st.success("Nettoyage effectué !")

def render_bulletins_statistics(candidatures):
    """Affiche les statistiques des bulletins scolaires"""
    st.subheader("🎓 Statistiques Bulletins Scolaires")
    
    bulletins_stats = {
        "avec_bulletins": 0,
        "verifies": 0,
        "honnetes": 0,
        "menteurs": 0
    }
    
    for candidature in candidatures:
        try:
            dossier = get_candidature_folder_path(candidature)
            if dossier.exists():
                detection = detecter_bulletins_scolaires(dossier)
                if detection["bulletins_detectes"]:
                    bulletins_stats["avec_bulletins"] += 1
                    
                    status = get_verification_status(dossier)
                    if status["verifie"]:
                        bulletins_stats["verifies"] += 1
                        if status["concordance"]:
                            bulletins_stats["honnetes"] += 1
                        else:
                            bulletins_stats["menteurs"] += 1
        except Exception:
            continue
    
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    
    with col_b1:
        st.metric("📚 Avec bulletins", bulletins_stats["avec_bulletins"])
    with col_b2:
        st.metric("🔍 Vérifiés", bulletins_stats["verifies"])
    with col_b3:
        st.metric("✅ Honnêtes", bulletins_stats["honnetes"])
    with col_b4:
        st.metric("❌ Menteurs", bulletins_stats["menteurs"])

def render_ocr_section_enhanced(candidature):
    """Version améliorée de render_ocr_section avec agent bulletins"""
    st.subheader("🔍 OCR & Extraction")
    
    dossier_candidature = get_candidature_folder_path(candidature)
    
    if not dossier_candidature.exists():
        st.error(f"❌ Dossier candidature introuvable: {dossier_candidature}")
        return
    
    pdfs = list(dossier_candidature.glob("*.pdf"))
    st.info(f"📂 Dossier: `{dossier_candidature.name}` | 📄 {len(pdfs)} PDFs détectés")
    
    # Section bulletins scolaires
    try:
        detection_bulletins = detecter_bulletins_scolaires(dossier_candidature)
        
        if detection_bulletins["bulletins_detectes"]:
            render_bulletins_verification_section(candidature, dossier_candidature, detection_bulletins)
    except Exception as e:
        st.error(f"❌ Erreur détection bulletins: {str(e)}")
    
    # Section OCR générale
    st.markdown("---")
    st.markdown("### 🔍 **OCR Général**")
    render_ocr_section(candidature)

def render_bulletins_verification_section(candidature, dossier_candidature, detection_bulletins):
    """Section spécialisée pour la vérification des bulletins"""
    st.markdown("---")
    st.markdown("### 🎓 **Vérification Bulletins Scolaires**")
    
    # Informations détectées
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("**📋 Formulaire candidature:**")
        if detection_bulletins["formulaire_detecte"]:
            st.success(f"✅ {detection_bulletins['formulaire']}")
        else:
            st.warning("⚠️ Aucun formulaire détecté")
    
    with col_info2:
        st.markdown(f"**📚 Bulletins scolaires: ({detection_bulletins['nb_bulletins']})**")
        for bulletin in detection_bulletins["liste_bulletins"]:
            st.success(f"✅ {bulletin}")
    
    status_verif = get_verification_status(dossier_candidature)
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        bouton_text = "🔄 Reverifier" if status_verif["verifie"] else "🚀 Vérifier Bulletins"
        
        if st.button(
            bouton_text,
            type="primary",
            disabled=not detection_bulletins["verifiable"],
            key="btn_verifier_bulletins"
        ):
            if detection_bulletins["verifiable"]:
                lancer_verification_bulletins(candidature, dossier_candidature)
            else:
                st.error("❌ Formulaire ET bulletins requis")
    
    with col_action2:
        if status_verif["verifie"] and status_verif["rapport_excel"]:
            st.success(f"📊 Rapport disponible")
            if st.button("📋 Voir Rapport", key="btn_voir_rapport"):
                afficher_rapport_verification(Path(status_verif["rapport_excel"]))
        else:
            st.info("📊 Aucun rapport généré")
    
    with col_action3:
        if status_verif["verifie"]:
            if status_verif["concordance"]:
                st.success("✅ Honnête")
            else:
                st.error(f"❌ {status_verif['nb_discordances']} mensonge(s)")
        else:
            st.info("⏳ Non vérifié")

def lancer_verification_bulletins(candidature, dossier_candidature):
    """Lance la vérification des bulletins scolaires"""
    with st.spinner("🔍 Vérification en cours..."):
        try:
            progress_bar = st.progress(0)
            
            progress_bar.progress(30)
            resultat = verifier_bulletins_scolaires(str(dossier_candidature))
            
            progress_bar.progress(100)
            progress_bar.empty()
            
            # Affichage des résultats
            afficher_resultats_verification(resultat)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la vérification: {str(e)}")

def afficher_resultats_verification(resultat):
    """Affiche les résultats de la vérification"""
    st.markdown("---")
    st.markdown("### 📊 **Résultats de la Vérification**")
    
    # Résumé principal
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        candidat_nom = getattr(resultat, 'candidat_nom', 'INCONNU')
        candidat_prenom = getattr(resultat, 'candidat_prenom', 'INCONNU')
        st.metric("👤 Candidat", f"{candidat_prenom} {candidat_nom}")
    
    with col_res2:
        moyenne_declaree = getattr(resultat, 'moyenne_declaree', 0.0)
        st.metric("📊 Moyenne Déclarée", f"{moyenne_declaree}/20")
    
    with col_res3:
        concordance = getattr(resultat, 'concordance_globale', False)
        if concordance:
            st.success("✅ CANDIDAT HONNÊTE")
        else:
            st.error("❌ MENSONGES DÉTECTÉS")
    
    # Détails des discordances
    discordances = getattr(resultat, 'discordances', [])
    if discordances:
        st.markdown("#### 🚨 **Mensonges Détectés**")
        
        for i, discordance in enumerate(discordances, 1):
            matiere = getattr(discordance, 'matiere', 'INCONNU')
            gravite = getattr(discordance, 'gravite', 'INCONNU')
            
            with st.expander(f"🔥 Discordance #{i}: {matiere.upper()} ({gravite})"):
                col_d1, col_d2, col_d3 = st.columns(3)
                
                with col_d1:
                    periode = getattr(discordance, 'periode', 'INCONNU')
                    niveau = getattr(discordance, 'niveau', 'INCONNU')
                    st.markdown(f"**Période:** {periode}")
                    st.markdown(f"**Niveau:** {niveau}")
                
                with col_d2:
                    note_declaree = getattr(discordance, 'note_declaree', 0.0)
                    note_bulletin = getattr(discordance, 'note_bulletin', 0.0)
                    st.markdown(f"**Note Déclarée:** {note_declaree}/20")
                    st.markdown(f"**Note Bulletin:** {note_bulletin}/20")
                
                with col_d3:
                    ecart = getattr(discordance, 'ecart', 0.0)
                    st.markdown(f"**Écart:** {ecart:.2f} points")

def afficher_rapport_verification(fichier_excel):
    """Affiche un rapport de vérification existant"""
    try:
        import pandas as pd
        
        st.markdown("### 📋 **Rapport de Vérification**")
        
        with pd.ExcelFile(fichier_excel) as xls:
            for feuille in xls.sheet_names:
                df = pd.read_excel(fichier_excel, sheet_name=feuille)
                with st.expander(f"📊 {feuille}", expanded=(feuille == "📊 Résumé")):
                    st.dataframe(df, use_container_width=True)
        
        with open(fichier_excel, "rb") as file:
            st.download_button(
                label="💾 Télécharger Rapport Excel",
                data=file.read(),
                file_name=fichier_excel.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_download_rapport"
            )
    
    except Exception as e:
        st.error(f"❌ Erreur lecture rapport: {str(e)}")

def render_comparison_bulletins_section(candidature):
    """Section de comparaison spécifique aux bulletins"""
    dossier_candidature = get_candidature_folder_path(candidature)
    
    try:
        status_verif = get_verification_status(dossier_candidature)
        if status_verif["verifie"]:
            st.markdown("---")
            st.markdown("### 🎓 **Résultat Vérification Bulletins**")
            
            if status_verif["concordance"]:
                st.success(f"✅ **Candidat honnête**")
            else:
                st.error(f"❌ **{status_verif['nb_discordances']} mensonge(s) détecté(s)**")
            
            if st.button("📋 Voir détails complets", key="voir_details_bulletins"):
                if status_verif["rapport_excel"]:
                    afficher_rapport_verification(Path(status_verif["rapport_excel"]))
    except Exception as e:
        st.warning(f"⚠️ Erreur affichage comparaison bulletins: {str(e)}")

def get_candidature_folder_path(candidature):
    """Obtient le chemin du dossier candidature"""
    candidat_brut = candidature.get('candidat', 'inconnu')
    
    if isinstance(candidat_brut, dict):
        candidat_nom = candidat_brut.get('nom', candidat_brut.get('name', 'inconnu'))
    elif isinstance(candidat_brut, (list, tuple)):
        candidat_nom = str(candidat_brut[0]) if candidat_brut else 'inconnu'
    else:
        candidat_nom = str(candidat_brut) if candidat_brut else 'inconnu'
    
    candidatures_base = Path(ADMIN_CONFIG["candidatures_folder"])
    
    if not candidatures_base.exists():
        return candidatures_base / "dossier_inexistant"
    
    # Essayer par nom candidat
    try:
        for dossier in candidatures_base.iterdir():
            if dossier.is_dir() and candidat_nom.lower() in dossier.name.lower():
                return dossier
    except Exception:
        pass
    
    # Fallback
    nom_nettoye = candidat_nom.replace(' ', '_').replace('/', '_')
    return candidatures_base / nom_nettoye

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    import shutil
    
    candidatures_base = Path(ADMIN_CONFIG["candidatures_folder"])
    if candidatures_base.exists():
        for dossier in candidatures_base.iterdir():
            if dossier.is_dir():
                images_temp = dossier / "images_temp"
                if images_temp.exists():
                    try:
                        shutil.rmtree(images_temp)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()