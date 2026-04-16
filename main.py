from os import path

import streamlit as st
import json
import os
import requests
import pandas as pd
import glob

import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# --- FONCTION DE FUSION DES CSV ---
def get_network_mapping(directory='./dump_tcplife'):
    csv_files = glob.glob(os.path.join(directory, "*.log"))
    if not csv_files: return {}
    
    try:
        # Fusion rapide
        df_tcp = pd.concat([pd.read_csv(f, skipinitialspace=True) for f in csv_files], ignore_index=True)
        
        # Nettoyage : On vire les espaces, on force en entier (Int64 gère les NaN sans passer en float)
        df_tcp['RADDR'] = df_tcp['RADDR'].astype(str).str.strip()
        df_tcp['RPORT'] = pd.to_numeric(df_tcp['RPORT'], errors='coerce').astype('Int64')
        
        # On groupe et on transforme en chaîne sans les .0
        return df_tcp.dropna(subset=['RPORT']).groupby('RADDR')['RPORT'].unique().apply(
            lambda x: ", ".join(map(str, sorted(x)))
        ).to_dict()
    except:
        return {}

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Thruk Audit Cockpit", page_icon="🥊")

# --- 2. FONCTIONS DE CHARGEMENT ET CACHE ---
@st.cache_data
def load_config(config_path="./config/thruk_config.json"):
    if not os.path.exists(config_path): return {}
    with open(config_path, "r") as f: return json.load(f)

@st.cache_data
def load_query_config(query_config_path="./config/thruk_query.json"):
    if not os.path.exists(query_config_path): return {}
    with open(query_config_path, "r") as f: return json.load(f)

@st.cache_data(show_spinner="Appel API Thruk...")
def get_thruk_data(thruk_conf, endpoint):
    query_conf = load_query_config()
    cols = query_conf.get(endpoint, {}).get("columns", [])
    base_url = thruk_conf["url"].rstrip("/") + f"/{endpoint}"
    params = {"columns": ",".join(cols)}
    headers = {"X-Thruk-Auth-Key": thruk_conf['apikey'], "X-Thruk-Auth-User": thruk_conf['user']}
    try:
        resp = requests.get(base_url, headers=headers, params=params, timeout=15, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Erreur sur {endpoint} : {e}")
        return []

def main():
    # --- 3. INJECTION CSS (Anti-blocage Scroll) ---
    st.session_state["tcplife_data"] = st.session_state.get("tcplife_data", {})
    st.markdown("""
        <style>
        .main .block-container { max-width: 95%; padding-top: 1rem; }
        section.main { overflow-y: auto !important; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-thumb { background: #cccccc; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    config = load_config()
    if not config:
        st.error("Fichier de configuration introuvable.")
        st.stop()

    thruks = list(config.keys())
    
    with st.sidebar:
        st.header("⚙️ Paramètres")
        if st.button("🧹 Vider le cache", width='stretch'):
            st.cache_data.clear()
            st.rerun()

        if st.button("🔄 Recharger les données TCPLife", width='stretch'):
            current_net_map = get_network_mapping()
            if current_net_map is not None:
                st.session_state["tcplife_data"] = current_net_map
                st.success("Données TCPLife rechargées et fusionnées avec succès.")
            else:
                st.warning("Aucun fichier CSV trouvé dans le répertoire TCPLife.")

        t1 = st.selectbox("Instance SOURCE (Référence)", thruks, index=0)
        t2 = st.selectbox("Instance CIBLE", [t for t in thruks if t != t1], index=0)
        btn_compare = st.button("🚀 Lancer l'Audit", type="primary", width='stretch')
        

    if btn_compare or "results_ready" in st.session_state:
        st.session_state["results_ready"] = True
        
        # --- 4. PLACEHOLDER POUR LE COCKPIT GLOBAL ---
        cockpit_container = st.empty() 

        endpoints = load_query_config().keys()
        
        # Dictionnaires pour stocker les scores finaux
        summary = {ep: {"abs": 0, "trop": 0, "diff": 0} for ep in endpoints}

        for ep in endpoints:
            with st.expander(f"📦 ANALYSE DES {ep.upper()}", expanded=False):
                
                # Fetch data
                raw1 = get_thruk_data(config[t1], ep)
                raw2 = get_thruk_data(config[t2], ep)
                df1, df2 = pd.DataFrame(raw1), pd.DataFrame(raw2)

                if df1.empty and df2.empty:
                    st.warning(f"Données vides pour {ep}")
                    continue

                # Identifiant Unique (UID)
                if ep == "services":
                    df1['uid'] = df1['host_name'] + " / " + df1['description']
                    df2['uid'] = df2['host_name'] + " / " + df2['description']
                    display_cols = ["uid", "state", "plugin_output"]
                else:
                    df1['uid'] = df1['name']
                    df2['uid'] = df2['name']
                    display_cols = ["uid", "state", "address"] if "address" in df1.columns else ["uid"]

                # Logique Sets
                set1, set2 = set(df1['uid']), set(df2['uid'])
                absents = set1 - set2
                en_trop = set2 - set1
                communs = set1 & set2

                # Mise à jour du résumé pour le Cockpit
                summary[ep]["abs"] = len(absents)
                summary[ep]["trop"] = len(en_trop)

                # --- UI LOCALE : INDICATEURS ---
                with st.container(border=True):
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    c_m1.metric("Source", len(set1))
                    c_m2.metric("Cible", len(set2))
                    c_m3.metric("🔴 Absents", len(absents), delta=len(absents), delta_color="inverse")
                    c_m4.metric("🟠 En trop", len(en_trop), delta=len(en_trop), delta_color="off")
                    
                    only_diff = st.checkbox(f"Afficher uniquement les anomalies ({ep})", key=f"chk_{ep}")

                # Filtrage tableaux
                to_show1 = df1[df1['uid'].isin(absents)] if only_diff else df1
                to_show2 = df2[df2['uid'].isin(en_trop)] if only_diff else df2

                # Affichage Tableaux
                t_col1, t_col2 = st.columns(2)
                df_cfg = {"uid": st.column_config.TextColumn("Identifiant", width="large")}
                with t_col1:
                    st.caption(f"📍 {t1}")
                    st.dataframe(to_show1, column_order=display_cols, column_config=df_cfg, width='stretch', hide_index=True)
                with t_col2:
                    st.caption(f"🎯 {t2}")
                    st.dataframe(to_show2, column_order=display_cols, column_config=df_cfg, width='stretch', hide_index=True)

            # --- ANALYSE ÉTATS (SANTÉ) ENRICHIE ---
            if ep == "services" and communs:
                with st.expander(f"🚦 ÉCARTS D'ÉTATS & FLUX : {ep.upper()}", expanded=False):
                    df_c1 = df1[df1['uid'].isin(communs)].copy()
                    df_c2 = df2[df2['uid'].isin(communs)].copy()
                    
                    # 1. Identification de la colonne d'IP (priorité à host_address)
                    col_ip = next((c for c in ['host_address', 'address'] if c in df_c1.columns), None)
                    
                    # 2. Initialisation forcée de la colonne de flux pour éviter le KeyError
                    net_map = st.session_state.get("tcplife_data", {})
                    df_c1['flux_réels'] = "IP manquante"
                    
                    # 3. Mapping si l'IP est trouvée dans les colonnes Thruk
                    if col_ip:
                        df_c1['flux_réels'] = df_c1[col_ip].map(net_map).fillna("Aucun flux détecté")
                    else:
                        st.warning("⚠️ 'host_address' absent de l'API. Vérifiez thruk_query.json.")

                    # 4. Fusion (Merge) des instances Source et Cible
                    merge_cols = ['uid', 'state', 'flux_réels']
                    if col_ip: merge_cols.append(col_ip)
                    
                    comp_df = pd.merge(
                        df_c1[merge_cols], 
                        df_c2[['uid', 'state']], 
                        on='uid', 
                        suffixes=('_src', '_tgt')
                    )
                    
                    # Isolation des lignes où les états divergent
                    diff_df = comp_df[comp_df['state_src'] != comp_df['state_tgt']]
                    summary[ep]["diff"] = len(diff_df)

                    # 5. Affichage dynamique
                    final_display_cols = ["uid"]
                    if col_ip: final_display_cols.append(col_ip)
                    final_display_cols.extend(["state_src", "state_tgt", "flux_réels"])

                    st.dataframe(
                        diff_df, 
                        column_order=final_display_cols,
                        column_config={
                            "uid": "Service",
                            "host_address": "IP Host",
                            "address": "IP Host",
                            "state_src": f"État ({t1})",
                            "state_tgt": f"État ({t2})",
                            "flux_réels": "Ports (tcplife)"
                        },
                        width='stretch',  # Utilisation de ta convention pour container_width=True
                        hide_index=True
                    )



        # --- 5. REMPLISSAGE FINAL DU COCKPIT (Affiché en haut) ---
        with cockpit_container.container():
            st.header("📊 Cockpit Global d'Audit")
            # Bloc de synthèse
            with st.container(border=True):
                g1, g2, g3 = st.columns(3)
                
                total_abs = sum(v["abs"] for v in summary.values())
                total_trop = sum(v["trop"] for v in summary.values())
                total_diff = sum(v["diff"] for v in summary.values())
                
                g1.metric("🔴 TOTAL ABSENTS", total_abs)
                g2.metric("🟠 TOTAL EN TROP", total_trop)
                g3.metric("🟡 ÉCARTS ÉTATS", total_diff)

                # Petit tableau de synthèse propre
                summary_df = pd.DataFrame.from_dict(summary, orient='index')
                summary_df.columns = ["Absents (Manquants)", "En Trop (Surplus)", "Écarts États (Santé)"]
                st.table(summary_df)

if __name__ == "__main__":
    main()