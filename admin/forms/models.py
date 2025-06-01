"""
Modèles de données pour l'application de candidature
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class PersonalInfo:
    """Informations personnelles du candidat"""
    nom: str
    prenom: str
    email: str
    niveau_etude: str
    telephone: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Vérifie si toutes les informations obligatoires sont remplies"""
        return bool(self.nom and self.prenom and self.email and self.niveau_etude)
    
    def full_name(self) -> str:
        """Retourne le nom complet"""
        return f"{self.prenom} {self.nom}"


@dataclass
class Grade:
    """Modèle pour une note"""
    id: int
    matiere: str
    note: Optional[float]
    coefficient: int
    periode: str
    annee: str
    
    def is_valid(self) -> bool:
        """Vérifie si la note est complète et valide"""
        return bool(
            self.matiere and 
            self.note is not None and 
            0 <= self.note <= 20 and
            self.coefficient > 0 and
            self.periode and 
            self.annee
        )
    
    def weighted_value(self) -> float:
        """Retourne la valeur pondérée de la note"""
        if self.note is None:
            return 0
        return self.note * self.coefficient


@dataclass
class UploadedDocument:
    """Modèle pour un document téléversé"""
    year: str
    filename: str
    size: int
    file_type: str
    upload_date: datetime
    
    def size_mb(self) -> float:
        """Retourne la taille en MB"""
        return self.size / 1024 / 1024


@dataclass
class ApplicationSummary:
    """Résumé de la candidature"""
    personal_info: PersonalInfo
    grades: List[Grade]
    documents: List[UploadedDocument]
    submission_date: datetime
    
    def valid_grades(self) -> List[Grade]:
        """Retourne uniquement les notes valides"""
        return [grade for grade in self.grades if grade.is_valid()]
    
    def calculate_average(self) -> float:
        """Calcule la moyenne pondérée"""
        valid_grades = self.valid_grades()
        if not valid_grades:
            return 0
        
        weighted_sum = sum(grade.weighted_value() for grade in valid_grades)
        total_coefficients = sum(grade.coefficient for grade in valid_grades)
        
        return round(weighted_sum / total_coefficients, 2) if total_coefficients > 0 else 0
    
    def completion_percentage(self) -> float:
        """Calcule le pourcentage de completion du dossier"""
        progress = 0
        
        # Informations personnelles (20%)
        if self.personal_info.is_complete():
            progress += 20
        
        # Notes (40%)
        valid_grade_count = len(self.valid_grades())
        if valid_grade_count >= 5:
            progress += min(40, (valid_grade_count / 10) * 40)
        
        # Documents (40%)
        if self.documents:
            # Calculer selon le niveau d'étude requis
            progress += min(40, (len(self.documents) / 3) * 40)  # Supposant 3 années max
        
        return progress
    
    def can_submit(self) -> bool:
        """Vérifie si la candidature peut être soumise"""
        return (
            self.personal_info.is_complete() and
            len(self.valid_grades()) >= 5 and
            len(self.documents) > 0 and
            self.completion_percentage() >= 80
        )
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour export"""
        return {
            'candidat': self.personal_info.full_name(),
            'email': self.personal_info.email,
            'telephone': self.personal_info.telephone,
            'niveau': self.personal_info.niveau_etude,
            'bulletins': len(self.documents),
            'notes': len(self.valid_grades()),
            'moyenne': self.calculate_average(),
            'completion': f"{self.completion_percentage():.0f}%",
            'date_submission': self.submission_date.strftime('%d/%m/%Y %H:%M'),
            'grades_detail': [
                {
                    'matiere': grade.matiere,
                    'note': grade.note,
                    'coefficient': grade.coefficient,
                    'periode': grade.periode,
                    'annee': grade.annee
                }
                for grade in self.valid_grades()
            ],
            'documents': [
                {
                    'year': doc.year,
                    'filename': doc.filename,
                    'size_mb': round(doc.size_mb(), 2)
                }
                for doc in self.documents
            ]
        }


class GradeValidator:
    """Validateur pour les notes"""
    
    @staticmethod
    def validate_note(note: float) -> bool:
        """Valide qu'une note est dans la plage acceptable"""
        return 0 <= note <= 20
    
    @staticmethod
    def validate_coefficient(coefficient: int) -> bool:
        """Valide qu'un coefficient est acceptable"""
        return 1 <= coefficient <= 10
    
    @staticmethod
    def validate_matiere(matiere: str) -> bool:
        """Valide qu'une matière n'est pas vide"""
        return bool(matiere and matiere.strip())


class ApplicationValidator:
    """Validateur pour l'ensemble de la candidature"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validation basique d'email"""
        return "@" in email and "." in email.split("@")[1]
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validation basique de téléphone (optionnel)"""
        if not phone:
            return True  # Téléphone optionnel
        # Enlever les espaces et vérifier si ce sont des chiffres
        cleaned = phone.replace(" ", "").replace(".", "").replace("-", "")
        return cleaned.isdigit() and len(cleaned) >= 10
    
    @staticmethod
    def get_missing_requirements(summary: ApplicationSummary) -> List[str]:
        """Retourne la liste des exigences manquantes"""
        missing = []
        
        if not summary.personal_info.is_complete():
            missing.append("Informations personnelles complètes")
        
        if len(summary.valid_grades()) < 5:
            missing.append(f"Au moins 5 notes valides (actuellement {len(summary.valid_grades())})")
        
        if not summary.documents:
            missing.append("Au moins un bulletin téléversé")
        
        if summary.completion_percentage() < 80:
            missing.append(f"Dossier complété à 80% (actuellement {summary.completion_percentage():.0f}%)")
        
        return missing