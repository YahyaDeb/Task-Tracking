import streamlit as st
import sqlite3
from datetime import datetime

esn_from_home = None

DB_PATH = "airworthiness.db"

st.set_page_config(page_title="Visualiser", layout="wide")
st.title("🔍 Visualiser les moteurs")

now = datetime.now().date()
st.caption(f"📅 Date actuelle : {now}")


# Charger les modèles et ESNs
def load_options():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT model FROM engine_unit")
        models = [row[0] for row in c.fetchall()]
        c.execute("SELECT DISTINCT esn FROM engine_unit")
        esns = [row[0] for row in c.fetchall()]
        return models, esns

models, esns = load_options()

# Déterminer le mode par défaut
mode_options = ["Par modèle → moteur → tâche", "Par tâche → modèle → moteur"]
default_mode_index = 0

mode = st.radio("Méthode de tri", mode_options, horizontal=True, index=default_mode_index)

# === MODE 1 : modèle → moteur → tâche
if mode == "Par modèle → moteur → tâche":
    selected_model = st.selectbox("📦 Choisir un modèle", models)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT esn FROM engine_unit WHERE model = ?", (selected_model,))
        filtered_esns = [row[0] for row in c.fetchall()]


    selected_esn = st.selectbox(
        "Choisir un moteur (ESN)",
        filtered_esns,
        index=filtered_esns.index(esn_from_home) if esn_from_home in filtered_esns else 0
    )

    st.markdown(f"### 🔍 Détails pour le moteur **{selected_esn}**")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM engine_changes WHERE engine_esn = ?", (selected_esn,))
        for row in c.fetchall():
            st.markdown(f"🔄 **Engine Change**: Type={row[1]} OUT={row[2]} IN={row[3]} – 📌 {row[4]}")

        c.execute("SELECT * FROM shop_entries WHERE engine_esn = ?", (selected_esn,))
        for row in c.fetchall():
            st.markdown(f"🏭 **In Shop**: Status={row[1]} – 📌 {row[2]}")

        c.execute("SELECT * FROM on_watch WHERE engine_esn = ?", (selected_esn,))
        for row in c.fetchall():
            st.markdown(f"👁️ **On Watch**: Raison={row[1]}")

        c.execute("SELECT * FROM condition_monitoring WHERE engine_esn = ?", (selected_esn,))
        for row in c.fetchall():
            try:
                due = datetime.strptime(row[3], "%Y-%m-%d").date()
                is_late = due < now
            except:
                is_late = False
            msg = f"⚙️ **{row[1]}**: {row[2]} – 📅 {row[3]}"
            if is_late:
                st.markdown(f"<span style='color:red'>{msg} ⚠️ En retard</span>", unsafe_allow_html=True)
            else:
                st.markdown(msg)

        c.execute("SELECT * FROM other_tasks WHERE engine_esn = ?", (selected_esn,))
        for row in c.fetchall():
            st.markdown(f"✅ **Autre tâche**: {row[1]} ({row[2]})")

# === MODE 2 : tâche → modèle → moteur
else:
    selected_task = st.selectbox("🗂️ Choisir une catégorie", [
        "Engine Changes", "In Shop", "On Watch", "Monitoring", "Autres tâches"
    ])

    task_table_map = {
        "Engine Changes": "engine_changes",
        "In Shop": "shop_entries",
        "On Watch": "on_watch",
        "Monitoring": "condition_monitoring",
        "Autres tâches": "other_tasks"
    }

    table = task_table_map[selected_task]

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Moteurs avec cette tâche
        c.execute(f"SELECT DISTINCT engine_esn FROM {table}")
        task_esns = [row[0] for row in c.fetchall()]

        if not task_esns:
            st.warning("Aucun moteur trouvé.")
        else:
            # Modèles associés
            c.execute("SELECT DISTINCT model FROM engine_unit WHERE esn IN ({})".format(','.join(['?']*len(task_esns))), task_esns)
            task_models = [row[0] for row in c.fetchall()]

            selected_model = st.selectbox("📦 Modèle", task_models)
            c.execute("SELECT esn FROM engine_unit WHERE model = ? AND esn IN ({})".format(','.join(['?']*len(task_esns))), (selected_model, *task_esns))
            model_esns = [row[0] for row in c.fetchall()]

            selected_esn = st.selectbox(
                "Choisir un moteur (ESN)",
                model_esns,
                index=model_esns.index(esn_from_home) if esn_from_home in model_esns else 0
            )

            st.markdown(f"### 🔍 Moteur **{selected_esn}** – tâche : **{selected_task}**")

            c.execute(f"SELECT * FROM {table} WHERE engine_esn = ?", (selected_esn,))
            for row in c.fetchall():
                if selected_task == "Engine Changes":
                    st.markdown(f"- Type: {row[1]}, OUT: {row[2]}, IN: {row[3]} 📌 {row[4]}")
                elif selected_task == "In Shop":
                    st.markdown(f"- Status: {row[1]} 📌 {row[2]}")
                elif selected_task == "On Watch":
                    st.markdown(f"- Raison: {row[1]}")
                elif selected_task == "Monitoring":
                    try:
                        due = datetime.strptime(row[3], "%Y-%m-%d").date()
                        is_late = due < now
                    except:
                        is_late = False
                    msg = f"- {row[1]}: {row[2]} – 📆 {row[3]}"
                    if is_late:
                        st.markdown(f"<span style='color:red'>{msg} ⚠️</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(msg)
                elif selected_task == "Autres tâches":
                    st.markdown(f"- {row[1]} ({row[2]})")
