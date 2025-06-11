import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time


def geocode_pharmacies_simple(input_file: str, output_file: str):
    """
    Version simplifiée pour géocoder les pharmacies avec geopy.

    Installation requise: pip install geopy pandas
    """

    # Initialisation du géocodeur
    geolocator = Nominatim(user_agent="pharmacy_geocoder")

    # Lecture du fichier CSV
    print("Chargement des données...")
    df = pd.read_csv(input_file, header=None, names=['nom', 'adresse', 'code_postal', 'ville'])

    # Ajout des colonnes pour les coordonnées
    df['latitude'] = None
    df['longitude'] = None

    print(f"Géocodage de {len(df)} pharmacies...")

    for index, row in df.iterrows():
        try:
            # Construction de l'adresse complète
            full_address = f"{row['adresse']}, {row['code_postal']} {row['ville']}, France"

            print(f"{index + 1}/{len(df)}: {row['nom']}")

            # Géocodage
            location = geolocator.geocode(full_address, timeout=10)

            if location:
                df.at[index, 'latitude'] = location.latitude
                df.at[index, 'longitude'] = location.longitude
                print(f"  ✅ Trouvé: {location.latitude:.6f}, {location.longitude:.6f}")
            else:
                print(f"  ❌ Non trouvé")

            # Pause pour respecter les limites de l'API
            time.sleep(1)

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"  ⚠️ Erreur de géocodage: {e}")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

    # Sauvegarde
    df.to_csv(output_file, index=False, encoding='utf-8')

    # Statistiques
    success_count = df['latitude'].notna().sum()
    print(f"\n📊 Résultats:")
    print(f"  - Géocodées avec succès: {success_count}/{len(df)}")
    print(f"  - Fichier sauvegardé: {output_file}")


if __name__ == "__main__":
    geocode_pharmacies_simple("livraison85.csv", "pharmacies_coordonnees.csv")