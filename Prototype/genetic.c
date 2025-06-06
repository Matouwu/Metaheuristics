#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include "genetic.h"
#include "location.h"

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
int calculate_fitness(Board board, Solution* solution) {
    int fitness = 0;
    int penalty = 0;
    solution->total_duration = 0;

    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        route->duration = route_duration(board, route);
        solution->total_duration += route->duration;

        if (route->duration > MAX_TIME) {
            penalty += (route->duration - MAX_TIME) * 1000;
        }
    }

    // Fitness = (1e6 * nombre de véhicules) + durée totale + pénalités
    fitness = 1000000 * solution->num_vehicles + solution->total_duration + penalty;
    return fitness;
}

// Initialisation d'une solution vide
void init_solution(Solution* solution) {
    solution->num_vehicles = 0;
    solution->total_duration = 0;
    for (int i = 0; i < MAX_VEHICLES; i++) {
        solution->routes[i].length = 0;
        solution->routes[i].duration = 0;
        for (int j = 0; j < MAX_ROUTE_LENGTH; j++) {
            solution->routes[i].path[j] = -1;
        }
    }
}

// Construction d'une solution initiale (version finale)
void build_initial_solution(Board board, Solution* sol) {
    int visited[NUM_CITIES] = {0};
    visited[DEPOT] = 1;

    int unvisited[NUM_CITIES-1];
    int unvisited_count = 0;
    for (int i = 0; i < NUM_CITIES; i++) {
        if (i != DEPOT) unvisited[unvisited_count++] = i;
    }

    sol->num_vehicles = 0;

    // Mélanger les villes
    for (int i = unvisited_count-1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = unvisited[i];
        unvisited[i] = unvisited[j];
        unvisited[j] = temp;
    }

    while (unvisited_count > 0) {
        // Créer une nouvelle route
        if (sol->num_vehicles >= MAX_VEHICLES) break;

        Route* route = &sol->routes[sol->num_vehicles];
        route->length = 0;
        int current = DEPOT;
        int duration = 0;

        int remaining = unvisited_count;
        for (int i = 0; i < remaining; i++) {
            int city = unvisited[i];
            int travel_time = board[current][city];
            int return_time = board[city][DEPOT];

            // Vérifier si on peut ajouter la ville
            if (duration + travel_time + return_time <= MAX_TIME) {
                // Ajouter la ville à la route
                route->path[route->length++] = city;
                duration += travel_time;
                current = city;
                visited[city] = 1;

                // Retirer de la liste des non visités
                unvisited[i] = unvisited[--unvisited_count];
                i--; // Re-vérifier la nouvelle ville à cette position
                remaining = unvisited_count;
            }
        }

        sol->num_vehicles++;
    }

    // Ajouter les villes restantes une par une
    for (int i = 0; i < unvisited_count; i++) {
        int city = unvisited[i];
        int min_cost = INT_MAX;
        int best_route = -1;
        int best_pos = -1;

        for (int r = 0; r < sol->num_vehicles; r++) {
            Route* route = &sol->routes[r];

            for (int pos = 0; pos <= route->length; pos++) {
                int prev = (pos == 0) ? DEPOT : route->path[pos-1];
                int next = (pos == route->length) ? DEPOT : route->path[pos];
                int added_time = board[prev][city] + board[city][next] - board[prev][next];

                if (route->duration + added_time <= MAX_TIME && added_time < min_cost) {
                    min_cost = added_time;
                    best_route = r;
                    best_pos = pos;
                }
            }
        }

        if (best_route != -1) {
            Route* route = &sol->routes[best_route];
            for (int j = route->length; j > best_pos; j--) {
                route->path[j] = route->path[j-1];
            }
            route->path[best_pos] = city;
            route->length++;
            route->duration += min_cost;
        }
    }

    // Calculer les durées finales
    calculate_fitness(board, sol);
    repair_solution(board, sol);
}

// Initialisation de la population
void init_population(Board board, Population* pop) {
    pop->generation = 0;
    pop->stagnation_count = 0;

    for (int i = 0; i < POPULATION_SIZE; i++) {
        init_solution(&pop->members[i].solution);
        build_initial_solution(board, &pop->members[i].solution);
        pop->members[i].fitness = calculate_fitness(board, &pop->members[i].solution);
    }

    // Initialiser le meilleur individu
    pop->best_ever = pop->members[0];
    for (int i = 1; i < POPULATION_SIZE; i++) {
        if (pop->members[i].fitness < pop->best_ever.fitness) {
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

// Mutation: déplacer une ville
void mutate_move_city(Board board, Individual* indiv) {
    // Choisir une ville au hasard
    int city;
    do {
        city = rand() % NUM_CITIES;
    } while (city == DEPOT);

    // Trouver sa route actuelle
    int source_route = -1;
    int source_index = -1;
    for (int r = 0; r < indiv->solution.num_vehicles; r++) {
        Route* route = &indiv->solution.routes[r];
        for (int i = 0; i < route->length; i++) {
            if (route->path[i] == city) {
                source_route = r;
                source_index = i;
                break;
            }
        }
        if (source_route != -1) break;
    }

    if (source_route == -1) return; // Ville non trouvée

    // Retirer la ville de sa route actuelle
    Route* src_route = &indiv->solution.routes[source_route];
    for (int i = source_index; i < src_route->length - 1; i++) {
        src_route->path[i] = src_route->path[i+1];
    }
    src_route->length--;

    // Trouver une nouvelle route pour cette ville
    int min_cost = INT_MAX;
    int best_route = -1;
    int best_pos = -1;

    // Essayer de déplacer vers une autre route existante
    for (int r = 0; r < indiv->solution.num_vehicles; r++) {
        if (r == source_route) continue; // Ne pas remettre dans la même route

        Route* route = &indiv->solution.routes[r];
        for (int pos = 0; pos <= route->length; pos++) {
            int prev = (pos == 0) ? DEPOT : route->path[pos-1];
            int next = (pos == route->length) ? DEPOT : route->path[pos];
            int added_time = board[prev][city] + board[city][next] - board[prev][next];

            if (route->duration + added_time <= MAX_TIME && added_time < min_cost) {
                min_cost = added_time;
                best_route = r;
                best_pos = pos;
            }
        }
    }

    // Si aucune route existante ne convient, créer une nouvelle route
    if (best_route == -1 && indiv->solution.num_vehicles < MAX_VEHICLES) {
        best_route = indiv->solution.num_vehicles++;
        best_pos = 0;
        min_cost = board[DEPOT][city] + board[city][DEPOT];
    }

    // Insérer la ville dans la nouvelle position
    if (best_route != -1) {
        Route* dest_route = &indiv->solution.routes[best_route];
        // Décaler les éléments pour faire de la place
        for (int i = dest_route->length; i > best_pos; i--) {
            dest_route->path[i] = dest_route->path[i-1];
        }
        dest_route->path[best_pos] = city;
        dest_route->length++;
        dest_route->duration += min_cost;
    } else {
        // Si aucune option valide, remettre dans la route d'origine
        src_route->path[src_route->length++] = city;
    }

    // Mettre à jour la durée de la route source
    src_route->duration = route_duration(board, src_route);
}

// Mutation: échanger deux villes
void mutate_swap_cities(Individual* indiv) {
    // Choisir deux villes différentes au hasard
    int city1, city2;
    do {
        city1 = rand() % NUM_CITIES;
        city2 = rand() % NUM_CITIES;
    } while (city1 == DEPOT || city2 == DEPOT || city1 == city2);

    // Trouver leurs positions
    int route1_idx = -1, route2_idx = -1;
    int pos1 = -1, pos2 = -1;

    for (int r = 0; r < indiv->solution.num_vehicles; r++) {
        Route* route = &indiv->solution.routes[r];
        for (int i = 0; i < route->length; i++) {
            if (route->path[i] == city1) {
                route1_idx = r;
                pos1 = i;
            }
            if (route->path[i] == city2) {
                route2_idx = r;
                pos2 = i;
            }
        }
    }

    if (route1_idx == -1 || route2_idx == -1) return;

    // Échanger les villes
    Route* route1 = &indiv->solution.routes[route1_idx];
    Route* route2 = &indiv->solution.routes[route2_idx];

    route1->path[pos1] = city2;
    route2->path[pos2] = city1;
}

// Mutation: optimisation 2-opt sur une route
void mutate_2opt_route(Board board, Route* route) {
    if (route->length < 4) return;

    int i = rand() % (route->length - 1);
    int j = rand() % (route->length - i - 1) + i + 2;

    // Inverser la section entre i et j
    while (i < j) {
        int temp = route->path[i];
        route->path[i] = route->path[j];
        route->path[j] = temp;
        i++;
        j--;
    }

    // Recalculer la durée
    route->duration = route_duration(board, route);
}

// Mutation générale
void mutate(Board board, Individual* indiv) {
    if ((double)rand() / RAND_MAX < MUTATION_RATE) {
        int choice = rand() % 3;
        switch (choice) {
            case 0: mutate_move_city(board, indiv); break;
            case 1: mutate_swap_cities(indiv); break;
            case 2:
                if (indiv->solution.num_vehicles > 0) {
                    int r = rand() % indiv->solution.num_vehicles;
                    mutate_2opt_route(board, &indiv->solution.routes[r]);
                }
                break;
        }
        indiv->fitness = calculate_fitness(board, &indiv->solution);
    }
}

// Croisement (version finale)
void crossover(Board board, Individual* parent1, Individual* parent2, Individual* child) {
    init_solution(&child->solution);

    // Choisir une route valide dans parent1
    int attempts = 0;
    int route_idx;
    do {
        route_idx = rand() % parent1->solution.num_vehicles;
        attempts++;
    } while (parent1->solution.routes[route_idx].length == 0 && attempts < 10);

    if (attempts >= 10) {
        child->solution = parent1->solution; // Copie de la solution
        repair_solution(board, &child->solution); // Réparation après copie
        child->fitness = calculate_fitness(board, &child->solution);
        return;
    }

    Route* p1_route = &parent1->solution.routes[route_idx];

    // Copier cette route dans l'enfant
    Route* child_route = &child->solution.routes[0];
    memcpy(child_route->path, p1_route->path, p1_route->length * sizeof(int));
    child_route->length = p1_route->length;
    child_route->duration = p1_route->duration;
    child->solution.num_vehicles = 1;

    // Marquer les villes copiées
    int visited[NUM_CITIES] = {0};
    visited[DEPOT] = 1;
    for (int i = 0; i < child_route->length; i++) {
        visited[child_route->path[i]] = 1;
    }

    // Ajouter les villes manquantes depuis parent2
    for (int r = 0; r < parent2->solution.num_vehicles; r++) {
        Route* p2_route = &parent2->solution.routes[r];

        for (int i = 0; i < p2_route->length; i++) {
            int city = p2_route->path[i];

            if (is_valid_city(city) && !visited[city]) {
                // Trouver la meilleure position dans les routes existantes
                int min_cost = INT_MAX;
                int best_route_idx = -1;
                int best_pos = -1;

                for (int cr = 0; cr < child->solution.num_vehicles; cr++) {
                    Route* c_route = &child->solution.routes[cr];

                    for (int pos = 0; pos <= c_route->length; pos++) {
                        int prev = (pos == 0) ? DEPOT : c_route->path[pos-1];
                        int next = (pos == c_route->length) ? DEPOT : c_route->path[pos];
                        int added_time = board[prev][city] + board[city][next] - board[prev][next];

                        if (c_route->duration + added_time <= MAX_TIME && added_time < min_cost) {
                            min_cost = added_time;
                            best_route_idx = cr;
                            best_pos = pos;
                        }
                    }
                }

                // Créer une nouvelle route si nécessaire
                if (best_route_idx == -1 && child->solution.num_vehicles < MAX_VEHICLES) {
                    best_route_idx = child->solution.num_vehicles;
                    Route* new_route = &child->solution.routes[best_route_idx];
                    new_route->path[0] = city;
                    new_route->length = 1;
                    new_route->duration = board[DEPOT][city] + board[city][DEPOT];
                    child->solution.num_vehicles++;
                    visited[city] = 1;
                }
                // Insérer dans une route existante
                else if (best_route_idx != -1) {
                    Route* c_route = &child->solution.routes[best_route_idx];

                    // Faire de la place pour la nouvelle ville
                    for (int j = c_route->length; j > best_pos; j--) {
                        c_route->path[j] = c_route->path[j-1];
                    }

                    c_route->path[best_pos] = city;
                    c_route->length++;
                    c_route->duration += min_cost;
                    visited[city] = 1;
                }
            }
        }
    }

    // Réparer la solution
    repair_solution(board, &child->solution);
    child->fitness = calculate_fitness(board, &child->solution);
}

// Fonction pour vérifier si une ville est valide
int is_valid_city(int city) {
    return (city >= 0 && city < NUM_CITIES && city != DEPOT);
}

// Réparer une solution invalide (version finale)
void repair_solution(Board board, Solution* sol) {
    int global_visited[NUM_CITIES] = {0};
    global_visited[DEPOT] = 1;

    // Réinitialiser les routes et marquer les villes visitées
    for (int r = 0; r < sol->num_vehicles; r++) {
        Route* route = &sol->routes[r];
        int new_length = 0;
        int local_visited[NUM_CITIES] = {0};

        for (int i = 0; i < route->length; i++) {
            int city = route->path[i];
            if (is_valid_city(city) && !local_visited[city] && !global_visited[city]) {
                route->path[new_length++] = city;
                local_visited[city] = 1;
                global_visited[city] = 1;
            }
        }
        route->length = new_length;
    }

    // Ajouter les villes manquantes
    int missing_cities[NUM_CITIES];
    int missing_count = 0;
    for (int city = 0; city < NUM_CITIES; city++) {
        if (city != DEPOT && !global_visited[city]) {
            missing_cities[missing_count++] = city;
        }
    }

    for (int m = 0; m < missing_count; m++) {
        int city = missing_cities[m];
        int min_cost = INT_MAX;
        int best_route = -1;
        int best_pos = -1;

        for (int r = 0; r < sol->num_vehicles; r++) {
            Route* route = &sol->routes[r];
            for (int pos = 0; pos <= route->length; pos++) {
                int prev = (pos == 0) ? DEPOT : route->path[pos-1];
                int next = (pos == route->length) ? DEPOT : route->path[pos];
                int added_time = board[prev][city] + board[city][next] - board[prev][next];

                if (route->duration + added_time <= MAX_TIME && added_time < min_cost) {
                    min_cost = added_time;
                    best_route = r;
                    best_pos = pos;
                }
            }
        }

        if (best_route == -1 && sol->num_vehicles < MAX_VEHICLES) {
            best_route = sol->num_vehicles++;
            best_pos = 0;
            min_cost = board[DEPOT][city] + board[city][DEPOT];
        }

        if (best_route != -1) {
            Route* route = &sol->routes[best_route];
            for (int j = route->length; j > best_pos; j--) {
                route->path[j] = route->path[j-1];
            }
            route->path[best_pos] = city;
            route->length++;
            route->duration += min_cost;
        }
    }

    // Supprimer les routes vides
    int valid_routes = 0;
    for (int r = 0; r < sol->num_vehicles; r++) {
        if (sol->routes[r].length > 0) {
            if (valid_routes != r) {
                sol->routes[valid_routes] = sol->routes[r];
            }
            valid_routes++;
        }
    }
    sol->num_vehicles = valid_routes;

    // Recalculer les durées
    sol->total_duration = 0;
    for (int r = 0; r < sol->num_vehicles; r++) {
        sol->routes[r].duration = route_duration(board, &sol->routes[r]);
        sol->total_duration += sol->routes[r].duration;
    }
}

// Évolution de la population
void evolve_population(Board board, Population* pop) {
    Population new_pop;
    new_pop.generation = pop->generation + 1;

    // Élitisme: conserver le meilleur individu
    new_pop.members[0] = pop->best_ever;

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
    }

    // Trouver le nouveau meilleur individu
    new_pop.best_ever = new_pop.members[0];
    for (int i = 1; i < POPULATION_SIZE; i++) {
        if (new_pop.members[i].fitness < new_pop.best_ever.fitness) {
            new_pop.best_ever = new_pop.members[i];
        }
    }

    // Vérifier la stagnation
    if (new_pop.best_ever.fitness < pop->best_ever.fitness) {
        new_pop.stagnation_count = 0;
    } else {
        new_pop.stagnation_count = pop->stagnation_count + 1;
    }

    *pop = new_pop;
}

// Affichage d'une solution
void print_solution(Solution* solution) {
    printf("Solution avec %d véhicules:\n", solution->num_vehicles);
    for (int i = 0; i < solution->num_vehicles; i++) {
        Route route = solution->routes[i];
        printf("Véhicule %d (durée: %ds): 0 -> ", i+1, route.duration);
        for (int j = 0; j < route.length; j++) {
            printf("%d -> ", route.path[j]);
        }
        printf("0\n");
    }
    printf("Durée totale: %d secondes\n", solution->total_duration);
}

// Algorithme principal VRP
void solve_vrp(Board board, Solution* best_solution) {
    srand(time(NULL));
    Population pop;
    init_population(board, &pop);

    for (int gen = 0; gen < MAX_GENERATIONS; gen++) {
        evolve_population(board, &pop);

        if (gen % 10 == 0) {
            printf("Generation %d: Fitness = %d (Vehicles: %d, Duration: %d)\n",
                   gen, pop.best_ever.fitness,
                   pop.best_ever.solution.num_vehicles,
                   pop.best_ever.solution.total_duration);
        }

        // Arrêt prématuré si stagnation
        if (pop.stagnation_count >= STAGNATION_LIMIT) {
            printf("Stagnation detected. Stopping early at generation %d\n", gen);
            break;
        }
    }

    *best_solution = pop.best_ever.solution;
}