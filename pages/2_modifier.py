
import streamlit as st
import psycopg2
from datetime import datetime
import pytz

st.set_page_config(page_title="Modifier les tâches", layout="wide")
st.title("✏️ Modifier les tâches liées aux moteurs")

now = datetime.now(pytz.timezone("Africa/Casablanca")).date()
st.caption(f"📅 Date actuelle : {now}")

def get_pg_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

with get_pg_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT esn, model FROM engine_unit")
    moteurs = c.fetchall()

models = sorted(set([m[1] for m in moteurs]))
model_to_esns = {}
for esn, model in moteurs:
    model_to_esns.setdefault(model, []).append(esn)

st.subheader("🧭 Sélection du moteur")
selected_model = st.selectbox("📦 Modèle", models)
selected_esn = st.selectbox("🔧 Numéro de série (ESN)", model_to_esns[selected_model])

st.subheader("📌 Type de tâche à ajouter")
task_type = st.selectbox("Tâche", [
    "Engine Changes", "Engines in Shop", "Spare Engines Level", "Lease Engines Level",
    "On Watch", "Condition Monitoring", "Contrats et Appels d’Offres", "Autres Tâches"
])
st.markdown("---")

def insert_task(table, fields, values):
    with get_pg_connection() as conn:
        c = conn.cursor()
        query = f"INSERT INTO {table} (engine_esn, " + ", ".join(fields) + ") VALUES (%s, " + ", ".join(["%s"] * len(values)) + ")"
        c.execute(query, (selected_esn, *values))
        conn.commit()

if task_type == "Engine Changes":
    change_type = st.selectbox("Type", ["past", "upcoming"])
    out_esn = st.text_input("ESN OUT")
    in_esn = st.text_input("ESN IN")
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("engine_changes", ["type", "out_esn", "in_esn", "date_added"], [change_type, out_esn, in_esn, date.strftime("%Y-%m-%d")])

elif task_type == "Engines in Shop":
    status = st.selectbox("Statut", ["In Progress", "Completed"])
    commentaire = st.text_area("Commentaire")
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("shop_entries", ["status", "commentaire", "date_added"], [status, commentaire, date.strftime("%Y-%m-%d")])

elif task_type == "Spare Engines Level":
    semaine = st.selectbox("Semaine", ["S", "S+1", "S+2", "S+3", "S+4"])
    quantite = st.number_input("Quantité", min_value=0, step=1)
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("spare_engines", ["semaine", "quantite", "date_added"], [semaine, quantite, date.strftime("%Y-%m-%d")])

elif task_type == "Lease Engines Level":
    semaine = st.selectbox("Semaine", ["S", "S+1", "S+2", "S+3", "S+4"])
    quantite = st.number_input("Quantité", min_value=0, step=1)
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("lease_engines", ["semaine", "quantite", "date_added"], [semaine, quantite, date.strftime("%Y-%m-%d")])

elif task_type == "On Watch":
    raison = st.text_area("Raison")
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("on_watch", ["raison", "date_added"], [raison, date.strftime("%Y-%m-%d")])

elif task_type == "Condition Monitoring":
    cat = st.selectbox("Catégorie", ["CNR", "Upcoming CNR", "Upcoming BSI", "Fault"])
    desc = st.text_input("Description")
    date = st.date_input("Date limite", value=now)
    if st.button("➕ Ajouter"):
        insert_task("condition_monitoring", ["category", "description", "due_date"], [cat, desc, date.strftime("%Y-%m-%d")])

elif task_type == "Contrats et Appels d’Offres":
    desc = st.text_input("Description")
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("contracts_tasks", ["description", "due_date"], [desc, date.strftime("%Y-%m-%d")])

elif task_type == "Autres Tâches":
    titre = st.text_input("Titre")
    contenu = st.text_area("Contenu")
    date = st.date_input("Date", value=now)
    if st.button("➕ Ajouter"):
        insert_task("other_tasks", ["title", "content", "date_added"], [titre, contenu, date.strftime("%Y-%m-%d")])
