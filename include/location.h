#ifndef LOCATION_H
#define LOCATION_H

#define MAX_CITIES 200  // Taille maximale
#define MAX_VEHICLES 20
#define MAX_ROUTE_LENGTH 50
#define MAX_TIME 10800
#define DEPOT 0
#define PENALTY_PER_VIOLATION 10000000

extern int NUM_CITIES;  // Variable globale

typedef int Board[MAX_CITIES][MAX_CITIES];  // Utilise MAX_CITIES

typedef struct {
    int path[MAX_ROUTE_LENGTH];
    int length;
    int duration;
} Route;

typedef struct {
    Route routes[MAX_VEHICLES];
    int num_vehicles;
    int total_duration;
} Solution;

void initBoard(Board board);
void display_board(Board board);

#endif