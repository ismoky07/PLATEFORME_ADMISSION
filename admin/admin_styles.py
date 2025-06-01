"""
Styles CSS pour l'interface d'administration
"""

import streamlit as st


def apply_admin_styles():
    """Applique les styles CSS spécifiques à l'administration"""
    st.markdown("""
    <style>
        /* En-tête administration */
        .admin-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .admin-header h1 {
            margin-bottom: 0.5rem;
            font-weight: 300;
            font-size: 2.2rem;
        }
        
        .admin-header p {
            margin-bottom: 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        /* Sidebar améliorée */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Métriques administratives */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        [data-testid="metric-container"] > div {
            color: #495057;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            color: #667eea;
            font-weight: bold;
        }
        
        /* Statuts de candidature */
        .status-en_attente {
            background-color: #fff3cd;
            color: #856404;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-validee {
            background-color: #d4edda;
            color: #155724;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-rejetee {
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-en_cours {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-anomalie {
            background-color: #e2e3f3;
            color: #383d41;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        /* Onglets de navigation */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
            background-color: #f8f9fa;
            border-radius: 8px 8px 0 0;
            border: 1px solid #dee2e6;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        /* Tableaux de données */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .stDataFrame table {
            font-size: 0.9rem;
        }
        
        .stDataFrame th {
            background-color: #667eea;
            color: white;
            font-weight: 600;
            text-align: center;
        }
        
        .stDataFrame td {
            text-align: center;
        }
        
        /* Boutons d'action */
        .stButton > button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Bouton de validation */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        /* Boutons d'action secondaires */
        .stButton > button[data-testid*="examine"] {
            background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
            color: white;
        }
        
        .stButton > button[data-testid*="validate"] {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .stButton > button[data-testid*="reject"] {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
        }
        
        .stButton > button[data-testid*="export"] {
            background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
            color: #212529;
        }
        
        /* Alertes et messages */
        .stAlert {
            border-radius: 8px;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stSuccess {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left: 4px solid #28a745;
        }
        
        .stError {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-left: 4px solid #dc3545;
        }
        
        .stWarning {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border-left: 4px solid #ffc107;
        }
        
        .stInfo {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border-left: 4px solid #17a2b8;
        }
        
        /* Expandeurs pour anomalies */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-weight: 600;
        }
        
        .streamlit-expanderContent {
            background-color: white;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 8px 8px;
        }
        
        /* Sélecteurs et inputs */
        .stSelectbox > div > div {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            color: #212529;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #667eea;
            background-color: white;
        }
        
        .stSelectbox label {
            color: #495057;
            font-weight: 500;
        }
        
        .stTextInput > div > div > input {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            color: #212529;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            background-color: white;
        }
        
        .stTextInput label {
            color: #495057;
            font-weight: 500;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            color: #212529;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            background-color: white;
        }
        
        .stTextArea label {
            color: #495057;
            font-weight: 500;
        }
        
        /* Sliders */
        .stSlider > div > div > div > div {
            background-color: #667eea;
        }
        
        /* Indicateurs de progression */
        .stProgress .st-bo {
            background-color: #e9ecef;
        }
        
        .stProgress .st-bp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Cartes de contenu */
        .content-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
            margin-bottom: 1rem;
        }
        
        /* Badges de confiance OCR */
        .confidence-high {
            background-color: #d4edda;
            color: #155724;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .confidence-medium {
            background-color: #fff3cd;
            color: #856404;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .confidence-low {
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        /* Masquer éléments Streamlit par défaut */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Espacement amélioré */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .admin-header {
                padding: 1.5rem 1rem;
            }
            
            .admin-header h1 {
                font-size: 1.8rem;
            }
            
            [data-testid="metric-container"] {
                padding: 0.8rem;
            }
            
            .stButton > button {
                width: 100%;
                margin-bottom: 0.5rem;
            }
        }
        
        /* Animation pour les éléments interactifs */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .content-card {
            animation: fadeIn 0.3s ease-out;
        }
        
        /* Amélioration des multiselect */
        .stMultiSelect > div > div {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            color: #212529;
        }
        
        .stMultiSelect > div > div:focus-within {
            border-color: #667eea;
            background-color: white;
        }
        
        .stMultiSelect label {
            color: #495057;
            font-weight: 500;
        }
        
        /* Style pour les options sélectionnées dans multiselect */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #667eea;
            color: white;
        }
        
        /* Style pour le texte des placeholders */
        .stSelectbox input::placeholder,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #6c757d;
        }
        
        /* Style pour les valeurs sélectionnées */
        .stSelectbox [data-baseweb="select"] > div {
            color: #212529;
        }
        
        /* Style pour les graphiques */
        .stPlotlyChart {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            background: white;
            padding: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)