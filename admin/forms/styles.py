"""
Styles CSS pour l'application Streamlit
"""

import streamlit as st


def apply_custom_styles():
    """Applique les styles CSS personnalisés"""
    st.markdown("""
    <style>
        /* En-tête principal */
        .main-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        }
        
        .main-header h1 {
            margin-bottom: 0.5rem;
            font-weight: 300;
        }
        
        .main-header p {
            margin-bottom: 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        /* En-têtes de section */
        .section-header {
            background: #f8f9fa;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #4facfe;
            margin: 2rem 0 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .section-header h2 {
            margin: 0;
            color: #333;
            font-size: 1.3rem;
        }
        
        /* Alertes */
        .alert-info {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border-left: 4px solid #17a2b8;
        }
        
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border-left: 4px solid #28a745;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border-left: 4px solid #ffc107;
        }
        
        /* Cartes de statistiques */
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #4facfe;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4facfe;
            margin-bottom: 0.5rem;
            line-height: 1;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9rem;
            margin: 0;
        }
        
        /* Barre de progression */
        .progress-text {
            text-align: center;
            font-weight: bold;
            margin: 1rem 0;
            color: #333;
            font-size: 1.1rem;
        }
        
        /* Tableau des notes */
        .grades-table {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Améliorations générales */
        .stButton > button {
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        /* Bouton principal */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        /* Upload de fichiers */
        .uploadedFile {
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem;
            margin: 0.25rem 0;
            background: #f8f9fa;
        }
        
        /* Colonnes équilibrées */
        .element-container {
            margin-bottom: 0.5rem;
        }
        
        /* Messages d'information */
        .stInfo {
            border-radius: 6px;
        }
        
        .stSuccess {
            border-radius: 6px;
        }
        
        .stWarning {
            border-radius: 6px;
        }
        
        .stError {
            border-radius: 6px;
        }
        
        /* Masquer les éléments Streamlit par défaut */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Espacement des sections */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Style pour les métriques */
        [data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #4facfe;
        }
        
        /* Style pour les dataframes */
        .stDataFrame {
            border-radius: 6px;
            overflow: hidden;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-header {
                padding: 1.5rem 1rem;
            }
            
            .main-header h1 {
                font-size: 1.8rem;
            }
            
            .stat-value {
                font-size: 2rem;
            }
            
            .section-header {
                padding: 0.8rem 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)