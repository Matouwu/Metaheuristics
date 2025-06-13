#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include "inout.h"
#include "location.h"
#include "genetic.h"

int main(int argc, char* argv[]) {
    Board time_board, dist_board;
    Solution best_solution, candidate;
    int run;
    long long fitness;
    int best_fitness;
    clock_t start, end;
    double elapsed;
    float total_distance_km, fuel_consumption, fuel_cost;

    if (argc < 3) {
        printf("Usage: %s time_file.csv distance_file.csv\n", argv[0]);
        return EXIT_FAILURE;
    }

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

    printf("Nombre de villes : %d\n", NUM_CITIES);
    printf("Matrice temps:\n");
    display_board(time_board);
    printf("\nMatrice distances:\n");
    display_board(dist_board);

    printf("\nDémarrage de l'algorithme génétique...\n");
    start = clock();

    best_fitness = INT_MAX;

    for (run = 0; run < 3; run++) {
        solve_vrp(time_board, dist_board, &candidate);
        fitness = calculate_fitness(time_board, dist_board, &candidate);

        if (fitness < best_fitness) {
            best_solution = candidate;
            best_fitness = fitness;
        }
        printf("Execution %d: fitness=%lld\n", run+1, fitness);
    }

    end = clock();
    elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    printf("\nAlgorithme termine en %.2f secondes\n", elapsed);

    print_solution(&best_solution);
    write_solution("data/output.txt", &best_solution);

    /* Calcul des statistiques */
    total_distance_km = best_solution.total_distance / 1000.0f;
    fuel_consumption = total_distance_km * 6.5f / 100.0f; /* 6.5 L/100km */
    fuel_cost = fuel_consumption * 1.72f; /* 1.72 €/L */

    printf("\nStatistiques globales:\n");
    printf("Distance totale: %.2f km\n", total_distance_km);
    printf("Consommation carburant: %.2f L\n", fuel_consumption);
    printf("Coût carburant: %.2f €\n", fuel_cost);

    return EXIT_SUCCESS;
}