#include <stdio.h>
#include <time.h>
#include "location.h"

void initBoard(Board board){
  srand(time(NULL));
  int i,j;
  for(i = 0; i < 85; i++){
    for(j = 0; j < 85; j++){
      board[i][j] = rand() % 10;
    }
  }
}

void display_board(Board board){
  int i,j;
  for(i = 0; i < 85; i++){
    for(j = 0; j < 85; j++){
      printf("%d ",board[i][j]);
    }
    printf("\n");
  }
}
