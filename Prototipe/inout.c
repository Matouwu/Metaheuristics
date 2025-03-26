#include <stdio.h>
#include "inout.h"

int fread_board(const char* file, Board board){
    FILE* f;
    int i,j;
    int entry;

    f = fopen(file, "r");
    if (f == NULL){
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }




    return 1;
}