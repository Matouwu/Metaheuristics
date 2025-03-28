#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "inout.h"

int fread_board(const char* file, Board board){
    FILE* f = fopen(file, "r");
    int i = 0;
    int j = 0;
    char line[MAX_LINE_LENGTH];

    if (f == NULL){
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }

    fgets(line, MAX_LINE_LENGTH, f); /* Ignorer la première ligne */

    while (fgets(line, MAX_LINE_LENGTH, f) != NULL) {
        char* value = strtok(line, ",");

        while (value != NULL) {
            if (value != NULL) {
                board[i][j++] = atoi(value);
            }
            value = strtok(NULL, ",");
        }

        i++;
        j = 0;
    }

    fclose(f);
    return 1;
}