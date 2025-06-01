"""
Configuration pour l'interface d'administration
"""

# Configuration de l'administration
ADMIN_CONFIG = {
    "candidatures_folder": "forms/candidatures",
    "ocr_confidence_threshold": 0.7,
    "tolerance_notes": {
        "exacte": 0,
        "faible": 0.5,
        "moyenne": 1.0,
        "forte": 2.0
    },
    "export_formats": ["xlsx", "csv", "json", "pdf"],
    "max_file_size_mb": 10,
    "ocr_languages": ["fra", "eng"],
    "backup_folder": "backups",
    "temp_folder": "temp"
}

# Statuts de validation des candidatures
VALIDATION_STATUS = {
    "en_attente": {
        "name": "En attente",
        "color": "#ffc107",
        "icon": "⏳",
        "description": "Candidature reçue, en cours d'examen"
    },
    "en_cours": {
        "name": "En cours d'examen",
        "color": "#17a2b8",
        "icon": "🔍",
        "description": "Candidature en cours de vérification"
    },
    "validee": {
        "name": "Validée",
        "color": "#28a745",
        "icon": "✅",
        "description": "Candidature acceptée"
    },
    "rejetee": {
        "name": "Rejetée",
        "color": "#dc3545",
        "icon": "❌",
        "description": "Candidature refusée"
    },
    "en_attente_documents": {
        "name": "Documents manquants",
        "color": "#fd7e14",
        "icon": "📄",
        "description": "Documents complémentaires requis"
    },
    "anomalie": {
        "name": "Anomalie détectée",
        "color": "#6f42c1",
        "icon": "⚠️",
        "description": "Écarts importants détectés"
    }
}

# Types d'anomalies détectables
ANOMALY_TYPES = {
    "ecart_note_majeur": {
        "name": "Écart de note majeur",
        "severity": "high",
        "threshold": 2.0,
        "description": "Différence de plus de 2 points entre note saisie et OCR"
    },
    "note_manquante_ocr": {
        "name": "Note non trouvée dans OCR",
        "severity": "medium",
        "description": "Matière saisie non détectée dans les bulletins"
    },
    "note_supplementaire_ocr": {
        "name": "Note supplémentaire détectée",
        "severity": "medium",
        "description": "Note détectée par OCR mais non saisie"
    },
    "confiance_ocr_faible": {
        "name": "Confiance OCR faible",
        "severity": "low",
        "threshold": 0.6,
        "description": "Extraction OCR avec faible niveau de confiance"
    },
    "moyenne_incoherente": {
        "name": "Moyenne incohérente",
        "severity": "high",
        "description": "Différence importante entre moyenne saisie et calculée"
    }
}

# Configuration OCR
OCR_CONFIG = {
    "engines": {
        "tesseract": {
            "name": "Tesseract",
            "languages": ["fra", "eng"],
            "confidence_threshold": 0.6
        },
        "paddleocr": {
            "name": "PaddleOCR", 
            "languages": ["fr", "en"],
            "confidence_threshold": 0.7
        },
        "easyocr": {
            "name": "EasyOCR",
            "languages": ["fr", "en"], 
            "confidence_threshold": 0.8
        }
    },
    "preprocessing": {
        "resize_factor": 2.0,
        "denoise": True,
        "deskew": True,
        "contrast_enhancement": True
    },
    "postprocessing": {
        "spell_check": True,
        "grade_pattern_matching": True,
        "subject_name_correction": True
    }
}

# Patterns de reconnaissance pour les notes
GRADE_PATTERNS = {
    "note_sur_20": r"(\d{1,2}[,.]?\d{0,2})\s*[/]\s*20",
    "note_decimale": r"(\d{1,2}[,.]?\d{1,2})",
    "coefficient": r"coef[ficient]*\s*[:=]?\s*(\d+)",
    "matiere": r"([A-Za-zÀ-ÿ\s\-]+)(?=\s*:|\s*\d|\s*$)",
    "periode": r"(trimestre|semestre)\s*(\d+|premier|deuxième|troisième|1er|2ème|3ème)",
    "moyenne": r"moyenne\s*[:=]?\s*(\d{1,2}[,.]?\d{0,2})"
}

# Messages de l'interface admin
ADMIN_MESSAGES = {
    "welcome": "Bienvenue dans l'interface d'administration",
    "no_candidatures": "Aucune candidature trouvée",
    "ocr_processing": "Traitement OCR en cours...",
    "comparison_complete": "Comparaison terminée",
    "validation_success": "Candidature validée avec succès",
    "rejection_success": "Candidature rejetée",
    "export_success": "Export généré avec succès",
    "error_loading": "Erreur lors du chargement des données",
    "error_ocr": "Erreur lors du traitement OCR",
    "error_export": "Erreur lors de l'export"
}

# Configuration des rapports
REPORT_CONFIG = {
    "formats": {
        "excel": {
            "extension": ".xlsx",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        },
        "csv": {
            "extension": ".csv",
            "mime": "text/csv"
        },
        "pdf": {
            "extension": ".pdf",
            "mime": "application/pdf"
        },
        "json": {
            "extension": ".json",
            "mime": "application/json"
        }
    },
    "templates": {
        "rapport_individuel": "Template pour rapport de candidature individuelle",
        "rapport_global": "Template pour rapport global des candidatures",
        "anomalies": "Template pour rapport d'anomalies",
        "statistiques": "Template pour rapport statistique"
    }
}

# Permissions et rôles
USER_ROLES = {
    "admin": {
        "name": "Administrateur",
        "permissions": [
            "view_all", "edit_all", "delete", "export", "validate", "reject", 
            "manage_users", "system_config"
        ]
    },
    "examiner": {
        "name": "Examinateur",
        "permissions": [
            "view_all", "export", "validate", "reject", "add_comments"
        ]
    },
    "viewer": {
        "name": "Visualiseur",
        "permissions": [
            "view_assigned", "export_limited", "add_comments"
        ]
    }
}

# Configuration des notifications
NOTIFICATION_CONFIG = {
    "email": {
        "enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "username": "",
        "password": ""
    },
    "templates": {
        "candidature_validee": "Template email candidature validée",
        "candidature_rejetee": "Template email candidature rejetée", 
        "documents_manquants": "Template email documents manquants",
        "anomalie_detectee": "Template email anomalie détectée"
    }
}