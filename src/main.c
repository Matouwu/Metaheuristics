#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include "inout.h"
#include "location.h"
#include "genetic.h"

int main(int argc, char* argv[]) {
    if (argc < 3) {
        printf("Usage: %s time_file.csv distance_file.csv\n", argv[0]);
        return EXIT_FAILURE;
    }

    Board time_board, dist_board;
    initBoard(time_board);
    initBoard(dist_board);

    if (!fread_board(argv[1], time_board)) {
        printf("Erreur lors de la lecture du fichier temps\n");
        return EXIT_FAILURE;
    }
    if (!fread_board(argv[2], dist_board)) {
        printf("Erreur lors de la lecture du fichier distances\n");
        return EXIT_FAILURE;
    }

    printf("Nombre de villes detecté : %d\n", NUM_CITIES);
    printf("Matrice temps:\n");
    display_board(time_board);
    printf("\nMatrice distances:\n");
    display_board(dist_board);

    Solution best_solution;
    printf("\nDémarrage de l'algorithme génétique...\n");
    clock_t start = clock();

    int best_fitness = INT_MAX;
    Solution candidate;

    for (int run = 0; run < 5; run++) {
        solve_vrp(time_board, dist_board, &candidate);
        long long fitness = calculate_fitness(time_board, dist_board, &candidate);

        if (fitness < best_fitness) {
            best_solution = candidate;
            best_fitness = fitness;
        }
        printf("Execution %d: fitness=%lld\n", run+1, fitness);
    }

    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    printf("\nAlgorithme termine en %.2f secondes\n", elapsed);

    print_solution(&best_solution);
    write_solution("data/output.txt", &best_solution);

    // Calcul des statistiques
    float total_distance_km = best_solution.total_distance / 1000.0;
    float fuel_consumption = total_distance_km * 6.5 / 100.0; // 6.5 L/100km
    float fuel_cost = fuel_consumption * 1.72; // 1.72 €/L

    printf("\nStatistiques globales:\n");
    printf("Distance totale: %.2f km\n", total_distance_km);
    printf("Consommation carburant: %.2f L\n", fuel_consumption);
    printf("Coût carburant: %.2f €\n", fuel_cost);

    return EXIT_SUCCESS;
}