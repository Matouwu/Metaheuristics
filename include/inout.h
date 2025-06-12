#ifndef INOUT_H
#define INOUT_H

#include "location.h"

#define MAX_LINE_LENGTH 500

int fread_board(const char* file, Board board);
void write_solution(const char* filename, Solution* solution);

#endif