#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "inout.h"
#include "location.h"
#include "genetic.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s distance_file.csv\n", argv[0]);
        return EXIT_FAILURE;
    }

    Board board;
    initBoard(board);

    if (!fread_board(argv[1], board)) {
        printf("Erreur lors de la lecture du fichier\n");
        return EXIT_FAILURE;
    }
    display_board(board);

    Solution best_solution;
    printf("Démarrage de l'algorithme VRP...\n");
    clock_t start = clock();
    solve_vrp(board, &best_solution);
    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Algorithme terminé en %.2f secondes.\n", elapsed);

    print_solution(&best_solution);

    // Calcul des statistiques
    float total_distance_km = best_solution.total_duration / 3600.0 * 50.0; // 50 km/h
    float fuel_consumption = total_distance_km * 6.5 / 100.0; // 6.5 L/100km
    float fuel_cost = fuel_consumption * 1.72; // 1.72 €/L

    printf("\nStatistiques globales:\n");
    printf("Distance totale: %.2f km\n", total_distance_km);
    printf("Consommation carburant: %.2f L\n", fuel_consumption);
    printf("Coût carburant: %.2f €\n", fuel_cost);

    return EXIT_SUCCESS;
}