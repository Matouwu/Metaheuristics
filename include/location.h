#ifndef LOCATION_H
#define LOCATION_H

#define MAX_CITIES 200
#define MAX_VEHICLES 20
#define MAX_ROUTE_LENGTH 50
#define MAX_TIME 10800  /* 3 heures en secondes */
#define DEPOT 0
#define PENALTY_PER_VIOLATION 10000000

extern int NUM_CITIES;

typedef int Board[MAX_CITIES][MAX_CITIES];

typedef struct {
    int path[MAX_ROUTE_LENGTH];
    int length;
    int duration;   /* Temps total en secondes */
    int distance;   /* Distance totale en mètres */
} Route;

typedef struct {
    Route routes[MAX_VEHICLES];
    int num_vehicles;
    int total_duration;   /* Temps total en secondes */
    int total_distance;   /* Distance totale en mètres */
} Solution;

void initBoard(Board board);
void display_board(Board board);

#endif