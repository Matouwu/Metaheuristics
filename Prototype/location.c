#include <stdio.h>
#include <stdlib.h>
#include "location.h"

void initBoard(Board board) {
  // Initialisation par défaut (sera écrasée par fread_board)
  for (int i = 0; i < NUM_CITIES; i++) {
    for (int j = 0; j < NUM_CITIES; j++) {
      board[i][j] = (i == j) ? 0 : 999999;
    }
  }
}

void display_board(Board board) {
  printf("Matrice des distances:\n");
  for (int i = 0; i < 5; i++) { // Affiche seulement les 5 premières lignes
    for (int j = 0; j < 5; j++) { // et 5 premières colonnes
      printf("%6d ", board[i][j]);
    }
    printf("\n");
  }
  printf("[...] (Matrice tronquée)\n");
}