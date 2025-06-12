import pandas as pd
import numpy as np
import os


def extract_and_convert_matrices():
    print("Extraction des sous-matrices...")

    try:
        coord_df = pd.read_csv('Python/output/coord.csv', encoding='utf-8')
    except Exception as e:
        print(f"Erreur: {e}")
        return

    indices_originaux = coord_df['indice_original'].tolist()

    try:
        distance_matrix = pd.read_csv('Python/sources/meters.csv', encoding='utf-8', index_col=0)
        time_matrix = pd.read_csv('Python/sources/time.csv', encoding='utf-8', index_col=0)
    except Exception as e:
        print(f"Erreur: {e}")
        return

    indices_lignes = indices_originaux
    indices_colonnes = [str(idx) for idx in indices_originaux]

    try:
        sub_distance = distance_matrix.loc[indices_lignes, indices_colonnes]
        sub_time = time_matrix.loc[indices_lignes, indices_colonnes]
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}")
        return

    indices_sequentiels = list(range(len(coord_df)))

    final_distance_matrix = pd.DataFrame(
        sub_distance.values.astype(int),
        index=indices_sequentiels,
        columns=indices_sequentiels
    )

    final_time_matrix = pd.DataFrame(
        sub_time.values.astype(int),
        index=indices_sequentiels,
        columns=indices_sequentiels
    )


    os.makedirs('Python/output', exist_ok=True)

    try:
        final_distance_matrix.to_csv('Python/output/meters.csv', encoding='utf-8')
        final_time_matrix.to_csv('Python/output/time.csv', encoding='utf-8')

    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return

    print(f"Fichiers créés:")
    print(f"   - Python/output/meters.csv")
    print(f"   - Python/output/time.csv")

    return final_distance_matrix, final_time_matrix, coord_df


if __name__ == "__main__":
    print("Extracteur de sous-matrice")
    print("=" * 30)

    result = extract_and_convert_matrices()

    if result:
        print(f"\nExtraction réussie!")
        print(f"Fichiers créés:")
        print(f"   - Python/output/meters.csv")
        print(f"   - Python/output/time.csv")
        print(f"   - Python/output/coord.csv")
    else:
        print(f"\nExtraction échouée")