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
    int best_fitness;

    printf("Démarrage de l'algorithme génétique...\n");
    solve_tsp(board, best_path, &best_fitness);
    printf("Algorithme génétique terminé.\n");

    printf("Meilleur chemin trouvé:\n");
    print_path(best_path);

    printf("Temps total: %d secondes (%.2f minutes)\n",
           best_fitness, best_fitness / 60.0);

    /* Calcul des statistiques supplémentaires */
    float distance_km = best_fitness / 3600.0 * 50.0;  /* Conversion temps->km (50 km/h moyen) */
    float fuel_consumption = distance_km * 6.5 / 100.0; /* 6.5L/100km */
    float fuel_cost = fuel_consumption * 1.72;          /* 1.72€/L */

    printf("Distance approximative: %.2f km\n", distance_km);
    printf("Consommation de carburant estimée: %.2f L\n", fuel_consumption);
    printf("Coût du carburant: %.2f €\n", fuel_cost);

    return EXIT_SUCCESS;
}