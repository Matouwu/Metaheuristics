#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"
#include "inout.h"
#include "graphic.h"

#define POPULATION_SIZE 1000
#define MAX_GENERATIONS 200
#define TOURNAMENT_SIZE 50
#define MUTATION_RATE 0.2
#define CROSSOVER_RATE 0.8

typedef struct {
    Path path;
    int fitness;
} Individual;

typedef struct {
    Individual members[POPULATION_SIZE];
    int generation;
    Individual best_ever;
} Population;

int calcul_fitness(Board board, Path path);
void randomize_path(Board board, Path path);
void init_path(Path path);

void init_population(Board board, Population *pop);
void evolve_population(Board board, Population *pop);
Individual tournament_selection(Population *pop);
void crossover(Individual *parent1, Individual *parent2, Individual *child1, Individual *child2);
void mutate(Board board, Individual *individual);
void copy_path(Path source, Path destination);
void print_path(Path path);
Individual find_best_individual(Population *pop);
int path_contains(Path path, int city, int length);
void get_best_path(Board board, Path best_path, int max_iterations);

#endif /* GENETIC_H */