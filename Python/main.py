import sys
import os
from coord import create_indexed_pharmacy_file
from matrix import extract_and_convert_matrices


def main():
    """
    Script principal qui exécute coord.py puis matrix.py en séquence.
    """

    print("🚀 Traitement des pharmacies")

    # Demander le fichier à l'utilisateur
    user_input = input("📁 Entrez le nom du fichier CSV (dossier input par défaut): ").strip()

    # Si pas de slash, ajouter le dossier input par défaut
    if "/" not in user_input and "\\" not in user_input:
        input_file = f"input/{user_input}"
    else:
        input_file = user_input

    # Vérifier que le fichier existe
    if not os.path.exists(input_file):
        print(f"❌ Fichier non trouvé: {input_file}")
        return False

    print(f"📍 Traitement de: {input_file}")

    # Étape 1: Création du fichier de correspondance
    print("📍 Création des correspondances...")
    try:
        result_coord = create_indexed_pharmacy_file(input_file)
        if result_coord is None or len(result_coord) == 0:
            print("❌ Échec de la création des correspondances")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    # Étape 2: Extraction des matrices
    print("🗺️ Extraction des matrices...")
    try:
        result_matrix = extract_and_convert_matrices()
        if result_matrix is None:
            print("❌ Échec de l'extraction des matrices")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    print(f"✅ Traitement terminé: {len(result_coord)} pharmacies")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)