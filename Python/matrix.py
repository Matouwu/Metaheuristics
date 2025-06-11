import pandas as pd
import numpy as np
import os


def extract_and_convert_matrices():
    """
    Extrait les sous-matrices avec indices originaux puis les convertit en indices séquentiels.
    """

    print("🔄 Extraction des sous-matrices...")

    # 1. Charger le fichier de correspondance
    try:
        coord_df = pd.read_csv('sources/coord.csv', encoding='utf-8')
        print(f"✅ {len(coord_df)} pharmacies chargées")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return

    # 2. Récupérer les indices originaux
    indices_originaux = coord_df['indice_original'].tolist()

    # 3. Charger les matrices complètes
    try:
        distance_matrix = pd.read_csv('sources/meters.csv', encoding='utf-8', index_col=0)
        time_matrix = pd.read_csv('sources/time.csv', encoding='utf-8', index_col=0)
        print(f"✅ Matrices complètes chargées: {distance_matrix.shape}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return

    # 4. Préparer les indices (format mixte: lignes entières, colonnes strings)
    indices_lignes = indices_originaux
    indices_colonnes = [str(idx) for idx in indices_originaux]

    # 5. Extraire les sous-matrices
    try:
        sub_distance = distance_matrix.loc[indices_lignes, indices_colonnes]
        sub_time = time_matrix.loc[indices_lignes, indices_colonnes]
        print(f"✅ Sous-matrices extraites: {sub_distance.shape}")
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        return

    # 6. Convertir vers indices séquentiels
    indices_sequentiels = list(range(len(coord_df)))

    final_distance_matrix = pd.DataFrame(
        sub_distance.values,
        index=indices_sequentiels,
        columns=indices_sequentiels
    )

    final_time_matrix = pd.DataFrame(
        sub_time.values,
        index=indices_sequentiels,
        columns=indices_sequentiels
    )

    print(f"✅ Conversion vers indices séquentiels terminée")

    # 7. Créer le dossier de sortie et sauvegarder
    os.makedirs('final_input', exist_ok=True)

    try:
        final_distance_matrix.to_csv('final_input/meters.csv', encoding='utf-8')
        final_time_matrix.to_csv('final_input/time.csv', encoding='utf-8')
        coord_df.to_csv('final_input/coord.csv', index=False, encoding='utf-8')

        print(f"✅ Fichiers sauvegardés dans final_input/")

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return

    # 8. Statistiques finales
    distance_values = final_distance_matrix.values
    time_values = final_time_matrix.values
    non_zero_distances = distance_values[distance_values > 0]
    non_zero_times = time_values[time_values > 0]

    print(f"\n📊 Statistiques:")
    print(f"   - Pharmacies: {len(coord_df)}")
    print(f"   - Distance moyenne: {non_zero_distances.mean():.0f} m")
    print(f"   - Temps moyen: {non_zero_times.mean():.0f} s")

    return final_distance_matrix, final_time_matrix, coord_df


if __name__ == "__main__":
    print("🗺️ Extracteur de sous-matrice")
    print("=" * 30)

    result = extract_and_convert_matrices()

    if result:
        print(f"\n🎉 Extraction réussie!")
        print(f"📁 Fichiers créés:")
        print(f"   - final_input/meters.csv")
        print(f"   - final_input/time.csv")
        print(f"   - final_input/coord.csv")
    else:
        print(f"\n❌ Extraction échouée")