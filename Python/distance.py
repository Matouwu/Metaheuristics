import pandas as pd
import requests
import json
import numpy as np
import time
import logging
from typing import List, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DistanceMatrixCalculator:
    """Calculateur de matrice de distances et temps avec OpenRouteService."""

    def __init__(self, api_key: str):
        """
        Initialise le calculateur.

        Args:
            api_key: Clé API OpenRouteService
        """
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2/matrix/driving-car"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': api_key,
            'Content-Type': 'application/json; charset=utf-8'
        })

    def load_pharmacies(self, csv_file: str) -> pd.DataFrame:
        """Charge les pharmacies depuis le fichier CSV."""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            logger.info(f"Chargement de {len(df)} pharmacies depuis {csv_file}")

            required_columns = ['indice', 'latitude', 'longitude']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Colonnes manquantes: {missing_columns}")

            # Vérifier si les colonnes attendues existent
            if 'indice_original' in df.columns:
                logger.info("Structure détectée: colonnes 'indice' (séquentiel) et 'indice_original'")
            else:
                logger.info("Structure détectée: colonne 'indice' uniquement")

            df_clean = df.dropna(subset=['latitude', 'longitude'])
            if len(df_clean) < len(df):
                logger.warning(f"{len(df) - len(df_clean)} pharmacies supprimées (coordonnées manquantes)")

            return df_clean.sort_values('indice').reset_index(drop=True)

        except Exception as e:
            logger.error(f"Erreur lors du chargement de {csv_file}: {e}")
            raise

    def prepare_coordinates(self, df: pd.DataFrame) -> List[List[float]]:
        """Prépare les coordonnées au format requis par OpenRouteService."""
        coordinates = []
        for _, row in df.iterrows():
            coordinates.append([float(row['longitude']), float(row['latitude'])])

        logger.info(f"Préparation de {len(coordinates)} coordonnées")
        return coordinates

    def calculate_optimal_batch_size(self, total_locations: int) -> int:
        """Calcule la taille optimale des lots pour respecter la limite de 3500 routes."""
        max_routes_per_request = 3500
        max_sources_per_batch = max_routes_per_request // total_locations
        return max(1, min(max_sources_per_batch, total_locations))

    def calculate_matrices_batched(self, coordinates: List[List[float]],
                                   max_retries: int = 3) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Calcule les matrices de distances et temps via l'API OpenRouteService avec gestion des lots.

        Returns:
            Tuple (distance_matrix, duration_matrix) en mètres et secondes
        """
        total_locations = len(coordinates)
        total_routes = total_locations * total_locations
        batch_size = self.calculate_optimal_batch_size(total_locations)

        logger.info(f"📊 Analyse de la matrice:")
        logger.info(f"   - Pharmacies: {total_locations}")
        logger.info(f"   - Routes totales: {total_routes}")
        logger.info(f"   - Taille des lots: {batch_size} sources par requête")

        # Si tout tient dans une seule requête
        if total_routes <= 3500:
            logger.info("✅ Une seule requête suffira")
            return self._single_matrix_request(coordinates, max_retries)

        # Sinon, diviser en lots
        num_batches = (total_locations + batch_size - 1) // batch_size
        logger.info(f"🔄 Division en {num_batches} lots nécessaire")

        # Initialiser les matrices résultat
        distance_matrix = np.zeros((total_locations, total_locations))
        duration_matrix = np.zeros((total_locations, total_locations))

        # Traiter chaque lot
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, total_locations)
            sources = list(range(start_idx, end_idx))

            logger.info(f"📦 Lot {batch_idx + 1}/{num_batches}: sources {start_idx}-{end_idx - 1}")

            batch_distances, batch_durations = self._batch_matrix_request(
                coordinates, sources, max_retries
            )

            if batch_distances is None or batch_durations is None:
                logger.error(f"❌ Échec du lot {batch_idx + 1}")
                return None, None

            # Intégrer les résultats dans les matrices globales
            distance_matrix[start_idx:end_idx, :] = batch_distances
            duration_matrix[start_idx:end_idx, :] = batch_durations

            # Pause entre les requêtes pour respecter les limites
            if batch_idx < num_batches - 1:
                logger.info("⏳ Pause de 2 secondes...")
                time.sleep(2)

        logger.info("✅ Matrices complètes calculées avec succès!")
        return distance_matrix, duration_matrix

    def _single_matrix_request(self, coordinates: List[List[float]],
                               max_retries: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Requête simple pour petites matrices."""
        payload = {
            "locations": coordinates,
            "metrics": ["distance", "duration"],
            "units": "m"
        }

        return self._execute_matrix_request(payload, max_retries)

    def _batch_matrix_request(self, coordinates: List[List[float]],
                              sources: List[int], max_retries: int) -> Tuple[
        Optional[np.ndarray], Optional[np.ndarray]]:
        """Requête par lot avec paramètres sources/destinations."""
        payload = {
            "locations": coordinates,
            "sources": sources,
            "destinations": list(range(len(coordinates))),
            "metrics": ["distance", "duration"],
            "units": "m"
        }

        return self._execute_matrix_request(payload, max_retries)

    def _execute_matrix_request(self, payload: dict, max_retries: int) -> Tuple[
        Optional[np.ndarray], Optional[np.ndarray]]:
        """Exécute une requête vers l'API et retourne les matrices de distances et temps."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Requête API (tentative {attempt + 1}/{max_retries})...")

                response = self.session.post(
                    self.base_url,
                    data=json.dumps(payload),
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()
                    distances = np.array(data['distances'])
                    durations = np.array(data['durations'])
                    logger.info(f"✅ Réponse reçue: {distances.shape}")
                    return distances, durations

                elif response.status_code == 429:  # Rate limit
                    wait_time = 60 * (attempt + 1)
                    logger.warning(f"⏰ Rate limit atteint. Attente de {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(f"❌ Erreur API: {response.status_code} - {response.text}")
                    if attempt == max_retries - 1:
                        return None, None
                    time.sleep(10)

            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout lors de la tentative {attempt + 1}")
                if attempt == max_retries - 1:
                    return None, None
                time.sleep(30)

            except Exception as e:
                logger.error(f"❌ Erreur lors de la tentative {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return None, None
                time.sleep(10)

        return None, None

    def save_matrices(self, distance_matrix: np.ndarray, duration_matrix: np.ndarray,
                      pharmacy_df: pd.DataFrame) -> None:
        """Sauvegarde les matrices de distances et temps."""
        try:
            # Utiliser la colonne 'indice' (séquentielle) pour les indices des matrices
            indices = pharmacy_df['indice'].tolist()

            # Matrice des distances en mètres
            df_meters = pd.DataFrame(
                distance_matrix,
                index=indices,
                columns=indices
            )
            df_meters.to_csv('sources/meters.csv', encoding='utf-8')
            logger.info("✅ sources/meters.csv sauvegardé")

            # Matrice des temps en secondes
            df_time = pd.DataFrame(
                duration_matrix,
                index=indices,
                columns=indices
            )
            df_time.to_csv('sources/time.csv', encoding='utf-8')
            logger.info("✅ sources/time.csv sauvegardé")

            # Statistiques
            non_zero_distances = distance_matrix[distance_matrix > 0]
            non_zero_durations = duration_matrix[duration_matrix > 0]

            logger.info(f"📊 Statistiques distances:")
            logger.info(f"   - Distance minimale: {non_zero_distances.min():.0f} m")
            logger.info(f"   - Distance maximale: {distance_matrix.max():.0f} m")
            logger.info(f"   - Distance moyenne: {non_zero_distances.mean():.0f} m")

            logger.info(f"📊 Statistiques temps:")
            logger.info(f"   - Temps minimal: {non_zero_durations.min():.0f} s")
            logger.info(f"   - Temps maximal: {duration_matrix.max():.0f} s")
            logger.info(f"   - Temps moyen: {non_zero_durations.mean():.0f} s")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise


def main():
    """Fonction principale."""

    # Configuration
    input_file = "sources/coord.csv"

    # IMPORTANT: Remplacez par votre vraie clé API OpenRouteService
    api_key = "5b3ce3597851110001cf62488b7a0b7a0c8242f3ad01b013cd2a3808"

    if api_key == "VOTRE_CLE_API_ICI":
        print("❌ ERREUR: Vous devez obtenir une clé API OpenRouteService!")
        print("🔗 Rendez-vous sur: https://openrouteservice.org/dev/#/signup")
        print("📝 Remplacez 'VOTRE_CLE_API_ICI' par votre vraie clé API")
        return

    try:
        # Initialisation
        calculator = DistanceMatrixCalculator(api_key)

        # Chargement des pharmacies
        logger.info("🔄 Chargement des pharmacies...")
        pharmacy_df = calculator.load_pharmacies(input_file)

        if len(pharmacy_df) == 0:
            logger.error("Aucune pharmacie trouvée dans le fichier")
            return

        # Préparation des coordonnées
        coordinates = calculator.prepare_coordinates(pharmacy_df)

        logger.info(f"📍 Calcul des matrices {len(coordinates)}x{len(coordinates)}...")
        logger.info("⏳ Cela peut prendre quelques minutes...")

        # Calcul des matrices de distances et temps
        distance_matrix, duration_matrix = calculator.calculate_matrices_batched(coordinates)

        if distance_matrix is None or duration_matrix is None:
            logger.error("❌ Échec du calcul des matrices")
            return

        # Sauvegarde des résultats
        logger.info("💾 Sauvegarde des résultats...")
        calculator.save_matrices(distance_matrix, duration_matrix, pharmacy_df)

        print(f"\n🎉 Calcul terminé avec succès!")
        print(f"📁 Fichiers créés:")
        print(f"   - sources/meters.csv (distances en mètres)")
        print(f"   - sources/time.csv (temps en secondes)")

    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise


if __name__ == "__main__":
    main()