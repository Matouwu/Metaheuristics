#ifndef LOCATION_H
#define LOCATION_H

#define NUM_CITIES 85
#define MAX_VEHICLES 20
#define MAX_ROUTE_LENGTH 50
#define MAX_TIME 10800 // 3 heures en secondes (3*3600)
#define DEPOT 0

typedef int Board[NUM_CITIES][NUM_CITIES];

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

#endif /* LOCATION_H */