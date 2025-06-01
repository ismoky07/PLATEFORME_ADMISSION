"""
Configuration de l'application - Niveaux d'étude et constantes
"""

# Configuration des niveaux d'étude
STUDY_LEVELS = {
    "bac": {
        "name": "Baccalauréat",
        "years": ["2nde", "1ère", "Terminale"],
        "subjects": {
            "2nde": [
                "Français", "Mathématiques", "Histoire-Géographie", 
                "SVT", "Physique-Chimie", "Anglais", "Espagnol", "EPS"
            ],
            "1ère": [
                "Français", "Philosophie", "Histoire-Géographie", "Mathématiques",
                "Spécialité 1", "Spécialité 2", "Spécialité 3", "Anglais", "EPS"
            ],
            "Terminale": [
                "Philosophie", "Histoire-Géographie", "Mathématiques",
                "Spécialité 1", "Spécialité 2", "Anglais", "EPS"
            ]
        },
        "periods": ["1er trimestre", "2ème trimestre", "3ème trimestre"]
    },
    "licence": {
        "name": "Licence",
        "years": ["1ère année", "2ème année", "3ème année"],
        "subjects": {
            "1ère année": [
                "Mathématiques", "Informatique", "Physique", 
                "Anglais", "Expression écrite", "Algorithmique"
            ],
            "2ème année": [
                "Mathématiques avancées", "Programmation", "Base de données",
                "Systèmes", "Réseaux", "Anglais"
            ],
            "3ème année": [
                "Génie logiciel", "Intelligence artificielle", "Sécurité",
                "Projet tutoré", "Stage", "Anglais professionnel"
            ]
        },
        "periods": ["1er semestre", "2ème semestre"]
    },
    "master": {
        "name": "Master",
        "years": ["Master 1", "Master 2"],
        "subjects": {
            "Master 1": [
                "Recherche opérationnelle", "Systèmes distribués", "Machine Learning",
                "Gestion de projet", "Anglais scientifique", "Mémoire"
            ],
            "Master 2": [
                "Projet de fin d'études", "Stage en entreprise", "Soutenance",
                "Anglais professionnel", "Spécialisation"
            ]
        },
        "periods": ["1er semestre", "2ème semestre"]
    }
}

# Constantes de l'application
APP_CONFIG = {
    "max_file_size_mb": 10,
    "accepted_file_types": ['pdf', 'jpg', 'jpeg', 'png'],
    "min_grades_required": 5,
    "submission_threshold": 80,
    "progress_weights": {
        "personal_info": 20,
        "grades": 40,
        "documents": 40
    }
}

# Messages de l'application
MESSAGES = {
    "info": {
        "grades_instruction": "✏️ Saisissez toutes vos notes. Soyez précis, ces informations seront vérifiées avec vos bulletins que vous téléverserez ensuite.",
        "documents_instruction": "📄 Téléversez tous vos bulletins selon votre niveau d'étude. Ces documents serviront à vérifier les notes que vous avez saisies.",
        "select_level": "👆 Veuillez d'abord sélectionner votre niveau d'étude pour continuer.",
        "add_grades": "Cliquez sur '➕ Ajouter une note' pour commencer à saisir vos notes."
    },
    "success": {
        "draft_saved": "✅ Brouillon sauvegardé avec succès !",
        "file_uploaded": "✅ Fichier téléversé: {filename} ({size:.2f} MB)",
        "submission_success": "🎉 Candidature soumise avec succès !"
    },
    "error": {
        "complete_required_fields": "⚠️ Veuillez compléter tous les champs obligatoires avant de soumettre.",
        "min_grades_required": "⚠️ Veuillez saisir au moins {min_grades} notes complètes."
    }
}