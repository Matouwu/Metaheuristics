#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "genetic.h"

int calcul_fitness(Board board, Path path) {
    int fitness = 0;
    int i;
    for(i = 0; i < 84; i++) {
        fitness += board[path[i]][path[i+1]];
    }
    fitness += board[path[84]][path[0]];
    return fitness;
}

void init_path(Path path) {
    int i;
    for(i = 0; i < 85; i++) {
        path[i] = i;
    }
}

void randomize_path(Board board, Path path) {
    int i;
    for(i = 0; i < 1000; i++) {
        int a = (rand() % 84) + 1;
        int b = (rand() % 84) + 1;

        int temp = path[a];
        path[a] = path[b];
        path[b] = temp;
    }
}

void copy_path(Path source, Path destination) {
    memcpy(destination, source, sizeof(Path));
}

void init_population(Board board, Population *pop) {
    pop->generation = 0;

	int i;
    for(i = 0; i < POPULATION_SIZE; i++) {
        init_path(pop->members[i].path);
        randomize_path(board, pop->members[i].path);
        pop->members[i].fitness = calcul_fitness(board, pop->members[i].path);
    }

    pop->best_ever = find_best_individual(pop);
}

Individual find_best_individual(Population *pop) {
    Individual best = pop->members[0];

	int i;
    for(i = 1; i < POPULATION_SIZE; i++) {
        if(pop->members[i].fitness < best.fitness) {
            best = pop->members[i];
        }
    }

    return best;
}

Individual tournament_selection(Population *pop) {
    Individual best = pop->members[rand() % POPULATION_SIZE];

	int i;
    for(i = 1; i < TOURNAMENT_SIZE; i++) {
        Individual contestant = pop->members[rand() % POPULATION_SIZE];
        if(contestant.fitness < best.fitness) {
            best = contestant;
        }
    }

    return best;
}

int path_contains(Path path, int city, int length) {
    int i;
    for(i = 0; i < length; i++) {
        if(path[i] == city) {
            return 1;
        }
    }
    return 0;
}

void crossover(Individual *parent1, Individual *parent2, Individual *child1, Individual *child2) {
	int i;
    for(i = 0; i < 85; i++) {
        child1->path[i] = -1;
        child2->path[i] = -1;
    }

    child1->path[0] = 0;
    child2->path[0] = 0;

    int start = 1 + rand() % 83;
    int end = 1 + rand() % 83;

    if(start > end) {
        int temp = start;
        start = end;
        end = temp;
    }

    for(i = start; i <= end; i++) {
        child1->path[i] = parent1->path[i];
        child2->path[i] = parent2->path[i];
    }

    int current_p2_pos = 1;
    for(i = 1; i < 85; i++) {
        if(i >= start && i <= end) continue;

        while(path_contains(child1->path, parent2->path[current_p2_pos], 85) && current_p2_pos < 85) {
            current_p2_pos++;
        }

        if(current_p2_pos < 85) {
            child1->path[i] = parent2->path[current_p2_pos];
            current_p2_pos++;
        }
    }

    int current_p1_pos = 1;
    for(i = 1; i < 85; i++) {
        if(i >= start && i <= end) continue;

        while(path_contains(child2->path, parent1->path[current_p1_pos], 85) && current_p1_pos < 85) {
            current_p1_pos++;
        }

        if(current_p1_pos < 85) {
            child2->path[i] = parent1->path[current_p1_pos];
            current_p1_pos++;
        }
    }

    child1->fitness = 0;
    child2->fitness = 0;
}

void mutate(Board board, Individual *individual) {
    if((double)rand() / RAND_MAX < MUTATION_RATE) {
        int pos1 = 1 + rand() % 84;
        int pos2 = 1 + rand() % 84;

        int temp = individual->path[pos1];
        individual->path[pos1] = individual->path[pos2];
        individual->path[pos2] = temp;

        individual->fitness = calcul_fitness(board, individual->path);
    }
}

void evolve_population(Board board, Population *pop) {
    Population new_pop;
    new_pop.generation = pop->generation + 1;

    new_pop.members[0] = pop->best_ever;

	int i;
    for(i = 1; i < POPULATION_SIZE; i += 2) {
        Individual parent1 = tournament_selection(pop);
        Individual parent2 = tournament_selection(pop);

        Individual child1, child2;

        if((double)rand() / RAND_MAX < CROSSOVER_RATE) {
            crossover(&parent1, &parent2, &child1, &child2);
        } else {
            copy_path(parent1.path, child1.path);
            copy_path(parent2.path, child2.path);
            child1.fitness = parent1.fitness;
            child2.fitness = parent2.fitness;
        }

        mutate(board, &child1);
        mutate(board, &child2);

        child1.fitness = calcul_fitness(board, child1.path);
        child2.fitness = calcul_fitness(board, child2.path);

        new_pop.members[i] = child1;
        if(i + 1 < POPULATION_SIZE) {
            new_pop.members[i + 1] = child2;
        }
    }

    *pop = new_pop;

    Individual best_current = find_best_individual(pop);
    if(best_current.fitness < pop->best_ever.fitness) {
        pop->best_ever = best_current;
    }
}

void print_path(Path path) {
    printf("Path: ");

	int i;
    for(i = 0; i < 85; i++) {
        printf("%d ", path[i]);
    }
    printf("\n");
}

void get_best_path(Board board, Path best_path, int max_iterations) {
    srand(time(NULL));

    Population pop;
    init_population(board, &pop);

    printf("Initial best fitness: %d\n", pop.best_ever.fitness);

	int i;
    for(i = 0; i < max_iterations; i++) {
        evolve_population(board, &pop);

        if(i % 5 == 0) {
            printf("Generation %d: Best fitness = %d\n",
                   pop.generation, pop.best_ever.fitness);
        }
    }

    printf("Final best fitness: %d\n", pop.best_ever.fitness);

    copy_path(pop.best_ever.path, best_path);
}