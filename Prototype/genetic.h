#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"
#include "inout.h"
#include "graphic.h"

#define POPULATION_SIZE 500
#define MAX_GENERATIONS 1000
#define MUTATION_RATE 0.20
#define CROSSOVER_RATE 0.85
#define TOURNAMENT_SIZE 7
#define STAGNATION_LIMIT 100

typedef struct {
    Path path;
    int fitness;
} Individual;

typedef struct {
    Individual members[POPULATION_SIZE];
    int generation;
    Individual best_ever;
    int stagnation_count;
} Population;

int calculate_fitness(Board board, Path path);
void init_path(Path path);
void randomize_path(Board board, Path path);
void init_population(Board board, Population *pop);

Individual tournament_selection(Population *pop);
Individual find_best_individual(Population *pop);
void evolve_population(Board board, Population *pop);

void crossover(Individual *parent1, Individual *parent2, Individual *child1, Individual *child2);
void mutate(Board board, Individual *individual);
void copy_path(Path source, Path destination);

void print_path(Path path);
int path_contains(Path path, int city, int length);
int is_valid_path(Path path);

void solve_tsp(Board board, Path best_solution, int *best_fitness);

#endif /* GENETIC_H */