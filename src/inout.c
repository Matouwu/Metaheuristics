#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "inout.h"

int fread_board(const char* file, Board board) {
    FILE* f = fopen(file, "r");
    char line[MAX_LINE_LENGTH];
    int row = 0, col = 0;

    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }

    // Ignorer l'en-tête
    fgets(line, MAX_LINE_LENGTH, f);

    while (fgets(line, MAX_LINE_LENGTH, f) != NULL && row < NUM_CITIES) {
        col = 0;
        char* token = strtok(line, ",");

        while (token != NULL && col < NUM_CITIES) {
            board[row][col] = atoi(token);
            token = strtok(NULL, ",");
            col++;
        }
        row++;
    }

    fclose(f);
    return 1;
}