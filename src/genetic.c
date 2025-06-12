#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include "genetic.h"

#include <stdint.h>

// Calcul de la durée d'une route
int route_duration(Board board, Route* route) {
    if (route->length == 0) return 0;

    int duration = board[DEPOT][route->path[0]];
    for (int i = 0; i < route->length - 1; i++) {
        duration += board[route->path[i]][route->path[i+1]];
    }
    duration += board[route->path[route->length-1]][DEPOT];
    return duration;
}

// Calcul du fitness
unsigned long long calculate_fitness(Board board, Solution* solution) {
    unsigned long long fitness = 0;
    unsigned long long penalty = 0;
    solution->total_duration = 0;

    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        route->duration = route_duration(board, route);
        solution->total_duration += route->duration;

        // Pénalités pour contraintes violées
        if (route->duration > MAX_TIME) {
            penalty += (route->duration - MAX_TIME) * 1000;
        }
    }

    // Pénalité pour villes non visitées
    int visited[NUM_CITIES] = {0};
    visited[DEPOT] = 1;
    for (int i = 0; i < solution->num_vehicles; i++) {
        for (int j = 0; j < solution->routes[i].length; j++) {
            visited[solution->routes[i].path[j]] = 1;
        }
    }
    for (int i = 0; i < NUM_CITIES; i++) {
        if (!visited[i]) penalty += PENALTY_PER_VIOLATION;
    }

    fitness = solution->total_duration + solution->num_vehicles * 1000000 + penalty;
    return fitness;
}

// Initialisation d'une solution vide
void init_solution(Solution* solution) {
    solution->num_vehicles = 0;
    solution->total_duration = 0;
    for (int i = 0; i < MAX_VEHICLES; i++) {
        solution->routes[i].length = 0;
        solution->routes[i].duration = 0;
        memset(solution->routes[i].path, -1, sizeof(solution->routes[i].path));
    }
}

// Construction d'une solution initiale
void build_initial_solution(Board board, Solution* sol) {
    init_solution(sol);

    int visited[NUM_CITIES] = {0};
    visited[DEPOT] = 1;

    int unvisited_count = NUM_CITIES - 1;
    int unvisited[NUM_CITIES];
    for (int i = 0, j = 0; i < NUM_CITIES; i++) {
        if (i != DEPOT) unvisited[j++] = i;
    }

    // Mélanger les villes
    for (int i = unvisited_count - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = unvisited[i];
        unvisited[i] = unvisited[j];
        unvisited[j] = temp;
    }

    // Construction des routes
    while (unvisited_count > 0) {
        if (sol->num_vehicles >= MAX_VEHICLES) break;

        Route* route = &sol->routes[sol->num_vehicles];
        int current = DEPOT;
        int time_used = 0;
        int route_full = 0;

        while (!route_full && unvisited_count > 0) {
            int best_city = -1;
            int best_time = INT_MAX;

            // Trouver la ville non visitée la plus proche
            for (int i = 0; i < unvisited_count; i++) {
                int city = unvisited[i];
                int travel_time = board[current][city];
                int return_time = board[city][DEPOT];

                if (time_used + travel_time + return_time <= MAX_TIME && travel_time < best_time) {
                    best_time = travel_time;
                    best_city = i;
                }
            }

            if (best_city == -1) {
                route_full = 1;
            } else {
                int city = unvisited[best_city];
                route->path[route->length++] = city;
                time_used += board[current][city];
                current = city;
                visited[city] = 1;

                // Retirer de la liste des non visités
                unvisited[best_city] = unvisited[--unvisited_count];
            }
        }

        sol->num_vehicles++;
    }

    // Réparer les villes manquantes
    repair_solution(board, sol);
    calculate_fitness(board, sol);
}

// Réparation de solution
void repair_solution(Board board, Solution* sol) {
    int visited[NUM_CITIES] = {0};
    visited[DEPOT] = 1;

    // Marquer les villes visitées
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

                int added_time = board[prev][city] + board[city][next] - board[prev][next];
                int new_duration = route->duration + added_time;

                if (new_duration <= MAX_TIME && added_time < best_cost) {
                    best_cost = added_time;
                    best_route = r;
                    best_pos = pos;
                }
            }
        }

        if (best_route != -1) {
            Route* route = &sol->routes[best_route];

            // Décalage des éléments
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

// Initialisation de la population
void init_population(Board board, Population* pop) {
    pop->generation = 0;
    pop->stagnation_count = 0;

    for (int i = 0; i < POPULATION_SIZE; i++) {
        init_solution(&pop->members[i].solution);
        build_initial_solution(board, &pop->members[i].solution);
        pop->members[i].fitness = calculate_fitness(board, &pop->members[i].solution);

        if (i == 0 || pop->members[i].fitness < pop->best_ever.fitness) {
            pop->best_ever = pop->members[i];
        }
    }
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

// Croisement OX
void crossover(Board board, Individual* parent1, Individual* parent2, Individual* child) {
    init_solution(&child->solution);

    // Choisir une route aléatoire du parent1
    int route_idx = rand() % parent1->solution.num_vehicles;
    Route* p1_route = &parent1->solution.routes[route_idx];

    // Copier cette route dans l'enfant
    Route* child_route = &child->solution.routes[0];
    memcpy(child_route->path, p1_route->path, p1_route->length * sizeof(int));
    child_route->length = p1_route->length;
    child_route->duration = p1_route->duration;
    child->solution.num_vehicles = 1;

    // Marquer les villes copiées
    int visited[NUM_CITIES] = {0};
    for (int i = 0; i < child_route->length; i++) {
        visited[child_route->path[i]] = 1;
    }

    // Ajouter les villes manquantes depuis parent2
    for (int r = 0; r < parent2->solution.num_vehicles; r++) {
        Route* p2_route = &parent2->solution.routes[r];

        for (int i = 0; i < p2_route->length; i++) {
            int city = p2_route->path[i];

            if (!visited[city]) {
                int best_route = -1;
                int best_pos = -1;
                int best_cost = INT_MAX;

                // Trouver la meilleure position dans les routes existantes
                for (int cr = 0; cr < child->solution.num_vehicles; cr++) {
                    Route* c_route = &child->solution.routes[cr];

                    for (int pos = 0; pos <= c_route->length; pos++) {
                        int prev = (pos == 0) ? DEPOT : c_route->path[pos-1];
                        int next = (pos == c_route->length) ? DEPOT : c_route->path[pos];

                        int added_time = board[prev][city] + board[city][next] - board[prev][next];
                        int new_duration = c_route->duration + added_time;

                        if (new_duration <= MAX_TIME && added_time < best_cost) {
                            best_cost = added_time;
                            best_route = cr;
                            best_pos = pos;
                        }
                    }
                }

                // Créer une nouvelle route si nécessaire
                if (best_route == -1 && child->solution.num_vehicles < MAX_VEHICLES) {
                    best_route = child->solution.num_vehicles++;
                    Route* new_route = &child->solution.routes[best_route];
                    new_route->path[0] = city;
                    new_route->length = 1;
                    new_route->duration = board[DEPOT][city] + board[city][DEPOT];
                    visited[city] = 1;
                }
                // Insérer dans une route existante
                else if (best_route != -1) {
                    Route* c_route = &child->solution.routes[best_route];

                    // Décalage des éléments
                    for (int j = c_route->length; j > best_pos; j--) {
                        c_route->path[j] = c_route->path[j-1];
                    }

                    c_route->path[best_pos] = city;
                    c_route->length++;
                    c_route->duration += best_cost;
                    visited[city] = 1;
                }
            }
        }
    }

    repair_solution(board, &child->solution);
    child->fitness = calculate_fitness(board, &child->solution);
}

// Mutation
void mutate(Board board, Individual* indiv) {
    if ((double)rand() / RAND_MAX < MUTATION_RATE) {
        int mutation_type = rand() % 3;

        switch(mutation_type) {
            case 0: // Déplacement de ville
            {
                // Choisir une ville aléatoire
                int city;
                do {
                    city = rand() % NUM_CITIES;
                } while (city == DEPOT);

                // Trouver sa position actuelle
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

                // Retirer la ville
                Route* route = &indiv->solution.routes[src_route];
                for (int i = src_idx; i < route->length - 1; i++) {
                    route->path[i] = route->path[i+1];
                }
                route->length--;

                // Trouver une nouvelle position
                int best_route = -1, best_pos = -1, best_cost = INT_MAX;
                for (int r = 0; r < indiv->solution.num_vehicles; r++) {
                    if (r == src_route && route->length == 0) continue;

                    for (int pos = 0; pos <= indiv->solution.routes[r].length; pos++) {
                        int prev = (pos == 0) ? DEPOT : indiv->solution.routes[r].path[pos-1];
                        int next = (pos == indiv->solution.routes[r].length) ? DEPOT : indiv->solution.routes[r].path[pos];

                        int added_time = board[prev][city] + board[city][next] - board[prev][next];
                        int new_duration = indiv->solution.routes[r].duration + added_time;

                        if (new_duration <= MAX_TIME && added_time < best_cost) {
                            best_cost = added_time;
                            best_route = r;
                            best_pos = pos;
                        }
                    }
                }

                // Insérer à la nouvelle position
                if (best_route != -1) {
                    Route* dest_route = &indiv->solution.routes[best_route];
                    for (int i = dest_route->length; i > best_pos; i--) {
                        dest_route->path[i] = dest_route->path[i-1];
                    }
                    dest_route->path[best_pos] = city;
                    dest_route->length++;
                    dest_route->duration += best_cost;
                } else {
                    // Remettre à l'ancienne position si aucune nouvelle position trouvée
                    route->path[route->length++] = city;
                }
                break;
            }

            case 1: // Échange de deux villes
            {
                int city1, city2;
                do {
                    city1 = rand() % NUM_CITIES;
                    city2 = rand() % NUM_CITIES;
                } while (city1 == DEPOT || city2 == DEPOT || city1 == city2);

                // Trouver les positions
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

            case 2: // Optimisation 2-opt
            {
                if (indiv->solution.num_vehicles > 0) {
                    int r = rand() % indiv->solution.num_vehicles;
                    Route* route = &indiv->solution.routes[r];

                    if (route->length >= 4) {
                        int i = rand() % (route->length - 1);
                        int j = rand() % (route->length - i - 1) + i + 2;

                        // Inverser le segment
                        while (i < j) {
                            int temp = route->path[i];
                            route->path[i] = route->path[j];
                            route->path[j] = temp;
                            i++;
                            j--;
                        }

                        route->duration = route_duration(board, route);
                    }
                }
                break;
            }
        }

        indiv->fitness = calculate_fitness(board, &indiv->solution);
    }
}

// Évolution de la population
void evolve_population(Board board, Population* pop) {
    Population new_pop;
    new_pop.generation = pop->generation + 1;
    new_pop.stagnation_count = pop->stagnation_count;

    // Élitisme: conserver le meilleur individu
    new_pop.members[0] = pop->best_ever;
    new_pop.best_ever = pop->best_ever;

    // Générer les nouveaux individus
    for (int i = 1; i < POPULATION_SIZE; i++) {
        Individual parent1 = tournament_selection(pop);
        Individual parent2 = tournament_selection(pop);
        Individual child;

        if ((double)rand() / RAND_MAX < CROSSOVER_RATE) {
            crossover(board, &parent1, &parent2, &child);
        } else {
            child = parent1; // Clonage
        }

        mutate(board, &child);
        new_pop.members[i] = child;

        // Mettre à jour le meilleur individu
        if (child.fitness < new_pop.best_ever.fitness) {
            new_pop.best_ever = child;
        }
    }

    // Vérifier la stagnation
    if (new_pop.best_ever.fitness < pop->best_ever.fitness) {
        new_pop.stagnation_count = 0;
    } else {
        new_pop.stagnation_count++;
    }

    *pop = new_pop;
}

// Affichage d'une solution
void print_solution(Solution* solution) {
    printf("\nSolution optimale:\n");
    printf("Véhicules utilisés: %d\n", solution->num_vehicles);
    printf("Durée totale: %d secondes\n", solution->total_duration);

    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        printf("Véhicule %d (%ds): Depot", i+1, route->duration);
        for (int j = 0; j < route->length; j++) {
            printf(" -> %d", route->path[j]);
        }
        printf(" -> Depot\n");
    }
}

// Algorithme principal VRP
void solve_vrp(Board board, Solution* best_solution) {
    srand(time(NULL));
    Population pop;
    init_population(board, &pop);

    for (int gen = 0; gen < MAX_GENERATIONS; gen++) {
        evolve_population(board, &pop);

        if (gen % 10 == 0) {
            printf("Generation %d: Fitness=%lld Vehicules=%d Duree=%d\n",
                   gen, pop.best_ever.fitness,
                   pop.best_ever.solution.num_vehicles,
                   pop.best_ever.solution.total_duration);
        }

        if (pop.stagnation_count >= STAGNATION_LIMIT) {
            printf("Arret premature a la generation %d (stagnation)\n", gen);
            break;
        }
    }

    *best_solution = pop.best_ever.solution;
}