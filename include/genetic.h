#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"

#define POPULATION_SIZE 500
#define MAX_GENERATIONS 10000
#define MUTATION_RATE 0.2
#define CROSSOVER_RATE 0.9
#define TOURNAMENT_SIZE 7
#define STAGNATION_LIMIT 200
#define SERVICE_TIME 180
#define ELITE_SIZE (POPULATION_SIZE/10)

typedef struct {
    Solution solution;
    unsigned long long fitness;
} Individual;

typedef struct {
    Individual members[POPULATION_SIZE];
    int generation;
    Individual best_ever;
    int stagnation_count;
} Population;

/* Fonctions principales */
void init_population(Board time_board, Board dist_board, Population* pop);
void evolve_population(Board time_board, Board dist_board, Population* pop);
void solve_vrp(Board time_board, Board dist_board, Solution* best_solution);

/* Fonctions utilitaires */
unsigned long long calculate_fitness(Board time_board, Board dist_board, Solution* solution);
void print_solution(Solution* solution);
int route_duration(Board board, Route* route);
int route_distance(Board board, Route* route);
void repair_solution(Board time_board, Board dist_board, Solution* sol);
void remove_route_crossings(Board dist_board, Solution* sol);

/* Opérateurs génétiques */
Individual tournament_selection(Population* pop);
void crossover(Board time_board, Board dist_board, Individual* parent1, Individual* parent2, Individual* child);
void mutate(Board time_board, Board dist_board, Individual* indiv);

/* Construction initiale */
void build_initial_solution(Board time_board, Board dist_board, Solution* sol);
void nearest_neighbor_route(Board time_board, Board dist_board, Solution* sol, int* visited);

/* Fonctions de comparaison */
int compare_individuals(const void* a, const void* b);

#endif