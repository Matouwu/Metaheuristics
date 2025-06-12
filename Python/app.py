import subprocess

import streamlit as st
import pandas as pd
import os
from coord import create_indexed_pharmacy_file
from matrix import extract_and_convert_matrices


def main():

    st.header("Upload du fichier CSV")

    uploaded_file = st.file_uploader(
        "Choisissez votre fichier CSV de pharmacies",
        type=['csv']
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, header=None, names=['Nom', 'Adresse', 'Code Postal', 'Ville'])

            st.success(f"Fichier chargé: {len(df)} pharmacies")

            st.header("Aperçu du fichier")
            st.dataframe(df)

            if st.button("Trouver le meilleur chemin", type="primary"):
                process_file(uploaded_file)

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

    else:
        st.info("Veuillez uploader un fichier CSV pour commencer")


def process_file(uploaded_file):

    with st.spinner("Traitement en cours..."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Extraction des données")
            progress_bar.progress(10)

            os.makedirs('input', exist_ok=True)

            temp_file_path = f"input/{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result_coord = create_indexed_pharmacy_file(temp_file_path)

            result_matrix = extract_and_convert_matrices()

            if result_matrix is None:
                st.error("Échec de l'extraction des matrices")
                return

            status_text.text("Extraction des données réussie")
            progress_bar.progress(20)

            number = len(result_coord)

            display_matrixes(result_matrix)

            cmd = ["./../Prototype/recuit", "output/time.csv"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"Erreur: {result.stderr}")

        except Exception as e:
            st.error(f"Erreur durant le traitement: {e}")
            progress_bar.empty()
            status_text.empty()


def display_matrixes(result_matrix):
    tab1, tab2, tab3 = st.tabs(["Matrice des distances", "Matrice des temps de trajet", "Coordonées"])

    with tab1:
        st.dataframe(result_matrix[0], use_container_width=True)

    with tab2:
        st.dataframe(result_matrix[1], use_container_width=True)

    with tab3:
        st.dataframe(result_matrix[2], use_container_width=True)



if __name__ == "__main__":

    st.set_page_config(
        page_title="CERP Genetic",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    main()