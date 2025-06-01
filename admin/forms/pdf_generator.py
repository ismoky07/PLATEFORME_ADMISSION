"""
Générateur de PDF pour les candidatures
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import STUDY_LEVELS


def create_candidate_folder(nom, prenom):
    """Crée un dossier pour le candidat"""
    # Nettoyer le nom pour éviter les caractères problématiques
    safe_nom = "".join(c for c in nom if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_prenom = "".join(c for c in prenom if c.isalnum() or c in (' ', '-', '_')).strip()
    
    folder_name = f"{safe_nom}_{safe_prenom}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder_path = os.path.join("candidatures", folder_name)
    
    # Créer le dossier s'il n'existe pas
    os.makedirs(folder_path, exist_ok=True)
    
    return folder_path


def generate_candidate_pdf(personal_data, grades_data, uploaded_files, folder_path):
    """Génère un PDF avec toutes les données du candidat"""
    
    # Nom du fichier PDF
    pdf_filename = f"candidature_{personal_data['prenom']}_{personal_data['nom']}.pdf"
    pdf_path = os.path.join(folder_path, pdf_filename)
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=HexColor('#4facfe'),
        alignment=1  # Centré
    )
    
    # Style pour les en-têtes de section
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=HexColor('#333333'),
        backColor=HexColor('#f8f9fa'),
        borderPadding=10
    )
    
    # Style pour le texte normal
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 8
    
    # Contenu du PDF
    story = []
    
    # Titre principal
    story.append(Paragraph("📝 DOSSIER DE CANDIDATURE", title_style))
    story.append(Spacer(1, 20))
    
    # Informations personnelles
    story.append(Paragraph("1. INFORMATIONS PERSONNELLES", section_style))
    story.append(Spacer(1, 10))
    
    personal_info = [
        ['Nom :', personal_data.get('nom', 'Non renseigné')],
        ['Prénom :', personal_data.get('prenom', 'Non renseigné')],
        ['Email :', personal_data.get('email', 'Non renseigné')],
        ['Téléphone :', personal_data.get('telephone', 'Non renseigné')],
        ['Niveau d\'étude :', STUDY_LEVELS.get(personal_data.get('niveau_etude', ''), {}).get('name', 'Non renseigné')],
        ['Date de candidature :', datetime.now().strftime('%d/%m/%Y à %H:%M')]
    ]
    
    personal_table = Table(personal_info, colWidths=[2*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(personal_table)
    story.append(Spacer(1, 30))
    
    # Section des notes
    if grades_data:
        story.append(Paragraph("2. RELEVÉ DE NOTES SAISI", section_style))
        story.append(Spacer(1, 10))
        
        # Calcul de la moyenne
        valid_grades = [g for g in grades_data if g.get('matiere') and g.get('note') is not None]
        if valid_grades:
            weighted_sum = sum(g['note'] * g['coefficient'] for g in valid_grades)
            total_coefficients = sum(g['coefficient'] for g in valid_grades)
            average = round(weighted_sum / total_coefficients, 2) if total_coefficients > 0 else 0
            
            story.append(Paragraph(f"<b>Moyenne générale :</b> {average}/20", normal_style))
            story.append(Paragraph(f"<b>Nombre de matières :</b> {len(valid_grades)}", normal_style))
            story.append(Spacer(1, 15))
        
        # Tableau des notes
        notes_header = [['Matière', 'Note (/20)', 'Coefficient', 'Période', 'Année/Niveau']]
        notes_data = notes_header + [
            [
                grade.get('matiere', ''),
                f"{grade.get('note', 0)}/20" if grade.get('note') is not None else 'N/A',
                str(grade.get('coefficient', 1)),
                grade.get('periode', ''),
                grade.get('annee', '')
            ]
            for grade in valid_grades
        ]
        
        notes_table = Table(notes_data, colWidths=[2.2*inch, 1*inch, 1*inch, 1.3*inch, 1.5*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4facfe')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8f9fa')])
        ]))
        
        story.append(notes_table)
        story.append(Spacer(1, 30))
    
    # Section des documents
    story.append(Paragraph("3. DOCUMENTS TÉLÉVERSÉS", section_style))
    story.append(Spacer(1, 10))
    
    if uploaded_files:
        docs_data = [['Année/Niveau', 'Nom du fichier', 'Taille']]
        for year, file_info in uploaded_files.items():
            if hasattr(file_info, 'name') and hasattr(file_info, 'size'):
                size_mb = round(file_info.size / 1024 / 1024, 2)
                docs_data.append([year, file_info.name, f"{size_mb} MB"])
        
        docs_table = Table(docs_data, colWidths=[2*inch, 3*inch, 1.5*inch])
        docs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8f9fa')])
        ]))
        
        story.append(docs_table)
    else:
        story.append(Paragraph("Aucun document téléversé", normal_style))
    
    story.append(Spacer(1, 30))
    
    # Pied de page avec informations de validation
    story.append(Paragraph("4. INFORMATIONS DE SOUMISSION", section_style))
    story.append(Spacer(1, 10))
    
    submission_info = [
        ['Date de soumission :', datetime.now().strftime('%d/%m/%Y à %H:%M')],
        ['Statut :', 'Dossier soumis - En attente de vérification'],
        ['Référence :', f"CAND_{personal_data.get('nom', '')[:3].upper()}_{datetime.now().strftime('%Y%m%d%H%M')}"]
    ]
    
    submission_table = Table(submission_info, colWidths=[2*inch, 4*inch])
    submission_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(submission_table)
    
    # Note de bas de page
    story.append(Spacer(1, 40))
    story.append(Paragraph(
        "<i>Ce document a été généré automatiquement lors de la soumission de la candidature. "
        "Les informations devront être vérifiées par l'administration avec les documents officiels téléversés.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=colors.grey)
    ))
    
    # Construire le PDF
    doc.build(story)
    
    return pdf_path


def save_uploaded_files(uploaded_files, folder_path):
    """Sauvegarde les fichiers téléversés dans le dossier du candidat"""
    saved_files = []
    
    for year, uploaded_file in uploaded_files.items():
        if uploaded_file is not None:
            # Créer un nom de fichier sécurisé
            safe_filename = f"{year}_{uploaded_file.name}"
            file_path = os.path.join(folder_path, safe_filename)
            
            # Sauvegarder le fichier
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            saved_files.append({
                'year': year,
                'original_name': uploaded_file.name,
                'saved_path': file_path,
                'size': uploaded_file.size
            })
    
    return saved_files


def create_submission_summary(personal_data, grades_data, uploaded_files, folder_path):
    """Crée un fichier de résumé JSON de la soumission"""
    import json
    
    # Calculer les statistiques
    valid_grades = [g for g in grades_data if g.get('matiere') and g.get('note') is not None]
    
    if valid_grades:
        weighted_sum = sum(g['note'] * g['coefficient'] for g in valid_grades)
        total_coefficients = sum(g['coefficient'] for g in valid_grades)
        average = round(weighted_sum / total_coefficients, 2) if total_coefficients > 0 else 0
    else:
        average = 0
    
    summary = {
        'candidat': {
            'nom': personal_data.get('nom'),
            'prenom': personal_data.get('prenom'),
            'email': personal_data.get('email'),
            'telephone': personal_data.get('telephone'),
            'niveau_etude': personal_data.get('niveau_etude')
        },
        'statistiques': {
            'nombre_notes': len(valid_grades),
            'moyenne_generale': average,
            'nombre_documents': len(uploaded_files)
        },
        'notes': valid_grades,
        'documents': [
            {
                'annee': year,
                'nom_fichier': file.name if hasattr(file, 'name') else 'Unknown',
                'taille_mo': round(file.size / 1024 / 1024, 2) if hasattr(file, 'size') else 0
            }
            for year, file in uploaded_files.items() if file is not None
        ],
        'soumission': {
            'date': datetime.now().isoformat(),
            'dossier': folder_path,
            'reference': f"CAND_{personal_data.get('nom', '')[:3].upper()}_{datetime.now().strftime('%Y%m%d%H%M')}"
        }
    }
    
    # Sauvegarder le résumé JSON
    summary_path = os.path.join(folder_path, 'resume_candidature.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary_path, summary