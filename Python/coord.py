import os

import pandas as pd


def create_indexed_pharmacy_file(file):

    print("Chargement des fichiers")

    # Charger le fichier avec toutes les coordonnées (maintenant avec colonne indice)
    coord_df = pd.read_csv('Python/sources/pharmacies_coordonnees.csv', encoding='utf-8')

    # Charger le fichier sous-ensemble
    subset_df = pd.read_csv(file, header=None,
                            names=['nom', 'adresse', 'code_postal', 'ville'],
                            encoding='utf-8')

    # Récupérer automatiquement la ligne d'indice 0
    index_0_row = coord_df[coord_df['indice'] == 0]
    if len(index_0_row) == 0:
        print("Aucune ligne avec indice 0 trouvée dans pharmacies_coordonnees.csv")
        index_0_data = None
    else:
        index_0_data = index_0_row.iloc[0]

    # Préparer le DataFrame de résultat
    result_data = []

    # Ajouter d'abord la ligne d'indice 0 si elle existe (indice séquentiel = 0)
    if index_0_data is not None:
        result_data.append({
            'indice': 0,  # Indice séquentiel
            'indice_original': index_0_data['indice'],  # Indice original
            'nom': index_0_data['nom'],
            'adresse': index_0_data['adresse'],
            'code_postal': index_0_data['code_postal'],
            'ville': index_0_data['ville'],
            'latitude': index_0_data['latitude'],
            'longitude': index_0_data['longitude']
        })

    matches_found = 0
    sequential_index = 1 if index_0_data is not None else 0  # Commencer à 1 si l'indice 0 existe

    for index, row in subset_df.iterrows():
        # Recherche par nom exact
        match = coord_df[coord_df['nom'].str.lower().str.strip() == row['nom'].lower().strip()]

        if len(match) > 0:
            # Récupérer les données de la pharmacie correspondante
            match_data = match.iloc[0]
            result_data.append({
                'indice': sequential_index,  # Indice séquentiel
                'indice_original': match_data['indice'],  # Indice original
                'nom': match_data['nom'],
                'adresse': match_data['adresse'],
                'code_postal': match_data['code_postal'],
                'ville': match_data['ville'],
                'latitude': match_data['latitude'],
                'longitude': match_data['longitude']
            })
            matches_found += 1
            sequential_index += 1
        else:
            print(f"{row['nom']} → Non trouvé")

    # Créer le DataFrame final
    result_df = pd.DataFrame(result_data)

    os.makedirs("Python/output", exist_ok=True)

    # Sauvegarder le fichier
    result_df.to_csv('Python/output/coord.csv', index=False, encoding='utf-8')

    print(f"Fichiers créé:")
    print(f"   - Python/output/coord.csv")

    return result_df


if __name__ == "__main__":
    result = create_indexed_pharmacy_file('input/livraison20.csv')

    # Afficher le résumé final
    valid_pharmacies = result.dropna(subset=['indice'])
    if len(valid_pharmacies) > 0:
        indices = valid_pharmacies['indice'].astype(int).tolist()
    else:
        print(f"\nAucune correspondance trouvée!")