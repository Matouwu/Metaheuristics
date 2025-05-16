#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "genetic.h"
#include "location.h"

#define NUM_CITIES 85

/* Fonction de calcul du fitness (utilise votre matrice asymétrique) */
int calculate_fitness(Board board, Path path) {
    int total = 0;
    int i;

    /* Calcul du temps pour tout le parcours */
    for (i = 0; i < NUM_CITIES-1; i++) {
        total += board[path[i]][path[i+1]];
    }

    /* Optionnel : retour au départ */
     total += board[path[NUM_CITIES-1]][path[0]];

    return total;
}

/* Initialisation aléatoire d'un chemin */
void init_path(Path path) {
    int i;

    /* Création d'un chemin ordonné */
    for (i = 0; i < NUM_CITIES; i++) {
        path[i] = i;
    }

    /* Mélange aléatoire */
    for (i = NUM_CITIES-1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = path[i];
        path[i] = path[j];
        path[j] = temp;
    }
}

/* Initialisation de la population */
void init_population(Board board, Population *pop) {
    int i;

    pop->generation = 0;

    for (i = 0; i < POPULATION_SIZE; i++) {
        init_path(pop->members[i].path);
        pop->members[i].fitness = calculate_fitness(board, pop->members[i].path);
    }

    /* Initialisation du meilleur individu */
    pop->best_ever = pop->members[0];
    for (i = 1; i < POPULATION_SIZE; i++) {
        if (pop->members[i].fitness < pop->best_ever.fitness) {
            pop->best_ever = pop->members[i];
        }
    }
}

/* Sélection par tournoi */
Individual tournament_selection(Population *pop) {
    int i;
    Individual best = pop->members[rand() % POPULATION_SIZE];

    for (i = 1; i < TOURNAMENT_SIZE; i++) {
        Individual contender = pop->members[rand() % POPULATION_SIZE];
        if (contender.fitness < best.fitness) {
            best = contender;
        }
    }

    return best;
}

/* Croisement OX pour TSP asymétrique */
void asymmetric_crossover(Board board, Individual *parent1, Individual *parent2, Individual *child) {
    int start = rand() % NUM_CITIES;
    int end = rand() % NUM_CITIES;
    int i, j, pos;

    if (start > end) {
        int temp = start;
        start = end;
        end = temp;
    }

    /* Initialisation à -1 */
    for (i = 0; i < NUM_CITIES; i++) {
        child->path[i] = -1;
    }

    /* Copie de la section sélectionnée */
    for (i = start; i <= end; i++) {
        child->path[i] = parent1->path[i];
    }

    /* Remplissage avec parent2 en évitant les doublons */
    pos = (end + 1) % NUM_CITIES;
    for (i = 0; i < NUM_CITIES; i++) {
        int city = parent2->path[(end + 1 + i) % NUM_CITIES];
        int exists = 0;

        /* Vérifier si la ville existe déjà */
        for (j = 0; j < NUM_CITIES; j++) {
            if (child->path[j] == city) {
                exists = 1;
                break;
            }
        }

        if (!exists) {
            child->path[pos] = city;
            pos = (pos + 1) % NUM_CITIES;
        }
    }

    /* Calcul du nouveau fitness */
    child->fitness = calculate_fitness(board, child->path);
}

/* Mutation par inversion (2-opt adapté) */
void mutate(Board board, Individual *indiv) {
    if ((double)rand() / RAND_MAX < MUTATION_RATE) {
        int pos1 = rand() % NUM_CITIES;
        int pos2 = rand() % NUM_CITIES;
        int temp;

        if (pos1 > pos2) {
            int temp_pos = pos1;
            pos1 = pos2;
            pos2 = temp_pos;
        }

        /* Inversion de la sous-séquence */
        while (pos1 < pos2) {
            temp = indiv->path[pos1];
            indiv->path[pos1] = indiv->path[pos2];
            indiv->path[pos2] = temp;
            pos1++;
            pos2--;
        }

        /* Recalcul du fitness */
        indiv->fitness = calculate_fitness(board, indiv->path);
    }
}

/* Evolution de la population */
void evolve_population(Board board, Population *pop) {
    Population new_pop;
    int i;

    new_pop.generation = pop->generation + 1;

    /* Élitisme: conserver le meilleur */
    new_pop.members[0] = pop->best_ever;

    for (i = 1; i < POPULATION_SIZE; i++) {
        Individual parent1 = tournament_selection(pop);
        Individual parent2 = tournament_selection(pop);
        Individual child;

        if ((double)rand() / RAND_MAX < CROSSOVER_RATE) {
            asymmetric_crossover(board, &parent1, &parent2, &child);
        } else {
            /* Reproduction asexuée */
            child = parent1;
        }

        mutate(board, &child);
        new_pop.members[i] = child;
    }

    /* Trouver le nouveau meilleur */
    new_pop.best_ever = new_pop.members[0];
    for (i = 1; i < POPULATION_SIZE; i++) {
        if (new_pop.members[i].fitness < new_pop.best_ever.fitness) {
            new_pop.best_ever = new_pop.members[i];
        }
    }

    /* Mise à jour de la population */
    *pop = new_pop;
}

void print_path(Path path) {
    printf("Path: ");

    int i;
    for(i = 0; i < 85; i++) {
        printf("%d ", path[i]);
    }
    printf("\n");
}

/* Fonction principale */
void solve_tsp(Board board, Path best_solution, int *best_fitness) {
    srand(time(NULL));

    Population pop;
    int i;

    init_population(board, &pop);

    for (i = 0; i < MAX_GENERATIONS; i++) {
        evolve_population(board, &pop);

        if (i % 10 == 0) {
            printf("Generation %d: Best fitness = %d\n", i, pop.best_ever.fitness);
        }
    }

    /* Retourne la meilleure solution */
    memcpy(best_solution, pop.best_ever.path, sizeof(Path));
    *best_fitness = pop.best_ever.fitness;
}