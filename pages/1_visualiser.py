
import streamlit as st
import psycopg2
from datetime import datetime

st.set_page_config(page_title="Visualiser", layout="wide")
st.title("🔍 Visualiser les moteurs selon filtre")
now = datetime.now().date()
st.caption(f"📅 Date actuelle : {now}")

# Connexion PostgreSQL
def get_pg_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# Charger modèles et ESNs
def load_options():
    with get_pg_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT model FROM engine_unit")
        models = [row[0] for row in c.fetchall()]
        c.execute("SELECT DISTINCT esn FROM engine_unit")
        esns = [row[0] for row in c.fetchall()]
    return models, esns

models, esns = load_options()
mode = st.radio("Méthode de tri", ["Par modèle → moteur → tâche", "Par tâche → modèle → moteur"], horizontal=True)

if mode == "Par modèle → moteur → tâche":
    selected_model = st.selectbox("📦 Choisir un modèle", models)
    with get_pg_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT esn FROM engine_unit WHERE model = %s", (selected_model,))
        model_esns = [row[0] for row in c.fetchall()]
    selected_esn = st.selectbox("🔧 Choisir un moteur", model_esns)

    st.markdown(f"### 🔍 Détails pour le moteur **{selected_esn}**")
    with get_pg_connection() as conn:
        c = conn.cursor()

        tables = {
            "🔄 Engine Changes": ("engine_changes", "engine_esn"),
            "🏭 In Shop": ("shop_entries", "engine_esn"),
            "👁️ On Watch": ("on_watch", "engine_esn"),
            "⚙️ Monitoring": ("condition_monitoring", "engine_esn"),
            "✅ Autres tâches": ("other_tasks", "engine_esn")
        }

        for title, (table, col) in tables.items():
            c.execute(f"SELECT * FROM {table} WHERE {col} = %s", (selected_esn,))
            rows = c.fetchall()
            if rows:
                st.subheader(title)
                for row in rows:
                    st.markdown(f"- {row}")

else:
    task_categories = {
        "Engine Changes": "engine_changes",
        "In Shop": "shop_entries",
        "On Watch": "on_watch",
        "Monitoring": "condition_monitoring",
        "Autres tâches": "other_tasks"
    }
    selected_task = st.selectbox("🗂️ Choisir une catégorie", list(task_categories.keys()))
    table = task_categories[selected_task]

    with get_pg_connection() as conn:
        c = conn.cursor()
        c.execute(f"SELECT DISTINCT engine_esn FROM {table}")
        task_esns = [row[0] for row in c.fetchall()]

        if not task_esns:
            st.warning("Aucun moteur trouvé pour cette tâche.")
        else:
            c.execute("SELECT DISTINCT model FROM engine_unit WHERE esn = ANY(%s)", (task_esns,))
            models = [row[0] for row in c.fetchall()]
            selected_model = st.selectbox("📦 Choisir un modèle associé", models)

            c.execute("SELECT esn FROM engine_unit WHERE model = %s AND esn = ANY(%s)", (selected_model, task_esns))
            filtered_esns = [row[0] for row in c.fetchall()]
            selected_esn = st.selectbox("Choisir un moteur (ESN)", filtered_esns)

            st.markdown(f"### 🔍 Moteur **{selected_esn}** ({selected_model})")
            st.markdown(f"➡️ Tâche : **{selected_task}**")

            c.execute(f"SELECT * FROM {table} WHERE engine_esn = %s", (selected_esn,))
            rows = c.fetchall()
            for row in rows:
                st.markdown(f"- {row}")
