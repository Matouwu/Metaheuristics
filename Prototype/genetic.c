#include <stdio.h>
#include <stdlib.h>
#include "genetic.h"

int fitness(Board board, Path path){
    int fitness = 0;
    int i;
    for(i = 0; i < 84; i++){
        fitness += board[path[i]][path[i+1]];
    }
    fitness += board[path[84]][path[0]];
    return fitness;
}

void init_path(Path path){
    int i, j;
    for(i = 0; i < 85; i++){
        path[i] = i;
    }
}
