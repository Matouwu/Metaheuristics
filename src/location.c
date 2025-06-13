#include <stdio.h>
#include <stdlib.h>
#include "location.h"

void initBoard(Board board) {
    for (int i = 0; i < MAX_CITIES; i++) {
        for (int j = 0; j < MAX_CITIES; j++) {
            board[i][j] = (i == j) ? 0 : -1;
        }
    }
}

void display_board(Board board) {
    if (NUM_CITIES == 0) {
        printf("Aucune ville chargée\n");
        return;
    }

    printf("Matrice des distances (tronquée):\n");
    int display_size = (NUM_CITIES < 5) ? NUM_CITIES : 5;

    for (int i = 0; i < display_size; i++) {
        for (int j = 0; j < display_size; j++) {
            printf("%6d ", board[i][j]);
        }
        printf("\n");
    }

    if (NUM_CITIES > 5) {
        printf("[...] (Matrice de %d x %d)\n", NUM_CITIES, NUM_CITIES);
    }
}