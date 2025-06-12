#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "inout.h"

int fread_board(const char* file, Board board) {
    FILE* f = fopen(file, "r");
    char line[MAX_LINE_LENGTH];
    int row = 0;

    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }

    // Ignorer la première ligne (en-tête des colonnes)
    fgets(line, MAX_LINE_LENGTH, f);

    // Lire chaque ligne suivante
    while (fgets(line, MAX_LINE_LENGTH, f) != NULL && row < NUM_CITIES) {
        int col = 0;
        char* token = strtok(line, ",");  // Ignorer le premier champ de la ligne (index de ligne)

        // Lire les champs suivants (valeurs de la ligne)
        token = strtok(NULL, ",");
        while (token != NULL && col < NUM_CITIES) {
            board[row][col] = atoi(token);
            token = strtok(NULL, ",");
            col++;
        }

        // Vérification optionnelle
        if (col != NUM_CITIES) {
            fprintf(stderr, "Erreur : ligne %d a %d colonnes au lieu de %d\n", row, col, NUM_CITIES);
            fclose(f);
            return 0;
        }

        row++;
    }

    if (row != NUM_CITIES) {
        fprintf(stderr, "Erreur : le fichier contient %d lignes au lieu de %d\n", row, NUM_CITIES);
        fclose(f);
        return 0;
    }

    fclose(f);
    return 1;
}
