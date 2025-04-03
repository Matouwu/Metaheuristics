#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#include "inout.h"
#include "location.h"
#include "genetic.h"
#include "graphic.h"

  for (i = 0; i < 85; i++){
    printf("%d ", path[i]);
  }
int main(int argc, char *argv[]){

  Board board;
  initBoard(board);
  fread_board(argv[1], board);
  display_board(board);
  Path path;
  init_path(path);
  printf("%d\n",calcul_fitness(board, path));
  int i;
  for (i = 0; i < 15000; i++){
    randomize_path(board, path);
  }
  printf("%d\n",calcul_fitness(board, path));
  return EXIT_SUCCESS;
}

