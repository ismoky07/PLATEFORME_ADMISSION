# ==================================================
# AGENT OCR BULLETINS SCOLAIRES - VERSION FINALE
# Intégré spécialement pour votre plateforme d'admission
# ==================================================

import os
import json
import base64
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Imports externes
import fitz  # PyMuPDF
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# ==================================================
# MODÈLES DE DONNÉES SPÉCIALISÉS
# ==================================================

@dataclass
class NoteDeclaree:
    """Note déclarée par le candidat dans le formulaire"""
    matiere: str
    note: float
    coefficient: int
    periode: str
    niveau: str

@dataclass
class NoteBulletin:
    """Note extraite d'un bulletin officiel"""
    matiere: str
    note: float
    periode: str
    niveau: str
    etablissement: Optional[str] = None

@dataclass
class Discordance:
    """Discordance détectée entre déclaré et réel"""
    matiere: str
    periode: str
    niveau: str
    note_declaree: float
    note_bulletin: float
    ecart: float
    gravite: str  # "LEGER", "MODERE", "GRAVE"

@dataclass
class ResultatVerification:
    """Résultat global de la vérification - Compatible avec votre système"""
    candidat_nom: str
    candidat_prenom: str
    moyenne_declaree: float
    moyenne_reelle: Optional[float]
    concordance_globale: bool
    discordances: List[Discordance]
    notes_non_verifiables: List[str]
    timestamp: str
    rapport_excel_path: Optional[str] = None
    
    def to_dict(self):
        """Convertit en dictionnaire pour sauvegarde JSON"""
        return {
            "candidat_nom": self.candidat_nom,
            "candidat_prenom": self.candidat_prenom,
            "moyenne_declaree": self.moyenne_declaree,
            "moyenne_reelle": self.moyenne_reelle,
            "concordance_globale": self.concordance_globale,
            "discordances": [asdict(d) for d in self.discordances],
            "notes_non_verifiables": self.notes_non_verifiables,
            "timestamp": self.timestamp,
            "rapport_excel_path": self.rapport_excel_path
        }

# ==================================================
# AGENT SPÉCIALISÉ BULLETINS SCOLAIRES
# ==================================================

class AgentVerificationScolaireAdmin:
    """Agent spécialisé pour vérifier les notes scolaires - Version Admin Production"""
    
    def __init__(self, dossier_candidature: str):
        self.dossier_candidature = Path(dossier_candidature)
        
        # VÉRIFICATIONS ROBUSTES
        self._valider_dossier_candidature()
        
        self.dossier_images = self.dossier_candidature / "images_temp"
        self.client_openai = self._init_openai()
        
        # Seuils de tolérance configurables
        self.seuil_leger = 0.5    # ±0.5 point = discordance légère
        self.seuil_modere = 1.0   # ±1.0 point = discordance modérée
        # >1.0 point = discordance grave
        
        # Créer le dossier images
        self.dossier_images.mkdir(exist_ok=True)
        
        # Configuration des patterns de détection
        self.patterns_formulaire = ["candidature*", "*formulaire*", "*dossier*", "*CAND_*"]
        self.patterns_bulletins = ["*bulletin*", "*2nde*", "*1ere*", "*1ère*", "*terminale*", "*tle*"]
        
    def _valider_dossier_candidature(self):
        """Valide le dossier candidature selon votre structure"""
        
        print(f"🔍 Validation du dossier: {self.dossier_candidature}")
        
        if not self.dossier_candidature.exists():
            # Essayer de trouver le dossier dans la structure forms/candidatures/
            candidatures_base = Path("forms/candidatures")
            nom_recherche = self.dossier_candidature.name
            
            print(f"🔍 Recherche dans forms/candidatures/ pour: {nom_recherche}")
            
            for dossier in candidatures_base.glob("*"):
                if dossier.is_dir() and nom_recherche.lower() in dossier.name.lower():
                    self.dossier_candidature = dossier
                    print(f"✅ Dossier trouvé: {self.dossier_candidature}")
                    return
            
            # Afficher les dossiers disponibles pour debug
            dossiers_disponibles = [d.name for d in candidatures_base.iterdir() if d.is_dir()]
            print(f"📂 Dossiers disponibles: {dossiers_disponibles}")
            
            raise FileNotFoundError(f"❌ Dossier candidature introuvable: {self.dossier_candidature}")
        
        # Vérifier la présence de PDFs
        pdfs = list(self.dossier_candidature.glob("*.pdf"))
        if not pdfs:
            raise FileNotFoundError(f"❌ Aucun PDF trouvé dans: {self.dossier_candidature}")
        
        print(f"✅ Dossier validé: {self.dossier_candidature}")
        print(f"✅ {len(pdfs)} PDFs détectés: {[pdf.name for pdf in pdfs]}")
        
    def _init_openai(self) -> OpenAI:
        """Initialise le client OpenAI avec gestion d'erreurs"""
        
        try:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("❌ OPENAI_API_KEY manquante dans le fichier .env")
            
            client = OpenAI(api_key=api_key)
            
            # Test de connexion
            try:
                # Test simple pour vérifier la validité de la clé
                test_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                print("✅ Connexion OpenAI établie")
            except Exception as e:
                print(f"⚠️ Avertissement connexion OpenAI: {e}")
            
            return client
            
        except Exception as e:
            print(f"❌ Erreur initialisation OpenAI: {e}")
            raise ValueError(f"Impossible d'initialiser OpenAI: {e}")
    
    def verifier_candidature_complete(self) -> ResultatVerification:
        """
        Workflow principal - Version production avec gestion d'erreurs complète
        """
        print("🎓 === DÉMARRAGE VÉRIFICATION BULLETINS SCOLAIRES ===")
        
        try:
            # Étape 1: Extraire les notes déclarées du formulaire
            print("\n📋 ÉTAPE 1: Extraction des notes déclarées...")
            formulaire_pdf = self._trouver_formulaire()
            notes_declarees = self._extraire_notes_formulaire(formulaire_pdf)
            candidat_nom, candidat_prenom, moyenne_declaree = self._extraire_infos_candidat(formulaire_pdf)
            
            print(f"✅ Candidat identifié: {candidat_prenom} {candidat_nom}")
            print(f"✅ Moyenne déclarée: {moyenne_declaree}/20")
            print(f"✅ {len(notes_declarees)} notes déclarées extraites")
            
            # Étape 2: Extraire les notes des bulletins officiels
            print("\n📚 ÉTAPE 2: Extraction des bulletins officiels...")
            bulletins_pdf = self._trouver_bulletins()
            notes_bulletins = self._extraire_notes_bulletins(bulletins_pdf)
            
            print(f"✅ {len(bulletins_pdf)} bulletins analysés")
            print(f"✅ {len(notes_bulletins)} notes extraites des bulletins")
            
            # Étape 3: Comparaison et détection des discordances
            print("\n⚖️ ÉTAPE 3: Comparaison déclaré vs réel...")
            discordances = self._comparer_notes(notes_declarees, notes_bulletins)
            notes_non_verifiables = self._identifier_notes_non_verifiables(notes_declarees, notes_bulletins)
            
            # Calculer moyenne réelle
            moyenne_reelle = self._calculer_moyenne_reelle(notes_bulletins)
            
            # Déterminer concordance globale
            concordance = len(discordances) == 0 and len(notes_non_verifiables) == 0
            
            print(f"✅ {len(discordances)} discordances détectées")
            print(f"✅ {len(notes_non_verifiables)} notes non vérifiables")
            print(f"✅ Concordance globale: {'OUI' if concordance else 'NON'}")
            
            # Créer le résultat
            resultat = ResultatVerification(
                candidat_nom=candidat_nom,
                candidat_prenom=candidat_prenom,
                moyenne_declaree=moyenne_declaree,
                moyenne_reelle=moyenne_reelle,
                concordance_globale=concordance,
                discordances=discordances,
                notes_non_verifiables=notes_non_verifiables,
                timestamp=datetime.now().isoformat()
            )
            
            # Étape 4: Génération du rapport Excel
            print("\n📊 ÉTAPE 4: Génération du rapport...")
            fichier_excel = self._generer_rapport_excel(resultat)
            resultat.rapport_excel_path = str(fichier_excel)
            print(f"✅ Rapport Excel généré: {fichier_excel}")
            
            # Étape 5: Sauvegarde JSON pour intégration système
            self._sauvegarder_resultat_json(resultat)
            
            print("\n🎉 === VÉRIFICATION TERMINÉE AVEC SUCCÈS ===")
            return resultat
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Retourner un résultat d'erreur pour éviter de planter l'interface
            return ResultatVerification(
                candidat_nom="ERREUR",
                candidat_prenom="ERREUR",
                moyenne_declaree=0.0,
                moyenne_reelle=None,
                concordance_globale=False,
                discordances=[],
                notes_non_verifiables=[f"Erreur système: {str(e)}"],
                timestamp=datetime.now().isoformat()
            )
    
    def _trouver_formulaire(self) -> Path:
        """Trouve le PDF formulaire de candidature avec fallbacks intelligents"""
        
        print("🔍 Recherche du formulaire candidature...")
        
        # Chercher par patterns de nom
        for pattern in self.patterns_formulaire:
            fichiers = list(self.dossier_candidature.glob(f"{pattern}.pdf"))
            if fichiers:
                print(f"✅ Formulaire trouvé via pattern '{pattern}': {fichiers[0].name}")
                return fichiers[0]
        
        # Si aucun pattern trouvé, chercher le PDF qui n'est pas un bulletin
        tous_pdfs = list(self.dossier_candidature.glob("*.pdf"))
        for pdf in tous_pdfs:
            nom = pdf.stem.lower()
            if not any(mot in nom for mot in ["bulletin", "2nde", "1ere", "1ère", "terminale", "tle"]):
                print(f"✅ Formulaire trouvé par exclusion: {pdf.name}")
                return pdf
        
        # Dernier recours: prendre le premier PDF
        if tous_pdfs:
            print(f"⚠️ Formulaire pris par défaut: {tous_pdfs[0].name}")
            return tous_pdfs[0]
        
        raise FileNotFoundError("❌ Aucun formulaire de candidature trouvé")
    
    def _trouver_bulletins(self) -> List[Path]:
        """Trouve tous les bulletins scolaires avec détection intelligente"""
        
        print("🔍 Recherche des bulletins scolaires...")
        
        bulletins = []
        
        # Chercher par patterns spécialisés
        for pattern in self.patterns_bulletins:
            bulletins.extend(self.dossier_candidature.glob(f"{pattern}.pdf"))
        
        # Dédupliquer
        bulletins = list(set(bulletins))
        
        if bulletins:
            print(f"✅ {len(bulletins)} bulletins trouvés:")
            for bulletin in bulletins:
                print(f"   📄 {bulletin.name}")
        else:
            print("❌ Aucun bulletin scolaire détecté")
            raise FileNotFoundError("Aucun bulletin scolaire trouvé")
        
        return bulletins
    
    def _extraire_notes_formulaire(self, formulaire_pdf: Path) -> List[NoteDeclaree]:
        """Extrait les notes déclarées du formulaire PDF via OCR"""
        
        print(f"📋 Extraction des notes du formulaire: {formulaire_pdf.name}")
        notes = []
        
        try:
            # Utiliser OCR pour extraire les notes du formulaire
            images = self._convertir_pdf_en_images([formulaire_pdf])
            
            prompt_formulaire = """Tu es un expert en analyse de formulaires de candidature scolaire français.

Analyse ce formulaire de candidature et extrait TOUTES les notes déclarées par le candidat.

Format de sortie JSON attendu:
{
  "notes_declarees": [
    {
      "matiere": "francais",
      "note": 12.5,
      "coefficient": 3,
      "periode": "1er trimestre",
      "niveau": "1ère"
    },
    {
      "matiere": "maths",
      "note": 14.0,
      "coefficient": 4,
      "periode": "2ème trimestre", 
      "niveau": "1ère"
    }
  ]
}

RÈGLES IMPORTANTES:
1. Cherche la section "RELEVÉ DE NOTES" ou "NOTES SAISIES" ou "BULLETINS"
2. Normalise les matières: "francais", "anglais", "maths", "histoire", "svt", "physique", etc.
3. Normalise les périodes: "1er trimestre", "2ème trimestre", "3ème trimestre"
4. Normalise les niveaux: "2nde", "1ère", "terminale"
5. Extrait UNIQUEMENT les notes déclarées par le candidat (pas d'invention)
6. Si une note est sur /20, garde la valeur. Si sur autre base, convertis sur /20
7. Coefficient par défaut = 1 si non spécifié"""

            for image_path in images:
                try:
                    print(f"   🔍 Analyse OCR de: {image_path.name}")
                    
                    with open(image_path, "rb") as f:
                        image_b64 = base64.b64encode(f.read()).decode()
                    
                    response = self.client_openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": prompt_formulaire},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Analyse ce formulaire et extrait les notes déclarées:"},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                                    }
                                ]
                            }
                        ],
                        max_tokens=2000,
                        temperature=0.1
                    )
                    
                    contenu = response.choices[0].message.content
                    print(f"   📝 Réponse OCR reçue: {len(contenu)} caractères")
                    
                    # Parser la réponse JSON
                    if "```json" in contenu:
                        contenu = contenu.split("```json")[1].split("```")[0]
                    elif "```" in contenu:
                        contenu = contenu.split("```")[1].split("```")[0]
                    
                    data = json.loads(contenu.strip())
                    
                    # Convertir en objets NoteDeclaree
                    for note_data in data.get("notes_declarees", []):
                        try:
                            note = NoteDeclaree(
                                matiere=note_data.get("matiere", "").lower().strip(),
                                note=float(note_data.get("note", 0)),
                                coefficient=int(note_data.get("coefficient", 1)),
                                periode=note_data.get("periode", "").strip(),
                                niveau=note_data.get("niveau", "").strip()
                            )
                            notes.append(note)
                            print(f"      ✓ Note extraite: {note.matiere} = {note.note}/20 ({note.periode}, {note.niveau})")
                        except (ValueError, TypeError) as e:
                            print(f"      ⚠️ Erreur parsing note: {e}")
                            continue
                        
                except json.JSONDecodeError as e:
                    print(f"      ❌ Erreur JSON pour {image_path.name}: {e}")
                    print(f"      Contenu reçu: {contenu[:200]}...")
                except Exception as e:
                    print(f"      ❌ Erreur OCR pour {image_path.name}: {e}")
                    
        except Exception as e:
            print(f"❌ Erreur générale extraction formulaire: {e}")
        
        print(f"📋 Résultat: {len(notes)} notes extraites du formulaire")
        return notes
    
    def _extraire_infos_candidat(self, formulaire_pdf: Path) -> Tuple[str, str, float]:
        """Extrait nom, prénom et moyenne du candidat via OCR"""
        
        print(f"👤 Extraction des informations candidat de: {formulaire_pdf.name}")
        
        try:
            # Utiliser OCR pour extraire les infos candidat
            images = self._convertir_pdf_en_images([formulaire_pdf])
            
            prompt_candidat = """Tu es un expert en analyse de formulaires de candidature.

Analyse ce formulaire et extrait les informations personnelles du candidat.

Format JSON attendu:
{
  "nom": "OUATTARA",
  "prenom": "Ismael", 
  "moyenne_generale": 11.54
}

RÈGLES:
1. Cherche la section "INFORMATIONS PERSONNELLES" ou similaire
2. Extrait le nom et prénom EXACT du candidat
3. Cherche "Moyenne générale" déclarée par le candidat
4. Ne pas inventer d'informations manquantes
5. Retourne null pour les champs non trouvés"""

            for image_path in images:
                try:
                    with open(image_path, "rb") as f:
                        image_b64 = base64.b64encode(f.read()).decode()
                    
                    response = self.client_openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": prompt_candidat},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extrait les infos personnelles du candidat:"},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                                    }
                                ]
                            }
                        ],
                        max_tokens=500,
                        temperature=0.1
                    )
                    
                    contenu = response.choices[0].message.content
                    
                    # Parser la réponse JSON
                    if "```json" in contenu:
                        contenu = contenu.split("```json")[1].split("```")[0]
                    elif "```" in contenu:
                        contenu = contenu.split("```")[1].split("```")[0]
                    
                    data = json.loads(contenu.strip())
                    
                    nom = data.get("nom", "INCONNU") or "INCONNU"
                    prenom = data.get("prenom", "INCONNU") or "INCONNU"
                    moyenne = float(data.get("moyenne_generale", 0.0) or 0.0)
                    
                    print(f"   ✅ Candidat identifié: {prenom} {nom} (moyenne: {moyenne}/20)")
                    return nom, prenom, moyenne
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Erreur JSON extraction candidat: {e}")
                except Exception as e:
                    print(f"   ❌ Erreur OCR candidat: {e}")
            
            # Fallback si OCR échoue - essayer d'extraire du nom de dossier
            nom_dossier = self.dossier_candidature.name
            if "_" in nom_dossier:
                parts = nom_dossier.split("_")
                if len(parts) >= 2:
                    nom_fallback = parts[0].upper()
                    prenom_fallback = parts[1].capitalize()
                    print(f"   🔄 Fallback depuis nom dossier: {prenom_fallback} {nom_fallback}")
                    return nom_fallback, prenom_fallback, 0.0
            
            return "INCONNU", "INCONNU", 0.0
            
        except Exception as e:
            print(f"❌ Erreur extraction infos candidat: {e}")
            return "INCONNU", "INCONNU", 0.0
    
    def _extraire_notes_bulletins(self, bulletins_pdf: List[Path]) -> List[NoteBulletin]:
        """Extrait les notes des bulletins officiels via OCR"""
        
        print(f"📚 Extraction des notes de {len(bulletins_pdf)} bulletins...")
        notes_bulletins = []
        
        prompt_systeme = """Tu es un expert en analyse de bulletins scolaires français.

Analyse ce bulletin scolaire et extrait TOUTES les notes visibles.

Format JSON attendu:
{
  "bulletin": {
    "periode": "1er trimestre",
    "niveau": "1ère", 
    "etablissement": "Lycée Victor Hugo",
    "notes": [
      {
        "matiere": "francais",
        "note": 12.5
      },
      {
        "matiere": "maths",
        "note": 14.0
      },
      {
        "matiere": "anglais", 
        "note": 13.5
      }
    ]
  }
}

RÈGLES IMPORTANTES:
1. Normalise les matières: "francais", "anglais", "maths", "histoire", "svt", "physique", "chimie", "philosophie", etc.
2. Normalise les périodes: "1er trimestre", "2ème trimestre", "3ème trimestre"
3. Normalise les niveaux: "2nde", "1ère", "terminale"
4. Extrait UNIQUEMENT les notes numériques sur 20
5. Ne pas inventer de données manquantes
6. Ignore les moyennes de classe, ne garde que les notes individuelles de l'élève"""

        for bulletin_pdf in bulletins_pdf:
            try:
                print(f"   📖 Analyse du bulletin: {bulletin_pdf.name}")
                
                # Convertir PDF en images
                images = self._convertir_pdf_en_images([bulletin_pdf])
                
                for image_path in images:
                    try:
                        # Encoder l'image
                        with open(image_path, "rb") as f:
                            image_b64 = base64.b64encode(f.read()).decode()
                        
                        # Appel OCR OpenAI
                        response = self.client_openai.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": prompt_systeme},
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "Analyse ce bulletin scolaire et extrait toutes les notes:"},
                                        {
                                            "type": "image_url",
                                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                                        }
                                    ]
                                }
                            ],
                            max_tokens=2000,
                            temperature=0.1
                        )
                        
                        # Parser la réponse
                        contenu = response.choices[0].message.content
                        
                        try:
                            # Nettoyer le JSON
                            if "```json" in contenu:
                                contenu = contenu.split("```json")[1].split("```")[0]
                            elif "```" in contenu:
                                contenu = contenu.split("```")[1].split("```")[0]
                            
                            data = json.loads(contenu.strip())
                            
                            # Extraire les infos du bulletin
                            bulletin_info = data.get("bulletin", {})
                            periode = bulletin_info.get("periode", "")
                            niveau = bulletin_info.get("niveau", "")
                            etablissement = bulletin_info.get("etablissement", "")
                            
                            # Convertir en objets NoteBulletin
                            notes_dans_bulletin = 0
                            for note_data in bulletin_info.get("notes", []):
                                try:
                                    note = NoteBulletin(
                                        matiere=note_data.get("matiere", "").lower().strip(),
                                        note=float(note_data.get("note", 0)),
                                        periode=periode,
                                        niveau=niveau,
                                        etablissement=etablissement
                                    )
                                    notes_bulletins.append(note)
                                    notes_dans_bulletin += 1
                                    print(f"      ✓ Note extraite: {note.matiere} = {note.note}/20 ({note.periode}, {note.niveau})")
                                except (ValueError, TypeError) as e:
                                    print(f"      ⚠️ Erreur conversion note: {e}")
                                    continue
                            
                            print(f"   ✅ {notes_dans_bulletin} notes extraites de {bulletin_pdf.name}")
                            
                        except json.JSONDecodeError as e:
                            print(f"      ❌ Erreur JSON pour {image_path.name}: {e}")
                            print(f"      Contenu reçu: {contenu[:200]}...")
                            
                    except Exception as e:
                        print(f"      ❌ Erreur traitement image {image_path.name}: {e}")
                        
            except Exception as e:
                print(f"   ❌ Erreur traitement bulletin {bulletin_pdf.name}: {e}")
        
        print(f"📚 Résultat: {len(notes_bulletins)} notes extraites au total des bulletins")
        return notes_bulletins
    
    def _convertir_pdf_en_images(self, pdfs: List[Path]) -> List[Path]:
        """Convertit les PDFs en images haute qualité pour OCR"""
        
        images_generees = []
        
        for pdf_path in pdfs:
            try:
                print(f"   🖼️ Conversion PDF → Images: {pdf_path.name}")
                
                doc = fitz.open(pdf_path)
                base_name = pdf_path.stem
                
                for i, page in enumerate(doc):
                    # Configuration optimale pour OCR
                    zoom = 300 / 72  # 300 DPI pour excellente qualité OCR
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    
                    image_path = self.dossier_images / f"{base_name}_page_{i+1:02d}.png"
                    pix.save(image_path)
                    images_generees.append(image_path)
                    print(f"      ✓ Image générée: {image_path.name}")
                
                doc.close()
                
            except Exception as e:
                print(f"   ❌ Erreur conversion {pdf_path.name}: {e}")
        
        return images_generees
    
    def _comparer_notes(self, notes_declarees: List[NoteDeclaree], notes_bulletins: List[NoteBulletin]) -> List[Discordance]:
        """Compare les notes déclarées avec les notes des bulletins"""
        
        print(f"⚖️ Comparaison de {len(notes_declarees)} notes déclarées avec {len(notes_bulletins)} notes de bulletins")
        discordances = []
        
        for note_dec in notes_declarees:
            # Chercher la note correspondante dans les bulletins
            note_correspondante = None
            
            for note_bul in notes_bulletins:
                if (self._matcher_matiere(note_dec.matiere, note_bul.matiere) and
                    self._matcher_periode(note_dec.periode, note_bul.periode) and
                    self._matcher_niveau(note_dec.niveau, note_bul.niveau)):
                    note_correspondante = note_bul
                    break
            
            if note_correspondante:
                ecart = abs(note_dec.note - note_correspondante.note)
                
                if ecart > self.seuil_leger:
                    # Déterminer la gravité
                    if ecart <= self.seuil_modere:
                        gravite = "MODERE"
                    else:
                        gravite = "GRAVE"
                    
                    discordance = Discordance(
                        matiere=note_dec.matiere,
                        periode=note_dec.periode,
                        niveau=note_dec.niveau,
                        note_declaree=note_dec.note,
                        note_bulletin=note_correspondante.note,
                        ecart=ecart,
                        gravite=gravite
                    )
                    discordances.append(discordance)
                    
                    symbole = "🔥" if gravite == "GRAVE" else "⚠️"
                    print(f"   {symbole} DISCORDANCE {gravite}: {note_dec.matiere} - Déclaré: {note_dec.note}/20, Réel: {note_correspondante.note}/20 (écart: {ecart:.2f})")
                else:
                    print(f"   ✅ Concordance: {note_dec.matiere} - {note_dec.note}/20 vs {note_correspondante.note}/20 (écart acceptable: {ecart:.2f})")
            else:
                print(f"   ❓ Note non trouvée dans bulletins: {note_dec.matiere} ({note_dec.periode}, {note_dec.niveau})")
        
        return discordances
    
    def _identifier_notes_non_verifiables(self, notes_declarees: List[NoteDeclaree], notes_bulletins: List[NoteBulletin]) -> List[str]:
        """Identifie les notes déclarées qui n'ont pas pu être vérifiées"""
        
        non_verifiables = []
        
        for note_dec in notes_declarees:
            trouve = False
            for note_bul in notes_bulletins:
                if (self._matcher_matiere(note_dec.matiere, note_bul.matiere) and
                    self._matcher_periode(note_dec.periode, note_bul.periode) and
                    self._matcher_niveau(note_dec.niveau, note_bul.niveau)):
                    trouve = True
                    break
            
            if not trouve:
                note_info = f"{note_dec.matiere} ({note_dec.periode}, {note_dec.niveau})"
                non_verifiables.append(note_info)
                print(f"   ⚠️ Note non vérifiable: {note_info}")
        
        return non_verifiables
    
    def _matcher_matiere(self, matiere1: str, matiere2: str) -> bool:
        """Vérifie si deux matières correspondent avec mapping intelligent"""
        
        # Normaliser
        m1 = matiere1.lower().strip()
        m2 = matiere2.lower().strip()
        
        # Correspondances exactes
        if m1 == m2:
            return True
        
        # Correspondances avec variations et synonymes
        correspondances = {
            "francais": ["français", "fran", "fr", "lettres"],
            "anglais": ["ang", "angl", "english", "lv1", "lve1"],
            "maths": ["mathématiques", "mathematiques", "math", "mathematique"],
            "histoire": ["hist", "histoire-geo", "histoire-géo", "histoire-géographie", "hg"],
            "svt": ["sciences", "biologie", "sciences-vie-terre", "sc-vie-terre"],
            "physique": ["physique-chimie", "phys", "pc", "sciences-physiques"],
            "chimie": ["physique-chimie", "chim", "pc"],
            "philosophie": ["philo", "phil"],
            "eps": ["sport", "education-physique", "éducation-physique"],
            "espagnol": ["esp", "lv2", "lve2"],
            "allemand": ["all", "lv2", "lve2"]
        }
        
        for base, variations in correspondances.items():
            if (m1 == base and m2 in variations) or (m2 == base and m1 in variations):
                return True
            # Vérifier les variations entre elles
            if m1 in variations and m2 in variations:
                return True
        
        return False
    
    def _matcher_periode(self, periode1: str, periode2: str) -> bool:
        """Vérifie si deux périodes correspondent"""
        
        p1 = periode1.lower().strip()
        p2 = periode2.lower().strip()
        
        # Extraire le numéro de trimestre
        num1 = re.search(r'(\d+)', p1)
        num2 = re.search(r'(\d+)', p2)
        
        if num1 and num2:
            return num1.group(1) == num2.group(1)
        
        # Correspondances textuelles
        if p1 == p2:
            return True
        
        # Mappings alternatifs
        mappings = {
            "1": ["premier", "1er", "first"],
            "2": ["deuxième", "2ème", "second", "2e"],
            "3": ["troisième", "3ème", "third", "3e"]
        }
        
        for num, variations in mappings.items():
            if (num in p1 and any(var in p2 for var in variations)) or \
               (num in p2 and any(var in p1 for var in variations)):
                return True
        
        return False
    
    def _matcher_niveau(self, niveau1: str, niveau2: str) -> bool:
        """Vérifie si deux niveaux correspondent"""
        
        n1 = niveau1.lower().strip()
        n2 = niveau2.lower().strip()
        
        correspondances = {
            "2nde": ["seconde", "2nd", "seconde générale"],
            "1ere": ["1ère", "premiere", "première", "première générale"],
            "terminale": ["tle", "term", "terminale générale"]
        }
        
        if n1 == n2:
            return True
        
        for base, variations in correspondances.items():
            if (n1 == base and n2 in variations) or (n2 == base and n1 in variations):
                return True
            # Vérifier variations entre elles
            if n1 in variations and n2 in variations:
                return True
        
        return False
    
    def _calculer_moyenne_reelle(self, notes_bulletins: List[NoteBulletin]) -> Optional[float]:
        """Calcule la moyenne réelle à partir des bulletins"""
        
        if not notes_bulletins:
            return None
        
        total_notes = sum(note.note for note in notes_bulletins)
        moyenne = total_notes / len(notes_bulletins)
        
        print(f"📊 Moyenne réelle calculée: {moyenne:.2f}/20 (basée sur {len(notes_bulletins)} notes)")
        return round(moyenne, 2)
    
    def _generer_rapport_excel(self, resultat: ResultatVerification) -> Path:
        """Génère le rapport Excel de vérification avec formatage professionnel"""
        
        print("📊 Génération du rapport Excel...")
        
        # Feuille 1: Résumé exécutif
        df_resume = pd.DataFrame([{
            "Candidat": f"{resultat.candidat_prenom} {resultat.candidat_nom}",
            "Moyenne Déclarée": resultat.moyenne_declaree,
            "Moyenne Réelle": resultat.moyenne_reelle or "N/A",
            "Écart Moyenne": f"{(resultat.moyenne_declaree - (resultat.moyenne_reelle or 0)):.2f}" if resultat.moyenne_reelle else "N/A",
            "Concordance Globale": "✅ HONNÊTE" if resultat.concordance_globale else "❌ MALHONNÊTE",
            "Nb Discordances": len(resultat.discordances),
            "Nb Notes Non Vérifiables": len(resultat.notes_non_verifiables),
            "Date Vérification": datetime.now().strftime('%d/%m/%Y à %H:%M'),
            "Statut Final": "VALIDÉ" if resultat.concordance_globale else "À EXAMINER"
        }])
        
        # Feuille 2: Discordances détaillées
        if resultat.discordances:
            df_discordances = pd.DataFrame([{
                "N°": i+1,
                "Matière": d.matiere.upper(),
                "Période": d.periode,
                "Niveau": d.niveau,
                "Note Déclarée": d.note_declaree,
                "Note Bulletin": d.note_bulletin,
                "Écart": f"{d.ecart:.2f}",
                "Écart %": f"{(d.ecart/20)*100:.1f}%",
                "Gravité": d.gravite,
                "Impact": "MENSONGE GRAVE" if d.gravite == "GRAVE" else "ÉCART SUSPECT",
                "Action Recommandée": "REJET CANDIDATURE" if d.gravite == "GRAVE" else "VÉRIFICATION MANUELLE"
            } for i, d in enumerate(resultat.discordances)])
        else:
            df_discordances = pd.DataFrame([{
                "Message": "✅ Aucune discordance détectée - Candidat honnête",
                "Détail": "Toutes les notes déclarées correspondent aux bulletins officiels"
            }])
        
        # Feuille 3: Notes non vérifiables
        if resultat.notes_non_verifiables:
            df_non_verifiables = pd.DataFrame([{
                "N°": i+1,
                "Note Non Vérifiable": note,
                "Raison": "Aucun bulletin correspondant trouvé",
                "Action": "Demander justificatif supplémentaire"
            } for i, note in enumerate(resultat.notes_non_verifiables)])
        else:
            df_non_verifiables = pd.DataFrame([{
                "Message": "✅ Toutes les notes ont été vérifiées avec succès",
                "Détail": "Correspondance parfaite entre déclarations et bulletins"
            }])
        
        # Nom de fichier avec horodatage
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nom_candidat = f"{resultat.candidat_nom}_{resultat.candidat_prenom}".replace(" ", "_")
        if nom_candidat == "INCONNU_INCONNU":
            nom_candidat = "CANDIDAT"
        
        fichier_excel = self.dossier_candidature / f"VERIFICATION_BULLETINS_{nom_candidat}_{timestamp}.xlsx"
        
        # Sauvegarde avec formatage Excel
        try:
            with pd.ExcelWriter(fichier_excel, engine='openpyxl') as writer:
                df_resume.to_excel(writer, sheet_name='📊 Résumé', index=False)
                df_discordances.to_excel(writer, sheet_name='🚨 Discordances', index=False)
                df_non_verifiables.to_excel(writer, sheet_name='⚠️ Non Vérifiables', index=False)
                
                # Formatage basique des colonnes
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"✅ Rapport Excel généré: {fichier_excel}")
            
        except Exception as e:
            print(f"❌ Erreur génération Excel: {e}")
            # Fallback: sauvegarde CSV
            fichier_csv = self.dossier_candidature / f"VERIFICATION_BULLETINS_{nom_candidat}_{timestamp}.csv"
            df_resume.to_csv(fichier_csv, index=False, encoding='utf-8')
            print(f"⚠️ Fallback: rapport CSV généré: {fichier_csv}")
            return fichier_csv
        
        return fichier_excel
    
    def _sauvegarder_resultat_json(self, resultat: ResultatVerification):
        """Sauvegarde le résultat en JSON pour intégration système"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = self.dossier_candidature / f"verification_bulletins_{timestamp}.json"
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(resultat.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"✅ Résultat JSON sauvegardé: {json_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")

# ==================================================
# FONCTIONS UTILITAIRES POUR INTÉGRATION ADMIN
# ==================================================

def verifier_bulletins_scolaires(dossier_path: str) -> ResultatVerification:
    """
    Fonction principale pour vérifier les bulletins scolaires
    Compatible avec votre interface Streamlit
    
    Args:
        dossier_path: Chemin vers le dossier candidature
        
    Returns:
        ResultatVerification: Résultat complet de la vérification
    """
    try:
        agent = AgentVerificationScolaireAdmin(dossier_path)
        return agent.verifier_candidature_complete()
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE dans verifier_bulletins_scolaires: {e}")
        # Retour d'erreur robuste
        return ResultatVerification(
            candidat_nom="ERREUR",
            candidat_prenom="SYSTÈME",
            moyenne_declaree=0.0,
            moyenne_reelle=None,
            concordance_globale=False,
            discordances=[],
            notes_non_verifiables=[f"Erreur système: {str(e)}"],
            timestamp=datetime.now().isoformat()
        )

def get_verification_status(dossier_candidature: Path) -> dict:
    """Obtient le statut de vérification d'une candidature"""
    
    try:
        # Chercher les rapports existants
        rapports_excel = list(dossier_candidature.glob("VERIFICATION_BULLETINS_*.xlsx"))
        rapports_json = list(dossier_candidature.glob("verification_bulletins_*.json"))
        
        if rapports_json:
            # Lire le dernier rapport JSON
            dernier_rapport = max(rapports_json, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(dernier_rapport, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return {
                    "verifie": True,
                    "date_verification": data.get("timestamp"),
                    "concordance": data.get("concordance_globale"),
                    "nb_discordances": len(data.get("discordances", [])),
                    "rapport_excel": data.get("rapport_excel_path"),
                    "rapport_json": str(dernier_rapport)
                }
            except Exception as e:
                print(f"❌ Erreur lecture rapport JSON: {e}")
        
        # Fallback: chercher seulement les rapports Excel
        if rapports_excel:
            dernier_excel = max(rapports_excel, key=lambda x: x.stat().st_mtime)
            return {
                "verifie": True,
                "date_verification": datetime.fromtimestamp(dernier_excel.stat().st_mtime).isoformat(),
                "concordance": None,  # Pas d'info sans JSON
                "nb_discordances": 0,
                "rapport_excel": str(dernier_excel),
                "rapport_json": None
            }
        
        return {
            "verifie": False,
            "date_verification": None,
            "concordance": None,
            "nb_discordances": 0,
            "rapport_excel": None,
            "rapport_json": None
        }
    
    except Exception as e:
        print(f"❌ Erreur get_verification_status: {e}")
        return {
            "verifie": False,
            "date_verification": None,
            "concordance": None,
            "nb_discordances": 0,
            "rapport_excel": None,
            "rapport_json": None
        }

def detecter_bulletins_scolaires(dossier_candidature: Path) -> dict:
    """Détecte la présence de bulletins scolaires dans une candidature"""
    
    try:
        pdfs = list(dossier_candidature.glob("*.pdf"))
        
        bulletins = []
        formulaire = None
        
        # Patterns de détection améliorés
        patterns_bulletins = ["bulletin", "2nde", "1ere", "1ère", "terminale", "tle", "seconde", "premiere"]
        patterns_formulaire = ["candidature", "formulaire", "dossier", "cand_"]
        
        for pdf in pdfs:
            nom = pdf.name.lower()
            
            # Détecter les bulletins
            if any(pattern in nom for pattern in patterns_bulletins):
                bulletins.append(pdf.name)
            # Détecter le formulaire
            elif any(pattern in nom for pattern in patterns_formulaire):
                formulaire = pdf.name
        
        # Si pas de formulaire détecté, prendre le premier PDF qui n'est pas un bulletin
        if not formulaire:
            for pdf in pdfs:
                nom = pdf.name.lower()
                if not any(pattern in nom for pattern in patterns_bulletins):
                    formulaire = pdf.name
                    break
        
        return {
            "bulletins_detectes": len(bulletins) > 0,
            "nb_bulletins": len(bulletins),
            "liste_bulletins": bulletins,
            "formulaire_detecte": formulaire is not None,
            "formulaire": formulaire,
            "verifiable": formulaire is not None and len(bulletins) > 0
        }
    
    except Exception as e:
        print(f"❌ Erreur detecter_bulletins_scolaires: {e}")
        return {
            "bulletins_detectes": False,
            "nb_bulletins": 0,
            "liste_bulletins": [],
            "formulaire_detecte": False,
            "formulaire": None,
            "verifiable": False
        }

