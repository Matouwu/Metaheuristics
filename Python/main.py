import os
import sys
from coord import create_indexed_pharmacy_file
from matrix import extract_and_convert_matrices


def main():
    """
    Script principal qui exécute coord.py puis matrix.py en séquence.
    """

    print("🚀 Script principal - Traitement des pharmacies")
    print("=" * 50)

    # Vérifier que le fichier d'entrée existe
    input_file = 'input/livraison20.csv'
    if not os.path.exists(input_file):
        print(f"❌ Fichier d'entrée non trouvé: {input_file}")
        print("📁 Vérifiez que le fichier existe dans le dossier input/")
        return False

    print(f"✅ Fichier d'entrée trouvé: {input_file}")

    # Étape 1: Exécuter coord.py
    print(f"\n📍 Étape 1: Création du fichier de correspondance")
    print("-" * 40)

    try:
        result_coord = create_indexed_pharmacy_file(input_file)

        if result_coord is not None and len(result_coord) > 0:
            print(f"✅ Étape 1 réussie: {len(result_coord)} pharmacies traitées")
            print(f"📁 Fichier créé: sources/coord.csv")
        else:
            print("❌ Étape 1 échouée: Aucune pharmacie traitée")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de l'étape 1: {e}")
        return False

    # Vérifier que le fichier coord.csv a été créé
    if not os.path.exists('sources/coord.csv'):
        print("❌ Le fichier sources/coord.csv n'a pas été créé")
        return False

    # Étape 2: Exécuter matrix.py
    print(f"\n🗺️ Étape 2: Extraction des matrices")
    print("-" * 40)

    try:
        result_matrix = extract_and_convert_matrices()

        if result_matrix is not None:
            print(f"✅ Étape 2 réussie: Matrices extraites")
            print(f"📁 Fichiers créés dans output/")
        else:
            print("❌ Étape 2 échouée: Extraction des matrices impossible")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de l'étape 2: {e}")
        return False

    # Vérification finale
    output_files = ['output/coord.csv', 'output/meters.csv', 'output/time.csv']
    missing_files = [f for f in output_files if not os.path.exists(f)]

    if missing_files:
        print(f"⚠️ Fichiers manquants: {missing_files}")
        return False

    # Résumé final
    print(f"\n🎉 Traitement terminé avec succès!")
    print("=" * 50)
    print(f"📊 Résumé:")
    print(f"   - Fichier d'entrée: {input_file}")
    print(f"   - Pharmacies traitées: {len(result_coord)}")
    print(f"   - Fichiers de sortie:")

    for file in output_files:
        if os.path.exists(file):
            print(f"     ✅ {file}")
        else:
            print(f"     ❌ {file}")

    print(f"\n📁 Les fichiers finaux sont dans le dossier output/")

    return True


def check_dependencies():
    """
    Vérifie que tous les fichiers et dossiers nécessaires existent.
    """

    print("🔍 Vérification des dépendances...")

    # Vérifier les scripts
    required_scripts = ['coord.py', 'matrix.py']
    for script in required_scripts:
        if not os.path.exists(script):
            print(f"❌ Script manquant: {script}")
            return False
        print(f"✅ {script}")

    # Vérifier les dossiers
    required_dirs = ['input', 'sources']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Dossier manquant: {directory}")
            return False
        print(f"✅ {directory}/")

    # Vérifier les fichiers sources
    required_files = [
        'input/livraison20.csv',
        'sources/pharmacies_coordonnees.csv',
        'sources/meters.csv',
        'sources/time.csv'
    ]

    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)

    if missing_files:
        print(f"\n⚠️ Fichiers manquants: {len(missing_files)}")
        print("📝 Assurez-vous que tous les fichiers requis sont présents")
        return False

    print("✅ Toutes les dépendances sont présentes")
    return True


if __name__ == "__main__":
    # Vérifier les dépendances
    if not check_dependencies():
        print("\n❌ Vérification des dépendances échouée")
        sys.exit(1)

    # Exécuter le traitement principal
    success = main()

    if success:
        print("\n🎯 Traitement terminé avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Traitement échoué")
        sys.exit(1)