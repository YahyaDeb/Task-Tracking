# ✅ MODIFIER.PY COMPLET - Gestion des 8 KPI
import streamlit as st
import sqlite3
from datetime import datetime
import pytz

DB_PATH = "airworthiness.db"
st.set_page_config(page_title="Modifier les tâches", layout="wide")
st.title("✏️ Modifier les tâches liées aux moteurs")

# 📅 Date actuelle au Maroc
now = datetime.now(pytz.timezone("Africa/Casablanca")).date()
st.caption(f"📅 Date actuelle : {now}")

# === Récupération moteurs ===
with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute("SELECT esn, model FROM engine_unit")
    moteurs = c.fetchall()

models = sorted(set([m[1] for m in moteurs]))
model_to_esns = {}
for esn, model in moteurs:
    model_to_esns.setdefault(model, []).append(esn)

# === Choix moteur ===
st.subheader("🧭 Sélection du moteur")
selected_model = st.selectbox("📦 Modèle", models)
selected_esn = st.selectbox("🔧 Numéro de série (ESN)", model_to_esns[selected_model])

# === Choix tâche ===
st.subheader("📌 Type de tâche à ajouter")
task_type = st.selectbox("Tâche", [
    "Engine Changes", "Engines in Shop", "Spare Engines Level", "Lease Engines Level",
    "On Watch", "Condition Monitoring", "Contrats et Appels d’Offres", "Autres Tâches"
])
st.markdown("---")

# === Formulaire par type de tâche ===
def insert_and_manage(table, fields, insert_stmt, field_labels):
    values = []
    for label in field_labels:
        field_type = field_labels[label]
        if field_type == "text":
            values.append(st.text_input(label))
        elif field_type == "area":
            values.append(st.text_area(label))
        elif field_type == "select_status":
            values.append(st.selectbox(label, ["In Progress", "Completed"]))
        elif field_type == "select_type":
            values.append(st.selectbox(label, ["past", "upcoming"]))
        elif field_type == "select_cat":
            values.append(st.selectbox(label, ["CNR", "Upcoming CNR", "Upcoming BSI", "Fault"]))
        elif field_type == "select_week":
            values.append(st.selectbox(label, ["S", "S+1", "S+2", "S+3", "S+4"]))
        elif field_type == "number":
            values.append(st.number_input(label, min_value=0, step=1))
        elif field_type == "date":
            values.append(st.date_input(label, value=now))

    if st.button("➕ Ajouter"):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(insert_stmt, (selected_esn, *[v.strftime("%Y-%m-%d") if isinstance(v, datetime) else v for v in values]))
            conn.commit()
        st.success("✅ Tâche ajoutée.")

    # === Affichage existant ===
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        try:
            c.execute(f"SELECT rowid, * FROM {table} WHERE engine_esn = ?", (selected_esn,))
            rows = c.fetchall()
        except:
            st.warning(f"⚠️ Table {table} introuvable.")
            return

    if rows:
        st.markdown("### 🛠️ Modifier ou Supprimer")
        for row in rows:
            with st.expander(f"📝 {row[1:]}"):
                updated_vals = []
                for i, label in enumerate(field_labels):
                    ftype = field_labels[label]
                    val = row[i+2]  # décalé de 2 (rowid + esn)
                    if ftype == "text":
                        updated_vals.append(st.text_input(f"🖊️ {label}", value=val, key=f"{row[0]}_{label}"))
                    elif ftype == "area":
                        updated_vals.append(st.text_area(f"🖊️ {label}", value=val, key=f"{row[0]}_{label}"))
                    elif ftype == "select_status":
                        updated_vals.append(st.selectbox(f"{label}", ["In Progress", "Completed"], index=["In Progress", "Completed"].index(val), key=f"{row[0]}_{label}"))
                    elif ftype == "select_type":
                        updated_vals.append(st.selectbox(f"{label}", ["past", "upcoming"], index=["past", "upcoming"].index(val), key=f"{row[0]}_{label}"))
                    elif ftype == "select_cat":
                        updated_vals.append(st.selectbox(f"{label}", ["CNR", "Upcoming CNR", "Upcoming BSI", "Fault"], index=["CNR", "Upcoming CNR", "Upcoming BSI", "Fault"].index(val), key=f"{row[0]}_{label}"))
                    elif ftype == "select_week":
                        updated_vals.append(st.selectbox(f"{label}", ["S", "S+1", "S+2", "S+3", "S+4"], index=["S", "S+1", "S+2", "S+3", "S+4"].index(val), key=f"{row[0]}_{label}"))
                    elif ftype == "number":
                        updated_vals.append(st.number_input(f"{label}", value=int(val), key=f"{row[0]}_{label}"))
                    elif ftype == "date":
                        updated_vals.append(st.date_input(f"{label}", value=datetime.strptime(val, "%Y-%m-%d"), key=f"{row[0]}_{label}"))

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Modifier", key=f"save_{row[0]}"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            sets = ', '.join([f"{k} = ?" for k in field_labels])
                            c.execute(f"UPDATE {table} SET {sets} WHERE rowid = ?", (
                                *[v.strftime("%Y-%m-%d") if isinstance(v, datetime) else v for v in updated_vals], row[0]))
                            conn.commit()
                        st.success("✅ Modifié.")
                        st.experimental_rerun()
                with col2:
                    if st.button("🗑️ Supprimer", key=f"del_{row[0]}"):
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute(f"DELETE FROM {table} WHERE rowid = ?", (row[0],))
                            conn.commit()
                        st.warning("🗑️ Supprimé.")
                        st.experimental_rerun()

# === Délégation selon le type de tâche ===
if task_type == "Engine Changes":
    insert_and_manage("engine_changes", ["type", "out_esn", "in_esn", "date_added"],
                      "INSERT INTO engine_changes (engine_esn, type, out_esn, in_esn, date_added) VALUES (?, ?, ?, ?, ?)",
                      {"Type de changement": "select_type", "ESN OUT": "text", "ESN IN": "text", "Date": "date"})

elif task_type == "Engines in Shop":
    insert_and_manage("shop_entries", ["status", "commentaire", "date_added"],
                      "INSERT INTO shop_entries (engine_esn, status, commentaire, date_added) VALUES (?, ?, ?, ?)",
                      {"Statut": "select_status", "Commentaire": "area", "Date": "date"})

elif task_type == "Spare Engines Level":
    insert_and_manage("spare_engines", ["semaine", "quantite", "date_added"],
                      "INSERT INTO spare_engines (engine_esn, semaine, quantite, date_added) VALUES (?, ?, ?, ?)",
                      {"Semaine": "select_week", "Quantité": "number", "Date": "date"})

elif task_type == "Lease Engines Level":
    insert_and_manage("lease_engines", ["semaine", "quantite", "date_added"],
                      "INSERT INTO lease_engines (engine_esn, semaine, quantite, date_added) VALUES (?, ?, ?, ?)",
                      {"Semaine": "select_week", "Quantité": "number", "Date": "date"})

elif task_type == "On Watch":
    insert_and_manage("on_watch", ["raison", "date_added"],
                      "INSERT INTO on_watch (engine_esn, raison, date_added) VALUES (?, ?, ?)",
                      {"Raison": "area", "Date": "date"})

elif task_type == "Condition Monitoring":
    insert_and_manage("condition_monitoring", ["category", "description", "due_date"],
                      "INSERT INTO condition_monitoring (engine_esn, category, description, due_date) VALUES (?, ?, ?, ?)",
                      {"Catégorie": "select_cat", "Description": "text", "Date limite": "date"})

elif task_type == "Contrats et Appels d’Offres":
    insert_and_manage("contracts_tasks", ["description", "date_added"],
                      "INSERT INTO contracts_tasks (engine_esn, description, date_added) VALUES (?, ?, ?)",
                      {"Description": "text", "Date": "date"})

elif task_type == "Autres Tâches":
    insert_and_manage("other_tasks", ["title", "content", "date_added"],
                      "INSERT INTO other_tasks (engine_esn, title, content, date_added) VALUES (?, ?, ?, ?)",
                      {"Titre": "text", "Contenu": "area", "Date": "date"})
