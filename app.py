import streamlit as st
import psycopg2
from datetime import datetime

try:
    with get_pg_connection() as conn:
        st.success("✅ Connexion PostgreSQL réussie.")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
    st.stop()


st.set_page_config(page_title="Accueil - Suivi Navigabilité", layout="wide")

now = datetime.now().date()

# 📦 Connexion PostgreSQL via secrets.toml
def get_pg_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# 🔢 Compter les lignes dans une table PostgreSQL
def count_rows(query):
    with get_pg_connection() as conn:
        c = conn.cursor()
        c.execute(query)
        return c.fetchone()[0]

# ⚠️ Tâches de monitoring en retard
def count_monitoring_urgent():
    overdue = []
    with get_pg_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT engine_esn, category, description, due_date FROM condition_monitoring")
        rows = c.fetchall()
        for esn, cat, desc, date in rows:
            try:
                due = datetime.strptime(date, "%Y-%m-%d").date()
                if due < now:
                    overdue.append((esn, cat, desc, due))
            except:
                continue
    return overdue

# 🔁 Redirection helper
def redirect_to_visualiser(filter_key):
    st.query_params["filter"] = filter_key
    st.switch_page("pages/1_visualiser.py")

# 📋 Données de monitoring
overdue_tasks = count_monitoring_urgent()
nb_overdue = len(overdue_tasks)

# 🔔 Alerte en haut
cols_top = st.columns([0.9, 0.1])
with cols_top[1]:
    if nb_overdue:
        if st.button(f"🔔 {nb_overdue}", key="top_alert"):
            st.sidebar.subheader("📋 Tâches en retard")
            for i, (esn, cat, desc, date) in enumerate(overdue_tasks):
                st.sidebar.markdown(f"🔴 **{esn}** | {cat} → {desc} – 📆 {date}")
    else:
        st.button("🔔", key="top_alert_disabled")

# 🛫 Titre
st.title("🛫 Tableau de bord global - Moteurs & APU")
st.caption(f"📅 Date actuelle : {now}")

# Synthèse des 8 éléments suivis
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🔄 Engine Changes", count_rows("SELECT COUNT(*) FROM engine_changes"))
    if st.button("➡️ Voir", key="btn1"):
        redirect_to_visualiser("changes")

    st.metric("🏭 In-Shop", count_rows("SELECT COUNT(*) FROM shop_entries"))
    if st.button("➡️ Voir", key="btn2"):
        redirect_to_visualiser("shop")

    st.metric("📦 Spare Engines Records", count_rows("SELECT COUNT(*) FROM spare_engines"))
    if st.button("➡️ Voir", key="btn3"):
        redirect_to_visualiser("spare")

with col2:
    st.metric("🤝 Lease Engines Records", count_rows("SELECT COUNT(*) FROM lease_engines"))
    if st.button("➡️ Voir", key="btn4"):
        redirect_to_visualiser("lease")

    st.metric("👁️ On Watch", count_rows("SELECT COUNT(*) FROM on_watch"))
    if st.button("➡️ Voir", key="btn5"):
        redirect_to_visualiser("watch")

    st.metric("⚙️ Monitoring Entries", count_rows("SELECT COUNT(*) FROM condition_monitoring"))
    if st.button("➡️ Voir", key="btn8"):
        redirect_to_visualiser("monitoring")

with col3:
    st.metric("📄 Contrats & AO", count_rows("SELECT COUNT(*) FROM contracts_tasks"))
    if st.button("➡️ Voir", key="btn6"):
        redirect_to_visualiser("contracts")

    st.metric("✅ Autres tâches", count_rows("SELECT COUNT(*) FROM other_tasks"))
    if st.button("➡️ Voir", key="btn7"):
        redirect_to_visualiser("tasks")

st.markdown("---")
st.info("Utilise le menu à gauche pour visualiser ou modifier les données par moteur.")
