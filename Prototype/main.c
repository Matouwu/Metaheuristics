#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "inout.h"
#include "location.h"
#include "genetic.h"
#include "graphic.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s distance_file.csv\n", argv[0]);
        return EXIT_FAILURE;
    }

    Board board;
    initBoard(board);

    if (!fread_board(argv[1], board)) {
        printf("Erreur lors de la lecture du fichier de distances\n");
        return EXIT_FAILURE;
    }

    Path best_path;

    printf("Démarrage de l'algorithme génétique...\n");
    get_best_path(board, best_path, MAX_GENERATIONS);
    printf("Algorithme génétique terminé.\n");

    printf("Meilleur chemin trouvé:\n");
    print_path(best_path);

    int total_distance = calcul_fitness(board, best_path);
    printf("Distance totale: %d secondes (%.2f minutes)\n",
           total_distance, total_distance / 60.0);

    float distance_km = total_distance / 60.0 / 60.0 * 50.0;
    float fuel_consumption = distance_km * 6.5 / 100.0;
    float fuel_cost = fuel_consumption * 1.72;

    printf("Distance approximative: %.2f km\n", distance_km);
    printf("Consommation de carburant estimée: %.2f L\n", fuel_consumption);
    printf("Coût du carburant: %.2f €\n", fuel_cost);

    return EXIT_SUCCESS;
}