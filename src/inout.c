#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "inout.h"
#include "location.h"

int NUM_CITIES = 0;

int fread_board(const char* file, Board board) {
    FILE* f = fopen(file, "r");
    char line[MAX_LINE_LENGTH];
    int row = 0;
    int col;
    char* token;

    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }

    /* Lecture de la première ligne (en-tête) pour déterminer le nombre de villes */
    if (fgets(line, MAX_LINE_LENGTH, f) == NULL) {
        fprintf(stderr, "Fichier vide ou en-tête manquante\n");
        fclose(f);
        return 0;
    }

    /* Compter le nombre de colonnes (ignore la première cellule vide) */
    token = strtok(line, ",");  /* Ce token est la case vide en début de ligne */
    NUM_CITIES = 0;
    while ((token = strtok(NULL, ",")) != NULL) {
        NUM_CITIES++;
    }

    if (NUM_CITIES > MAX_CITIES) {
        fprintf(stderr, "Trop de villes ! Max = %d\n", MAX_CITIES);
        fclose(f);
        return 0;
    }

    /* Lire les lignes de données */
    while (fgets(line, MAX_LINE_LENGTH, f) != NULL && row < NUM_CITIES) {
        col = 0;
        token = strtok(line, ",");  /* index ignoré */
        while ((token = strtok(NULL, ",")) != NULL && col < NUM_CITIES) {
            board[row][col] = atoi(token);
            col++;
        }
        row++;
    }
    fclose(f);
    return 1;
}

void write_solution(const char* filename, Solution* solution) {
    FILE* f = fopen(filename, "w");
    int i, j;

    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", filename);
        return;
    }

    for (i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        fprintf(f, "[");

        for (j = 0; j < route->length; j++) {
            if (j == 0)
                fprintf(f, "%d", route->path[j]);
            else
                fprintf(f, ",%d", route->path[j]);
        }

        fprintf(f, "]\n");
    }

    fclose(f);
}