#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "inout.h"
#include "location.h"

int NUM_CITIES = 0;

int fread_board(const char* file, Board board) {
    FILE* f = fopen(file, "r");
    char line[MAX_LINE_LENGTH];
    int num_lines = 0;

    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", file);
        return 0;
    }

    // Compter le nombre de lignes (villes)
    fgets(line, MAX_LINE_LENGTH, f); // Ignorer l'en-tête
    while (fgets(line, MAX_LINE_LENGTH, f) != NULL) {
        num_lines++;
    }

    if (num_lines > MAX_CITIES) {
        fprintf(stderr, "Trop de villes! Max=%d\n", MAX_CITIES);
        fclose(f);
        return 0;
    }

    NUM_CITIES = num_lines;

    // Relire le fichier pour extraire les données
    rewind(f);
    fgets(line, MAX_LINE_LENGTH, f); // Ignorer à nouveau l'en-tête

    for (int row = 0; row < NUM_CITIES; row++) {
        if (fgets(line, MAX_LINE_LENGTH, f) == NULL) break;

        int col = 0;
        char* token = strtok(line, ",");
        token = strtok(NULL, ","); // Ignorer la première colonne

        while (token != NULL && col < NUM_CITIES) {
            board[row][col] = atoi(token);
            token = strtok(NULL, ",");
            col++;
        }
    }

    fclose(f);
    return 1;
}

void write_solution(const char* filename, Solution* solution) {
    FILE* f = fopen(filename, "w");
    if (f == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier %s\n", filename);
        return;
    }

    for (int i = 0; i < solution->num_vehicles; i++) {
        Route* route = &solution->routes[i];
        fprintf(f, "[");

        for (int j = 0; j < route->length; j++) {
            if (j == 0)
                fprintf(f, "%d", route->path[j]);
            else
                fprintf(f, ",%d", route->path[j]);
        }

        fprintf(f, "]\n");
    }

    fclose(f);
}