#ifndef GENETIC_H
#define GENETIC_H

#include "location.h"
#include "inout.h"
#include "graphic.h"

int calcul_fitness(Board board, Path path);
void randomize_path(Board board, Path path);
void init_path(Path path);

#endif /* GENETIC_H */
