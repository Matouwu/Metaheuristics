#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#include "inout.h"
#include "location.h"
#include "genetic.h"
#include "graphic.h"


int main(int argc, char *argv[]){

  Board board;
  initBoard(board);
  fread_board(argv[1], board);
  display_board(board);

  return EXIT_SUCCESS;
}

