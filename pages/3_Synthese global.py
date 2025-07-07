import streamlit as st
import sqlite3

DB_PATH = "airworthiness.db"

st.set_page_config(page_title="État des moteurs", layout="wide")
st.title("🧾 Vue globale de la flotte moteurs/APU")

# ===== Fonctions de lecture regroupée =====
def get_matrice_status():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT model, type FROM engine_unit GROUP BY model, type")
        models = c.fetchall()

        result = []
        for model, type_ in models:
            # Récupérer tous les moteurs de ce modèle
            c.execute("SELECT esn FROM engine_unit WHERE model = ?", (model,))
            all_esns = [row[0] for row in c.fetchall()]

            # In-Shop
            c.execute("SELECT engine_esn FROM shop_entries WHERE engine_esn IN ({seq})".format(
                seq=','.join(['?']*len(all_esns))), all_esns)
            in_shop = [row[0] for row in c.fetchall()]

            # Removal (type 'upcoming' où le moteur est dans 'out_esn')
            c.execute("SELECT out_esn FROM engine_changes WHERE change_type = 'upcoming' AND out_esn IN ({seq})".format(
                seq=','.join(['?']*len(all_esns))), all_esns)
            removals = [row[0] for row in c.fetchall()]

            # Shipping (type 'upcoming' où le moteur est dans 'in_esn')
            c.execute("SELECT in_esn FROM engine_changes WHERE change_type = 'upcoming' AND in_esn IN ({seq})".format(
                seq=','.join(['?']*len(all_esns))), all_esns)
            shipping = [row[0] for row in c.fetchall()]

            # Post-installation (type 'past' où le moteur est dans 'in_esn')
            c.execute("SELECT in_esn FROM engine_changes WHERE change_type = 'past' AND in_esn IN ({seq})".format(
                seq=','.join(['?']*len(all_esns))), all_esns)
            post_init = [row[0] for row in c.fetchall()]

            result.append({
                "model": model,
                "type": type_,
                "in_shop": in_shop,
                "removal": removals,
                "shipping": shipping,
                "post_installation": post_init
            })
        return result

# ===== Interface affichage =====
st.markdown("### 📋 Synthèse des statuts moteurs")
data = get_matrice_status()

for entry in data:
    st.subheader(f"🛠️ {entry['model']} ({entry['type']})")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**In Shop:** {', '.join(entry['in_shop']) if entry['in_shop'] else '-'}")
        st.markdown(f"**Removal (à déposer):** {', '.join(entry['removal']) if entry['removal'] else '-'}")
    with col2:
        st.markdown(f"**Shipping (préparé):** {', '.join(entry['shipping']) if entry['shipping'] else '-'}")
        st.markdown(f"**Post-installation:** {', '.join(entry['post_installation']) if entry['post_installation'] else '-'}")
