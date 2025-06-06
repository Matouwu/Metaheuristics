#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "location.h"

void initBoard(Board board){
  srand(time(NULL));
  int i,j;
  for(i = 0; i < NUM_CITIES; i++){
    for(j = 0; j < NUM_CITIES; j++){
      board[i][j] = 1;
    }
  }
}

void display_board(Board board){
  int i,j;
  for(i = 0; i < NUM_CITIES; i++){
    for(j = 0; j < NUM_CITIES; j++){
      printf("%d ",board[i][j]);
    }
    printf("\n");
  }
}