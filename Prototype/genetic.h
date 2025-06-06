#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"

#define POPULATION_SIZE 500
#define MAX_GENERATIONS 1000
#define MUTATION_RATE 0.20
#define CROSSOVER_RATE 0.85
#define TOURNAMENT_SIZE 7
#define STAGNATION_LIMIT 100
#define MAX_TRIALS 50 // Tentatives pour réparer les solutions

typedef struct {
    Solution solution;
    int fitness;
} Individual;

typedef struct {
    Individual members[POPULATION_SIZE];
    int generation;
    Individual best_ever;
    int stagnation_count;
} Population;

int calculate_fitness(Board board, Solution* solution);
void init_solution(Solution* solution);
void build_initial_solution(Board board, Solution* sol);
void init_population(Board board, Population* pop);
Individual tournament_selection(Population* pop);
void evolve_population(Board board, Population* pop);
void print_solution(Solution* solution);
void solve_vrp(Board board, Solution* best_solution);

// Opérateurs de mutation
void mutate_move_city(Board board, Individual* indiv);
void mutate_swap_cities(Individual* indiv);
void mutate_2opt_route(Board board, Route* route);
void mutate(Board board, Individual* indiv);

// Croisement
void crossover(Board board, Individual* parent1, Individual* parent2, Individual* child);

// Fonctions utilitaires
int find_city_in_solution(Solution* sol, int city);
int is_valid_city(int city);
void repair_solution(Board board, Solution* sol);
int route_duration(Board board, Route* route);

#endif /* GENETIC_H */