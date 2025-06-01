"""
Système d'authentification pour l'interface d'administration
"""

import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
from admin_config import USER_ROLES


# Configuration des utilisateurs (en production, utiliser une base de données)
ADMIN_USERS = {
    "admin": {
        "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # "admin"
        "role": "admin",
        "name": "Administrateur",
        "email": "admin@etablissement.fr",
        "created_date": "2024-01-01",
        "last_login": None,
        "active": True
    },
    "prof_martin": {
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # "secret123"
        "role": "examiner",
        "name": "Prof. Martin",
        "email": "martin@etablissement.fr",
        "created_date": "2024-01-15",
        "last_login": None,
        "active": True
    },
    "secretaire": {
        "password_hash": "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0",  # "viewer123"
        "role": "viewer",
        "name": "Secrétariat",
        "email": "secretariat@etablissement.fr",
        "created_date": "2024-02-01",
        "last_login": None,
        "active": True
    }
}


def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return hash_password(password) == password_hash


def load_users() -> Dict:
    """Charge les utilisateurs depuis un fichier JSON (si il existe)"""
    users_file = "admin_users.json"
    
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur lors du chargement des utilisateurs : {str(e)}")
    
    # Retourner les utilisateurs par défaut si le fichier n'existe pas
    return ADMIN_USERS


def save_users(users: Dict):
    """Sauvegarde les utilisateurs dans un fichier JSON"""
    users_file = "admin_users.json"
    
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des utilisateurs : {str(e)}")


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authentifie un utilisateur"""
    users = load_users()
    
    if username in users:
        user = users[username]
        
        if not user.get('active', True):
            return None
        
        if verify_password(password, user['password_hash']):
            # Mettre à jour la dernière connexion
            user['last_login'] = datetime.now().isoformat()
            users[username] = user
            save_users(users)
            
            return {
                'username': username,
                'role': user['role'],
                'name': user['name'],
                'email': user['email'],
                'permissions': USER_ROLES.get(user['role'], {}).get('permissions', [])
            }
    
    return None


def check_permission(permission: str) -> bool:
    """Vérifie si l'utilisateur connecté a une permission spécifique"""
    if 'admin_user' not in st.session_state:
        return False
    
    user_permissions = st.session_state.admin_user.get('permissions', [])
    return permission in user_permissions


def require_permission(permission: str):
    """Décorateur pour exiger une permission spécifique"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_permission(permission):
                st.error(f"🚫 Accès refusé. Permission requise : {permission}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_authentication():
    """Vérifie que l'utilisateur est authentifié"""
    if 'admin_user' not in st.session_state or not st.session_state.admin_user:
        show_login_form()
        st.stop()


def show_login_form():
    """Affiche le formulaire de connexion"""
    st.markdown("""
    <div style="max-width: 400px; margin: 50px auto; padding: 30px; 
                background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Connexion Administration")
    st.markdown("Veuillez vous connecter pour accéder à l'interface d'administration.")
    
    with st.form("login_form"):
        username = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_button = st.form_submit_button("🚪 Se connecter", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❓ Aide", use_container_width=True):
                show_help_info()
    
    if login_button:
        if username and password:
            user = authenticate_user(username, password)
            
            if user:
                st.session_state.admin_user = user
                st.session_state.login_time = datetime.now()
                
                st.success(f"✅ Connexion réussie ! Bienvenue {user['name']}")
                st.balloons()
                
                # Log de connexion
                log_user_action(username, "login", "Connexion réussie")
                
                st.rerun()
            else:
                st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
                
                # Log de tentative échouée
                log_user_action(username, "failed_login", "Tentative de connexion échouée")
        else:
            st.warning("⚠️ Veuillez remplir tous les champs")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Informations de connexion par défaut (à supprimer en production)
    with st.expander("🔧 Comptes de démonstration", expanded=False):
        st.markdown("""
        **Administrateur :**
        - Utilisateur : `admin`
        - Mot de passe : `admin`
        
        **Examinateur :**
        - Utilisateur : `prof_martin`
        - Mot de passe : `secret123`
        
        **Visualiseur :**
        - Utilisateur : `secretaire`
        - Mot de passe : `viewer123`
        """)


def show_help_info():
    """Affiche les informations d'aide"""
    st.info("""
    **Aide à la connexion :**
    
    🔑 **Problème de mot de passe ?**
    Contactez l'administrateur système pour réinitialiser votre mot de passe.
    
    👤 **Nouveau utilisateur ?**
    Demandez la création d'un compte à l'administrateur.
    
    📧 **Contact :** admin@etablissement.fr
    📞 **Téléphone :** 01 23 45 67 89
    """)


def show_user_info():
    """Affiche les informations de l'utilisateur connecté"""
    if 'admin_user' not in st.session_state:
        return
    
    user = st.session_state.admin_user
    login_time = st.session_state.get('login_time', datetime.now())
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Utilisateur connecté")
        
        st.markdown(f"**Nom :** {user['name']}")
        st.markdown(f"**Rôle :** {USER_ROLES.get(user['role'], {}).get('name', user['role'])}")
        st.markdown(f"**Email :** {user['email']}")
        st.markdown(f"**Connecté depuis :** {login_time.strftime('%H:%M')}")
        
        # Session timeout (optionnel)
        session_duration = datetime.now() - login_time
        if session_duration > timedelta(hours=8):
            st.warning("⏰ Session expirée")
            if st.button("🔄 Renouveler la session"):
                st.session_state.login_time = datetime.now()
                st.rerun()
        
        if st.button("🚪 Se déconnecter", type="secondary", use_container_width=True):
            logout_user()


def logout_user():
    """Déconnecte l'utilisateur"""
    if 'admin_user' in st.session_state:
        username = st.session_state.admin_user.get('username', 'Unknown')
        
        # Log de déconnexion
        log_user_action(username, "logout", "Déconnexion")
        
        # Nettoyer la session
        del st.session_state.admin_user
        if 'login_time' in st.session_state:
            del st.session_state.login_time
        
        st.success("👋 Déconnexion réussie")
        st.rerun()


def log_user_action(username: str, action: str, details: str = ""):
    """Log des actions utilisateur"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'action': action,
        'details': details,
        'ip_address': 'localhost'  # En production, récupérer la vraie IP
    }
    
    # Sauvegarder dans un fichier de log
    log_file = "admin_logs.json"
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        # Garder seulement les 1000 derniers logs
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        # Ne pas faire planter l'app si le log échoue
        print(f"Erreur lors de l'écriture du log : {str(e)}")


def create_user(username: str, password: str, role: str, name: str, email: str) -> bool:
    """Crée un nouvel utilisateur (admin seulement)"""
    if not check_permission("manage_users"):
        return False
    
    users = load_users()
    
    if username in users:
        return False  # Utilisateur existe déjà
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "name": name,
        "email": email,
        "created_date": datetime.now().isoformat(),
        "last_login": None,
        "active": True
    }
    
    save_users(users)
    log_user_action(st.session_state.admin_user['username'], "create_user", f"Utilisateur créé : {username}")
    
    return True


def update_user_password(username: str, new_password: str) -> bool:
    """Met à jour le mot de passe d'un utilisateur"""
    if not check_permission("manage_users") and st.session_state.admin_user['username'] != username:
        return False
    
    users = load_users()
    
    if username not in users:
        return False
    
    users[username]['password_hash'] = hash_password(new_password)
    save_users(users)
    
    log_user_action(st.session_state.admin_user['username'], "password_change", f"Mot de passe modifié pour : {username}")
    
    return True


def deactivate_user(username: str) -> bool:
    """Désactive un utilisateur"""
    if not check_permission("manage_users"):
        return False
    
    users = load_users()
    
    if username not in users:
        return False
    
    users[username]['active'] = False
    save_users(users)
    
    log_user_action(st.session_state.admin_user['username'], "deactivate_user", f"Utilisateur désactivé : {username}")
    
    return True


def get_user_logs(username: str = None, limit: int = 100) -> List[Dict]:
    """Récupère les logs d'un utilisateur"""
    if not check_permission("view_all"):
        return []
    
    log_file = "admin_logs.json"
    
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        if username:
            logs = [log for log in logs if log.get('username') == username]
        
        # Retourner les plus récents en premier
        logs.reverse()
        
        return logs[:limit]
        
    except Exception as e:
        print(f"Erreur lors de la lecture des logs : {str(e)}")
        return []


def show_user_management():
    """Interface de gestion des utilisateurs (admin seulement)"""
    if not check_permission("manage_users"):
        st.error("🚫 Accès refusé. Vous n'avez pas les permissions pour gérer les utilisateurs.")
        return
    
    st.subheader("👥 Gestion des Utilisateurs")
    
    users = load_users()
    
    # Affichage des utilisateurs existants
    st.markdown("### Utilisateurs existants")
    
    for username, user_data in users.items():
        with st.expander(f"👤 {user_data['name']} ({username})", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Rôle :** {user_data['role']}")
                st.markdown(f"**Email :** {user_data['email']}")
            
            with col2:
                st.markdown(f"**Créé le :** {user_data['created_date'][:10]}")
                st.markdown(f"**Dernière connexion :** {user_data.get('last_login', 'Jamais')[:16] if user_data.get('last_login') else 'Jamais'}")
            
            with col3:
                status = "🟢 Actif" if user_data.get('active', True) else "🔴 Inactif"
                st.markdown(f"**Statut :** {status}")
                
                if user_data.get('active', True) and username != st.session_state.admin_user['username']:
                    if st.button(f"❌ Désactiver {username}", key=f"deactivate_{username}"):
                        if deactivate_user(username):
                            st.success(f"Utilisateur {username} désactivé")
                            st.rerun()
    
    # Création d'un nouvel utilisateur
    st.markdown("---")
    st.markdown("### Créer un nouvel utilisateur")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Nom d'utilisateur")
            new_name = st.text_input("Nom complet")
        
        with col2:
            new_email = st.text_input("Email")
            new_role = st.selectbox("Rôle", list(USER_ROLES.keys()))
        
        new_password = st.text_input("Mot de passe temporaire", type="password")
        
        if st.form_submit_button("➕ Créer l'utilisateur", type="primary"):
            if new_username and new_name and new_email and new_password:
                if create_user(new_username, new_password, new_role, new_name, new_email):
                    st.success(f"✅ Utilisateur {new_username} créé avec succès")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la création (utilisateur existe déjà ?)")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs")


def show_activity_logs():
    """Affiche les logs d'activité"""
    if not check_permission("view_all"):
        st.error("🚫 Accès refusé.")
        return
    
    st.subheader("📋 Logs d'Activité")
    
    # Filtres
    col1, col2 = st.columns(2)
    
    with col1:
        username_filter = st.selectbox("Filtrer par utilisateur", ["Tous"] + list(load_users().keys()))
    
    with col2:
        limit = st.selectbox("Nombre d'entrées", [50, 100, 200, 500], index=1)
    
    # Récupérer les logs
    logs = get_user_logs(
        username=None if username_filter == "Tous" else username_filter,
        limit=limit
    )
    
    if logs:
        # Convertir en DataFrame pour affichage
        df_logs = pd.DataFrame(logs)
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Renommer les colonnes
        df_logs = df_logs.rename(columns={
            'timestamp': 'Date/Heure',
            'username': 'Utilisateur',
            'action': 'Action',
            'details': 'Détails'
        })
        
        st.dataframe(df_logs[['Date/Heure', 'Utilisateur', 'Action', 'Détails']], use_container_width=True)
    else:
        st.info("Aucun log trouvé")