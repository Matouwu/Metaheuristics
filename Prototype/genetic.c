#include <stdio.h>
#include <stdlib.h>
#include "genetic.h"

int calcul_fitness(Board board, Path path){
    int fitness = 0;
    int i;
    for(i = 0; i < 84; i++){
        fitness += board[path[i]][path[i+1]];
    }
    fitness += board[path[84]][path[0]];
    return fitness;
}

void init_path(Path path){
    int i;
    for(i = 0; i < 85; i++){
        path[i] = i;
    }
}

void randomize_path(Board board, Path path){
    int i, j, temp, fitness;
    fitness = calcul_fitness(board, path);
    i = rand() % 85;
    j = rand() % 85;
    temp = path[i];
    path[i] = path[j];
    path[j] = temp;
    if (calcul_fitness(board, path) > fitness){
        temp = path[i];
        path[i] = path[j];
        path[j] = temp;
        return;
    }
}