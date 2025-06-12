#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"

#define POPULATION_SIZE 200
#define MAX_GENERATIONS 5000
#define MUTATION_RATE 0.15
#define CROSSOVER_RATE 0.85
#define TOURNAMENT_SIZE 5
#define STAGNATION_LIMIT 500

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

// Fonctions principales
void init_population(Board board, Population* pop);
void evolve_population(Board board, Population* pop);
void solve_vrp(Board board, Solution* best_solution);

// Fonctions utilitaires
unsigned long long calculate_fitness(Board board, Solution* solution);
void print_solution(Solution* solution);
int route_duration(Board board, Route* route);
void repair_solution(Board board, Solution* sol);

// Opérateurs génétiques
Individual tournament_selection(Population* pop);
void crossover(Board board, Individual* parent1, Individual* parent2, Individual* child);
void mutate(Board board, Individual* indiv);

// Construction initiale
void build_initial_solution(Board board, Solution* sol);

#endif