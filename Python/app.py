import subprocess

import streamlit as st
import pandas as pd
import os
from coord import create_indexed_pharmacy_file
from matrix import extract_and_convert_matrices
from pdf_generator import generate_pdf

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

            val = None

            if st.button("Trouver le meilleur chemin", type="primary"):
                with st.spinner("Traitement en cours :"):
                    process_file(uploaded_file)

            if "result_matrix" in st.session_state:
                display_matrixes(st.session_state["result_matrix"])

            if "Ran" in st.session_state:
                if st.button("PDF"):
                    generate_pdf()


        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

    else:
        st.info("Veuillez uploader un fichier CSV pour commencer")


def process_file(uploaded_file):

    try:
        os.makedirs('Python/input', exist_ok=True)
        temp_file_path = f"Python/input/{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state["result_coord"] = create_indexed_pharmacy_file(temp_file_path)
        st.session_state["result_matrix"]  = extract_and_convert_matrices()
        if st.session_state["result_matrix"] is None:
            st.error("Échec de l'extraction des matrices")
            return
        cmd = ["./vrp", "./Python/output/time.csv"]
        subprocess.run(cmd, capture_output=True, text=True)
        st.session_state["Ran"] = True
    except Exception as e:
        st.error(f"Erreur durant le traitement: {e}")


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