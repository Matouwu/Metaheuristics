#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include <math.h>
#include "genetic.h"
#include "location.h"

// Fonction de comparaison pour le tri
int compare_individuals(const void* a, const void* b) {
    Individual* ia = (Individual*)a;
    Individual* ib = (Individual*)b;
    return (ia->fitness > ib->fitness) ? 1 : -1;
}

// Calcul de la durée d'une route
int route_duration(Board board, Route* route) {
    if (route->length == 0) return 0;

    int duration = board[DEPOT][route->path[0]];
    for (int i = 0; i < route->length - 1; i++) {
        duration += board[route->path[i]][route->path[i+1]] + SERVICE_TIME;
    }
    duration += board[route->path[route->length-1]][DEPOT];
    return duration;
}

// Calcul de la distance d'une route
int route_distance(Board board, Route* route) {
    if (route->length == 0) return 0;

    int distance = board[DEPOT][route->path[0]];
    for (int i = 0; i < route->length - 1; i++) {
        distance += board[route->path[i]][route->path[i+1]];
    }
    distance += board[route->path[route->length-1]][DEPOT];
    return distance;
}

// Fonction de fitness améliorée
unsigned long long calculate_fitness(Board time_board, Board dist_board, Solution* solution) {
    unsigned long long fitness = 0;
    unsigned long long penalty = 0;
    solution->total_duration = 0;
    solution->total_distance = 0;

    // Calcul des métriques et pénalités de temps
    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        route->duration = route_duration(time_board, route);
        route->distance = route_distance(dist_board, route);
        solution->total_duration += route->duration;
        solution->total_distance += route->distance;

        if (route->duration > MAX_TIME) {
            penalty += (route->duration - MAX_TIME) * 10000;
        }
    }

    // Vérification des villes visitées
    int visited[MAX_CITIES] = {0};
    visited[DEPOT] = 1;

    for (int i = 0; i < solution->num_vehicles; i++) {
        for (int j = 0; j < solution->routes[i].length; j++) {
            int city = solution->routes[i].path[j];
            if (visited[city] > 0) {
                penalty += PENALTY_PER_VIOLATION * 2;
            }
            visited[city]++;
        }
    }

    for (int i = 0; i < NUM_CITIES; i++) {
        if (!visited[i]) penalty += PENALTY_PER_VIOLATION;
    }

    fitness = solution->total_distance * 2 + solution->num_vehicles * 1500000 + penalty;
    return fitness;
}

// Initialisation d'une solution
void init_solution(Solution* solution) {
    solution->num_vehicles = 0;
    solution->total_duration = 0;
    solution->total_distance = 0;
    for (int i = 0; i < MAX_VEHICLES; i++) {
        solution->routes[i].length = 0;
        solution->routes[i].duration = 0;
        solution->routes[i].distance = 0;
        memset(solution->routes[i].path, -1, sizeof(solution->routes[i].path));
    }
}

// Construction d'une route avec l'heuristique du plus proche voisin
void nearest_neighbor_route(Board time_board, Board dist_board, Solution* sol, int* visited) {
    Route* route = &sol->routes[sol->num_vehicles];
    int current = DEPOT;
    int time_used = 0;

    while (1) {
        int best_city = -1;
        int best_time = INT_MAX;
        int best_dist = INT_MAX;

        for (int i = 0; i < NUM_CITIES; i++) {
            if (i == DEPOT || visited[i]) continue;

            int travel_time = time_board[current][i];
            int total_time = time_used + travel_time + SERVICE_TIME + time_board[i][DEPOT];
            int travel_dist = dist_board[current][i];

            if (total_time <= MAX_TIME && travel_dist < best_dist) {
                best_dist = travel_dist;
                best_time = travel_time;
                best_city = i;
            }
        }

        if (best_city == -1 || route->length >= MAX_ROUTE_LENGTH) break;

        route->path[route->length++] = best_city;
        time_used += time_board[current][best_city] + SERVICE_TIME;
        current = best_city;
        visited[best_city] = 1;
    }

    if (route->length > 0) {
        sol->num_vehicles++;
    }
}

// Construction de la solution initiale
void build_initial_solution(Board time_board, Board dist_board, Solution* sol) {
    init_solution(sol);
    int visited[MAX_CITIES] = {0};
    visited[DEPOT] = 1;

    // Créer des routes jusqu'à ce que toutes les villes soient visitées
    while (1) {
        int all_visited = 1;
        for (int i = 0; i < NUM_CITIES; i++) {
            if (!visited[i] && i != DEPOT) {
                all_visited = 0;
                break;
            }
        }
        if (all_visited || sol->num_vehicles >= MAX_VEHICLES) break;

        nearest_neighbor_route(time_board, dist_board, sol, visited);
    }

    repair_solution(time_board, dist_board, sol);
    remove_route_crossings(dist_board, sol);
    calculate_fitness(time_board, dist_board, sol);
}

// Réparation d'une solution
void repair_solution(Board time_board, Board dist_board, Solution* sol) {
    int visited[MAX_CITIES] = {0};
    visited[DEPOT] = 1;

    // Marquer les villes déjà visitées
    for (int i = 0; i < sol->num_vehicles; i++) {
        for (int j = 0; j < sol->routes[i].length; j++) {
            visited[sol->routes[i].path[j]] = 1;
        }
    }

    // Ajouter les villes manquantes
    for (int city = 0; city < NUM_CITIES; city++) {
        if (visited[city]) continue;

        int best_route = -1;
        int best_pos = -1;
        int best_cost = INT_MAX;

        for (int r = 0; r < sol->num_vehicles; r++) {
            Route* route = &sol->routes[r];

            for (int pos = 0; pos <= route->length; pos++) {
                int prev = (pos == 0) ? DEPOT : route->path[pos-1];
                int next = (pos == route->length) ? DEPOT : route->path[pos];

                int added_time = time_board[prev][city] + time_board[city][next] - time_board[prev][next] + SERVICE_TIME;
                int new_duration = route->duration + added_time;
                int added_dist = dist_board[prev][city] + dist_board[city][next] - dist_board[prev][next];

                if (new_duration <= MAX_TIME && added_dist < best_cost) {
                    best_cost = added_dist;
                    best_route = r;
                    best_pos = pos;
                }
            }
        }

        if (best_route != -1) {
            Route* route = &sol->routes[best_route];
            for (int i = route->length; i > best_pos; i--) {
                route->path[i] = route->path[i-1];
            }
            route->path[best_pos] = city;
            route->length++;
            route->duration += best_cost;
            visited[city] = 1;
        }
    }
}

// Suppression des croisements dans les routes
void remove_route_crossings(Board dist_board, Solution* sol) {
    for (int r = 0; r < sol->num_vehicles; r++) {
        Route* route = &sol->routes[r];

        for (int i = 0; i < route->length - 3; i++) {
            for (int j = i + 2; j < route->length - 1; j++) {
                int a = route->path[i];
                int b = route->path[i+1];
                int c = route->path[j];
                int d = route->path[j+1];

                int ab_cd = dist_board[a][c] + dist_board[b][d];
                int ac_bd = dist_board[a][b] + dist_board[c][d];

                if (ab_cd < ac_bd) {
                    int start = i+1;
                    int end = j;
                    while (start < end) {
                        int temp = route->path[start];
                        route->path[start] = route->path[end];
                        route->path[end] = temp;
                        start++;
                        end--;
                    }
                }
            }
        }
        route->distance = route_distance(dist_board, route);
    }
}

// Initialisation de la population
void init_population(Board time_board, Board dist_board, Population* pop) {
    pop->generation = 0;
    pop->stagnation_count = 0;

    for (int i = 0; i < POPULATION_SIZE; i++) {
        init_solution(&pop->members[i].solution);
        build_initial_solution(time_board, dist_board, &pop->members[i].solution);
        pop->members[i].fitness = calculate_fitness(time_board, dist_board, &pop->members[i].solution);

        if (i == 0 || pop->members[i].fitness < pop->best_ever.fitness) {
            pop->best_ever = pop->members[i];
        }
    }

    qsort(pop->members, POPULATION_SIZE, sizeof(Individual), compare_individuals);
}

// Sélection par tournoi
Individual tournament_selection(Population* pop) {
    Individual best = pop->members[rand() % POPULATION_SIZE];

    for (int i = 1; i < TOURNAMENT_SIZE; i++) {
        Individual contender = pop->members[rand() % POPULATION_SIZE];
        if (contender.fitness < best.fitness) {
            best = contender;
        }
    }
    return best;
}

// Croisement amélioré
void crossover(Board time_board, Board dist_board, Individual* parent1, Individual* parent2, Individual* child) {
    init_solution(&child->solution);

    // Sélection aléatoire d'un segment du parent1
    int route1 = rand() % parent1->solution.num_vehicles;
    Route* p1_route = &parent1->solution.routes[route1];
    int start = (p1_route->length > 0) ? rand() % p1_route->length : 0;
    int end = (p1_route->length > 0) ? start + rand() % (p1_route->length - start) : 0;

    // Copie du segment dans l'enfant
    Route* child_route = &child->solution.routes[0];
    for (int i = start; i <= end && child_route->length < MAX_ROUTE_LENGTH; i++) {
        child_route->path[child_route->length++] = p1_route->path[i];
    }
    child->solution.num_vehicles = 1;

    // Ajout des villes manquantes du parent2
    int visited[MAX_CITIES] = {0};
    for (int i = 0; i < child_route->length; i++) {
        visited[child_route->path[i]] = 1;
    }

    for (int r = 0; r < parent2->solution.num_vehicles; r++) {
        Route* p2_route = &parent2->solution.routes[r];
        for (int i = 0; i < p2_route->length; i++) {
            int city = p2_route->path[i];
            if (!visited[city]) {
                // Trouver la meilleure position d'insertion
                int best_route = -1, best_pos = -1;
                int best_cost = INT_MAX;

                for (int cr = 0; cr < child->solution.num_vehicles; cr++) {
                    Route* c_route = &child->solution.routes[cr];
                    for (int pos = 0; pos <= c_route->length; pos++) {
                        int prev = (pos == 0) ? DEPOT : c_route->path[pos-1];
                        int next = (pos == c_route->length) ? DEPOT : c_route->path[pos];

                        int added_time = time_board[prev][city] + time_board[city][next] - time_board[prev][next] + SERVICE_TIME;
                        int new_duration = route_duration(time_board, c_route) + added_time;
                        int added_dist = dist_board[prev][city] + dist_board[city][next] - dist_board[prev][next];

                        if (new_duration <= MAX_TIME && added_dist < best_cost) {
                            best_cost = added_dist;
                            best_route = cr;
                            best_pos = pos;
                        }
                    }
                }

                if (best_route != -1) {
                    Route* c_route = &child->solution.routes[best_route];
                    for (int j = c_route->length; j > best_pos; j--) {
                        c_route->path[j] = c_route->path[j-1];
                    }
                    c_route->path[best_pos] = city;
                    c_route->length++;
                    visited[city] = 1;
                } else if (child->solution.num_vehicles < MAX_VEHICLES) {
                    Route* new_route = &child->solution.routes[child->solution.num_vehicles++];
                    new_route->path[new_route->length++] = city;
                    visited[city] = 1;
                }
            }
        }
    }

    repair_solution(time_board, dist_board, &child->solution);
    remove_route_crossings(dist_board, &child->solution);
    child->fitness = calculate_fitness(time_board, dist_board, &child->solution);
}

// Mutation améliorée
void mutate(Board time_board, Board dist_board, Individual* indiv) {
    if ((double)rand() / RAND_MAX < MUTATION_RATE) {
        int mutation_type = rand() % 5;

        switch(mutation_type) {
            case 0: { // Déplacement d'une ville
                int city;
                do {
                    city = rand() % NUM_CITIES;
                } while (city == DEPOT);

                int src_route = -1, src_idx = -1;
                for (int r = 0; r < indiv->solution.num_vehicles; r++) {
                    for (int i = 0; i < indiv->solution.routes[r].length; i++) {
                        if (indiv->solution.routes[r].path[i] == city) {
                            src_route = r;
                            src_idx = i;
                            break;
                        }
                    }
                    if (src_route != -1) break;
                }
                if (src_route == -1) return;

                Route* route = &indiv->solution.routes[src_route];
                for (int i = src_idx; i < route->length - 1; i++) {
                    route->path[i] = route->path[i+1];
                }
                route->length--;

                int best_route = -1, best_pos = -1, best_cost = INT_MAX;
                for (int r = 0; r < indiv->solution.num_vehicles; r++) {
                    if (r == src_route && route->length == 0) continue;

                    for (int pos = 0; pos <= indiv->solution.routes[r].length; pos++) {
                        int prev = (pos == 0) ? DEPOT : indiv->solution.routes[r].path[pos-1];
                        int next = (pos == indiv->solution.routes[r].length) ? DEPOT : indiv->solution.routes[r].path[pos];

                        int added_time = time_board[prev][city] + time_board[city][next] - time_board[prev][next] + SERVICE_TIME;
                        int new_duration = indiv->solution.routes[r].duration + added_time;
                        int added_dist = dist_board[prev][city] + dist_board[city][next] - dist_board[prev][next];

                        if (new_duration <= MAX_TIME && added_dist < best_cost) {
                            best_cost = added_dist;
                            best_route = r;
                            best_pos = pos;
                        }
                    }
                }

                if (best_route != -1) {
                    Route* dest_route = &indiv->solution.routes[best_route];
                    for (int i = dest_route->length; i > best_pos; i--) {
                        dest_route->path[i] = dest_route->path[i-1];
                    }
                    dest_route->path[best_pos] = city;
                    dest_route->length++;
                    dest_route->duration += best_cost;
                } else {
                    route->path[route->length++] = city;
                }
                break;
            }

            case 1: { // Échange de deux villes
                int city1, city2;
                do {
                    city1 = rand() % NUM_CITIES;
                    city2 = rand() % NUM_CITIES;
                } while (city1 == DEPOT || city2 == DEPOT || city1 == city2);

                int route1 = -1, idx1 = -1, route2 = -1, idx2 = -1;
                for (int r = 0; r < indiv->solution.num_vehicles; r++) {
                    for (int i = 0; i < indiv->solution.routes[r].length; i++) {
                        if (indiv->solution.routes[r].path[i] == city1) {
                            route1 = r;
                            idx1 = i;
                        }
                        if (indiv->solution.routes[r].path[i] == city2) {
                            route2 = r;
                            idx2 = i;
                        }
                    }
                }

                if (route1 != -1 && route2 != -1) {
                    indiv->solution.routes[route1].path[idx1] = city2;
                    indiv->solution.routes[route2].path[idx2] = city1;
                }
                break;
            }

            case 2: { // Inversion de segment (2-opt)
                if (indiv->solution.num_vehicles > 0) {
                    int r = rand() % indiv->solution.num_vehicles;
                    Route* route = &indiv->solution.routes[r];

                    if (route->length >= 4) {
                        int i = 1 + rand() % (route->length - 2);
                        int j = i + 1 + rand() % (route->length - i - 1);

                        while (i < j) {
                            int temp = route->path[i];
                            route->path[i] = route->path[j];
                            route->path[j] = temp;
                            i++;
                            j--;
                        }

                        route->duration = route_duration(time_board, route);
                        route->distance = route_distance(dist_board, route);
                    }
                }
                break;
            }

            case 3: { // Échange de segments entre routes
                if (indiv->solution.num_vehicles >= 2) {
                    int r1 = rand() % indiv->solution.num_vehicles;
                    int r2 = rand() % indiv->solution.num_vehicles;
                    if (r1 == r2) break;

                    Route* route1 = &indiv->solution.routes[r1];
                    Route* route2 = &indiv->solution.routes[r2];
                    if (route1->length == 0 || route2->length == 0) break;

                    int i = rand() % route1->length;
                    int j = rand() % route2->length;
                    int len1 = 1 + rand() % (route1->length - i);
                    int len2 = 1 + rand() % (route2->length - j);

                    // Échanger les segments
                    for (int k = 0; k < len1 && k < len2; k++) {
                        int temp = route1->path[i+k];
                        route1->path[i+k] = route2->path[j+k];
                        route2->path[j+k] = temp;
                    }

                    route1->duration = route_duration(time_board, route1);
                    route1->distance = route_distance(dist_board, route1);
                    route2->duration = route_duration(time_board, route2);
                    route2->distance = route_distance(dist_board, route2);
                }
                break;
            }

            case 4: { // Suppression de route vide
                for (int r = 0; r < indiv->solution.num_vehicles; r++) {
                    if (indiv->solution.routes[r].length == 0) {
                        for (int i = r; i < indiv->solution.num_vehicles - 1; i++) {
                            indiv->solution.routes[i] = indiv->solution.routes[i+1];
                        }
                        indiv->solution.num_vehicles--;
                        break;
                    }
                }
                break;
            }
        }

        repair_solution(time_board, dist_board, &indiv->solution);
        remove_route_crossings(dist_board, &indiv->solution);
        indiv->fitness = calculate_fitness(time_board, dist_board, &indiv->solution);
    }
}

// Évolution de la population
void evolve_population(Board time_board, Board dist_board, Population* pop) {
    Population new_pop;
    new_pop.generation = pop->generation + 1;

    // Élitisme: conserver les meilleurs individus
    for (int i = 0; i < ELITE_SIZE; i++) {
        new_pop.members[i] = pop->members[i];
    }

    // Remplir le reste de la population
    for (int i = ELITE_SIZE; i < POPULATION_SIZE; i++) {
        Individual parent1 = tournament_selection(pop);
        Individual parent2 = tournament_selection(pop);
        Individual child;

        if ((double)rand() / RAND_MAX < CROSSOVER_RATE) {
            crossover(time_board, dist_board, &parent1, &parent2, &child);
        } else {
            child = parent1;
        }

        mutate(time_board, dist_board, &child);
        new_pop.members[i] = child;
    }

    // Trier la population par fitness
    qsort(new_pop.members, POPULATION_SIZE, sizeof(Individual), compare_individuals);

    // Mettre à jour la meilleure solution
    new_pop.best_ever = new_pop.members[0];
    if (new_pop.best_ever.fitness < pop->best_ever.fitness) {
        new_pop.stagnation_count = 0;
    } else {
        new_pop.stagnation_count = pop->stagnation_count + 1;
    }

    *pop = new_pop;
}

// Affichage d'une solution
void print_solution(Solution* solution) {
    printf("\nSolution optimale:\n");
    printf("Véhicules utilisés: %d\n", solution->num_vehicles);
    printf("Durée totale: %d secondes\n", solution->total_duration);
    printf("Distance totale: %d mètres\n", solution->total_distance);

    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        printf("Véhicule %d (%ds, %dm): Depot", i+1, route->duration, route->distance);
        for (int j = 0; j < route->length; j++) {
            printf(" -> %d", route->path[j]);
        }
        printf(" -> Depot\n");
    }
}

// Résolution du VRP
void solve_vrp(Board time_board, Board dist_board, Solution* best_solution) {
    srand(time(NULL));
    Population pop;
    init_population(time_board, dist_board, &pop);

    for (int gen = 0; gen < MAX_GENERATIONS; gen++) {
        evolve_population(time_board, dist_board, &pop);

        if (gen % 100 == 0) {
            printf("Generation %d: Fitness=%lld Vehicules=%d Duree=%d Distance=%d\n",
                   gen, pop.best_ever.fitness,
                   pop.best_ever.solution.num_vehicles,
                   pop.best_ever.solution.total_duration,
                   pop.best_ever.solution.total_distance);
        }

        if (pop.stagnation_count >= STAGNATION_LIMIT) {
            printf("Arret premature a la generation %d (stagnation)\n", gen);
            break;
        }
    }

    *best_solution = pop.best_ever.solution;
}