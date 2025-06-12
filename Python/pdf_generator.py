#!/usr/bin/env python3
"""
Script de génération de PDF pour le projet CERP de Rouen
Génère les PDF de tournées pour chaque camionnette avec vraies cartes GPS
"""

import csv
import json
import re
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
import requests
import io
from PIL import Image as PILImage
import matplotlib.pyplot as plt
try:
    import contextily as ctx
    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False
    print("Contextily non disponible - utilisation de cartes simples")
from pyproj import Transformer


class CERPDeliveryPDFGenerator:
    def __init__(self):
        """
        Initialise le générateur de PDF avec les vrais fichiers
        """
        # Initialiser les attributs
        self.depot_address = "600 Rue des Madeleines, 77100 Mareuil-lès-Meaux"
        self.styles = getSampleStyleSheet()

        # Configuration des horaires
        self.morning_start = "09:00"
        self.morning_end = "12:00"
        self.afternoon_start = "15:00"
        self.afternoon_end = "18:00"
        self.delivery_duration = 3  # minutes par livraison

        # Constantes imposées par le projet
        self.fuel_consumption_per_100km = 6.5  # L/100km
        self.diesel_price_per_liter = 1.72  # €/L

        # Chemins des fichiers
        pharmacies_file = "pharmacies_coordonnees.csv"  # Dans Python/
        distances_file = os.path.join("..", "Prototype", "distance.csv")  # Dans Prototype/

        print(f"Chargement des pharmacies: {pharmacies_file}")
        print(f"Chargement des distances: {distances_file}")

        # Charger les données
        self.pharmacies = self.load_pharmacies_with_coords(pharmacies_file)
        self.distances = self.load_distances(distances_file)

    def load_pharmacies_with_coords(self, file_path):
        """Charge les pharmacies avec leurs coordonnées GPS"""
        pharmacies = {}

        print(f"Tentative de chargement: {file_path}")
        print(f"Le fichier existe-t-il? {os.path.exists(file_path)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Ajouter le dépôt à l'index 0 (coordonnées approximatives de Mareuil-lès-Meaux)
                pharmacies[0] = {
                    'nom': 'Dépôt CERP Rouen',
                    'adresse': '600 Rue des Madeleines',
                    'code_postal': '77100',
                    'ville': 'Mareuil-lès-Meaux',
                    'adresse_complete': self.depot_address,
                    'latitude': 48.9341,
                    'longitude': 2.8738
                }

                # Charger les pharmacies (index 1 à 84)
                for i, row in enumerate(reader, 1):
                    nom = row['nom'].strip()
                    adresse = row['adresse'].strip()
                    code_postal = str(row['code_postal']).strip()
                    ville = row['ville'].strip()
                    latitude = float(row['latitude'])
                    longitude = float(row['longitude'])

                    pharmacies[i] = {
                        'nom': nom,
                        'adresse': adresse,
                        'code_postal': code_postal,
                        'ville': ville,
                        'adresse_complete': f"{adresse}, {code_postal} {ville}",
                        'latitude': latitude,
                        'longitude': longitude
                    }

        except FileNotFoundError:
            print(f"ERREUR: Fichier {file_path} non trouvé!")
            print(f"Dossier courant: {os.getcwd()}")
            print(f"Contenu du dossier: {os.listdir('.')}")
            return {}
        except Exception as e:
            print(f"ERREUR lors du chargement des pharmacies: {e}")
            return {}

        print(f"Chargé {len(pharmacies)-1} pharmacies + 1 dépôt avec coordonnées GPS")
        return pharmacies

    def load_distances(self, file_path):
        """Charge la matrice des distances depuis distance.csv"""
        distances = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header si présent

                for row in reader:
                    # Convertir en entiers (temps en secondes)
                    distances.append([int(float(x)) for x in row])

        except FileNotFoundError:
            print(f"ERREUR: Fichier {file_path} non trouvé!")
            return []
        except Exception as e:
            print(f"ERREUR lors du chargement des distances: {e}")
            return []

        print(f"Matrice de distances chargée: {len(distances)}x{len(distances[0]) if distances else 0}")
        return distances

    def parse_route_file(self, route_file=None):
        """
        Parse le fichier de sortie avec le format:
        [1,10,42,50,84,...]
        Camionnette 1 : 1 - 10
        Camionnette 2 : 11 - 20
        """
        if route_file is None:
            route_file = os.path.join("..", "Prototype", "route_output.txt")

        print(f"Lecture du fichier de routes: {route_file}")

        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            lines = content.split('\n')
            print(f"Contenu du fichier route_output.txt:")
            for i, line in enumerate(lines):
                print(f"  Ligne {i}: {line}")

            # Extraire l'itinéraire optimal (première ligne)
            optimal_route_line = lines[0]
            route_str = optimal_route_line.strip('[]')
            optimal_route = [int(x.strip()) for x in route_str.split(',')]

            print(f"Itinéraire optimal parsé: {optimal_route}")

            # Extraire les répartitions par camionnette
            trucks = {}
            for line in lines[1:]:
                if 'Camionnette' in line:
                    # Parser "Camionnette 1 : 1 - 10"
                    match = re.match(r'Camionnette (\d+) : (\d+) - (\d+)', line.strip())
                    if match:
                        truck_num = int(match.group(1))
                        start_idx = int(match.group(2))
                        end_idx = int(match.group(3))

                        print(f"Camionnette {truck_num}: indices {start_idx} à {end_idx}")

                        # Extraire la sous-route pour cette camionnette
                        truck_route = [0]  # Commence toujours au dépôt
                        truck_route.extend(optimal_route[start_idx-1:end_idx])  # -1 car indexation
                        trucks[truck_num] = truck_route

                        print(f"Route camionnette {truck_num}: {truck_route}")

            return optimal_route, trucks

        except FileNotFoundError:
            print(f"ERREUR: Fichier {route_file} non trouvé!")
            return [], {}
        except Exception as e:
            print(f"ERREUR lors du parsing du fichier route: {e}")
            return [], {}

    def get_route_coordinates(self, start_coords, end_coords):
        """
        Récupère le trajet routier réel entre deux points via l'API OpenRouteService
        """
        try:
            # API gratuite OpenRouteService (pas besoin de clé pour usage limité)
            url = "https://api.openrouteservice.org/v2/directions/driving-car"

            # TODO : Implémenter la key API ou utiliser autre API pour les trajets routiers

            # Coordonnées format longitude,latitude pour l'API
            start_lon, start_lat = start_coords[1], start_coords[0]
            end_lon, end_lat = end_coords[1], end_coords[0]

            params = {
                'start': f"{start_lon},{start_lat}",
                'end': f"{end_lon},{end_lat}",
                'format': 'geojson'
            }

            # Headers avec User-Agent pour éviter les blocages
            headers = {
                'User-Agent': 'CERP-Route-Optimizer/1.0'
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if 'features' in data and len(data['features']) > 0:
                    # Extraire les coordonnées du trajet
                    coordinates = data['features'][0]['geometry']['coordinates']
                    # Convertir de [lon, lat] vers [lat, lon]
                    route_coords = [[coord[1], coord[0]] for coord in coordinates]
                    return route_coords

            print(f"Erreur API routing: {response.status_code}")
            return None

        except Exception as e:
            print(f"Impossible de récupérer le trajet routier: {e}")
            return None

    def create_static_map_image(self, route, truck_number):
        """Crée une vraie carte avec fond OpenStreetMap et trajets routiers"""
        if not route or len(route) < 2:
            print(f"Route trop courte pour la camionnette {truck_number}")
            return None

        # Récupérer les coordonnées de tous les points
        points = []
        for loc_idx in route:
            if loc_idx in self.pharmacies:
                pharmacy = self.pharmacies[loc_idx]
                points.append({
                    'lat': pharmacy['latitude'],
                    'lon': pharmacy['longitude'],
                    'name': pharmacy['nom'],
                    'is_depot': (loc_idx == 0)
                })
            else:
                print(f"ATTENTION: Pharmacie {loc_idx} non trouvée")
                continue

        if len(points) < 2:
            print(f"Pas assez de points valides pour la camionnette {truck_number}")
            return None

        # Calculer les limites de la carte
        lats = [p['lat'] for p in points]
        lons = [p['lon'] for p in points]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Ajouter une marge proportionnelle
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        margin_lat = max(0.01, lat_range * 0.15)  # 15% de marge minimum
        margin_lon = max(0.01, lon_range * 0.15)

        min_lat -= margin_lat
        max_lat += margin_lat
        min_lon -= margin_lon
        max_lon += margin_lon

        # Créer la figure avec fond de carte si contextily est disponible
        fig, ax = plt.subplots(figsize=(12, 10))

        # Vérifier si contextily est disponible localement
        use_contextily = CONTEXTILY_AVAILABLE

        if use_contextily:
            try:
                # Convertir les coordonnées en Web Mercator pour contextily
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

                # Convertir les limites
                west, south = transformer.transform(min_lon, min_lat)
                east, north = transformer.transform(max_lon, max_lat)

                # Définir les limites en Web Mercator
                ax.set_xlim(west, east)
                ax.set_ylim(south, north)

                # Ajouter la carte de fond OpenStreetMap
                ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik, zoom=12)

                # Convertir tous les points en Web Mercator
                for point in points:
                    point['x'], point['y'] = transformer.transform(point['lon'], point['lat'])

                # Dessiner les trajets routiers réels en Web Mercator
                for i in range(len(points)-1):
                    start_point = points[i]
                    end_point = points[i+1]

                    start_coords = [start_point['lat'], start_point['lon']]
                    end_coords = [end_point['lat'], end_point['lon']]

                    # Récupérer le trajet routier réel
                    route_coords = self.get_route_coordinates(start_coords, end_coords)

                    if route_coords and len(route_coords) > 1:
                        # Convertir le trajet en Web Mercator
                        route_x, route_y = [], []
                        for coord in route_coords:
                            x, y = transformer.transform(coord[1], coord[0])  # lon, lat
                            route_x.append(x)
                            route_y.append(y)

                        ax.plot(route_x, route_y, 'blue', linewidth=3, alpha=0.8, zorder=5)
                    else:
                        # Fallback: ligne droite
                        ax.plot([start_point['x'], end_point['x']],
                                [start_point['y'], end_point['y']],
                                'blue', linestyle='--', linewidth=2, alpha=0.6, zorder=5)

                # Retour au dépôt si nécessaire
                if len(points) > 1 and not points[-1]['is_depot']:
                    last_point = points[-1]
                    depot_point = points[0]

                    start_coords = [last_point['lat'], last_point['lon']]
                    end_coords = [depot_point['lat'], depot_point['lon']]

                    route_coords = self.get_route_coordinates(start_coords, end_coords)

                    if route_coords and len(route_coords) > 1:
                        route_x, route_y = [], []
                        for coord in route_coords:
                            x, y = transformer.transform(coord[1], coord[0])
                            route_x.append(x)
                            route_y.append(y)
                        ax.plot(route_x, route_y, 'red', linestyle='--', linewidth=2, alpha=0.7, zorder=5)
                    else:
                        ax.plot([last_point['x'], depot_point['x']],
                                [last_point['y'], depot_point['y']],
                                'red', linestyle='--', linewidth=2, alpha=0.6, zorder=5)

                # Dessiner les points en Web Mercator
                for i, point in enumerate(points):
                    if point['is_depot']:
                        ax.plot(point['x'], point['y'], 'o', color='red', markersize=15,
                                markeredgecolor='darkred', markeredgewidth=2, zorder=10, label='Dépôt CERP')
                    else:
                        ax.plot(point['x'], point['y'], 'o', color='blue', markersize=10,
                                markeredgecolor='darkblue', markeredgewidth=1, zorder=10)

                    # Numéro d'étape avec fond blanc
                    ax.annotate(str(i+1), (point['x'], point['y']),
                                xytext=(8, 8), textcoords='offset points',
                                fontsize=9, fontweight='bold', color='black', zorder=11,
                                bbox=dict(boxstyle="circle,pad=0.3", facecolor="white",
                                          edgecolor="black", alpha=0.9))

                # Pas d'axes en mode carte
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_xlabel('')
                ax.set_ylabel('')

            except Exception as e:
                print(f"Erreur avec contextily: {e}")
                use_contextily = False

        # Fallback si contextily ne fonctionne pas
        if not use_contextily:
            print("Utilisation de la carte simple (sans fond OpenStreetMap)")
            ax.set_xlim(min_lon, max_lon)
            ax.set_ylim(min_lat, max_lat)
            ax.set_facecolor('#e6f3ff')  # Bleu très clair comme eau

            # Dessiner les trajets en coordonnées géographiques normales
            for i in range(len(points)-1):
                start_point = points[i]
                end_point = points[i+1]

                start_coords = [start_point['lat'], start_point['lon']]
                end_coords = [end_point['lat'], end_point['lon']]

                route_coords = self.get_route_coordinates(start_coords, end_coords)

                if route_coords and len(route_coords) > 1:
                    route_lats = [coord[0] for coord in route_coords]
                    route_lons = [coord[1] for coord in route_coords]
                    ax.plot(route_lons, route_lats, 'blue', linewidth=3, alpha=0.8)
                else:
                    ax.plot([start_point['lon'], end_point['lon']],
                            [start_point['lat'], end_point['lat']],
                            'blue', linestyle='--', linewidth=2, alpha=0.6)

            # Retour au dépôt
            if len(points) > 1 and not points[-1]['is_depot']:
                last_point = points[-1]
                depot_point = points[0]

                start_coords = [last_point['lat'], last_point['lon']]
                end_coords = [depot_point['lat'], depot_point['lon']]

                route_coords = self.get_route_coordinates(start_coords, end_coords)

                if route_coords and len(route_coords) > 1:
                    route_lats = [coord[0] for coord in route_coords]
                    route_lons = [coord[1] for coord in route_coords]
                    ax.plot(route_lons, route_lats, 'red', linestyle='--', linewidth=2, alpha=0.7)
                else:
                    ax.plot([last_point['lon'], depot_point['lon']],
                            [last_point['lat'], depot_point['lat']],
                            'red', linestyle='--', linewidth=2, alpha=0.6)

            # Dessiner les points
            for i, point in enumerate(points):
                if point['is_depot']:
                    ax.plot(point['lon'], point['lat'], 'o', color='red', markersize=12,
                            markeredgecolor='darkred', markeredgewidth=2, label='Dépôt CERP')
                else:
                    ax.plot(point['lon'], point['lat'], 'o', color='blue', markersize=8,
                            markeredgecolor='darkblue', markeredgewidth=1)

                ax.annotate(str(i+1), (point['lon'], point['lat']),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.grid(True, alpha=0.3)

        # Titre et légende
        ax.set_title(f'Parcours Camionnette {truck_number}', fontsize=14, fontweight='bold', pad=20)
        if any(p['is_depot'] for p in points):
            ax.legend(loc='upper right')

        # Sauvegarder en mémoire
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def calculate_route_times(self, route, start_time_str):
        """Calcule les horaires d'arrivée et de départ pour un itinéraire"""
        schedule = []
        current_time = datetime.strptime(start_time_str, "%H:%M")

        # Départ du dépôt
        schedule.append({
            'location': route[0],
            'type': 'depot_start',
            'arrival': current_time.strftime("%H:%M"),
            'departure': current_time.strftime("%H:%M")
        })

        # Visites des pharmacies
        for i in range(1, len(route)):
            current_loc = route[i-1]
            next_loc = route[i]

            # Temps de trajet en minutes (distance.csv est en secondes)
            travel_time_seconds = self.distances[current_loc][next_loc]
            travel_time_minutes = travel_time_seconds // 60

            current_time += timedelta(minutes=travel_time_minutes)
            arrival_time = current_time.strftime("%H:%M")

            # Temps de livraison (3 minutes)
            current_time += timedelta(minutes=self.delivery_duration)
            departure_time = current_time.strftime("%H:%M")

            schedule.append({
                'location': next_loc,
                'type': 'pharmacy',
                'arrival': arrival_time,
                'departure': departure_time
            })

        # Retour au dépôt
        if route[-1] != 0:
            last_loc = route[-1]
            travel_time_seconds = self.distances[last_loc][0]
            travel_time_minutes = travel_time_seconds // 60
            current_time += timedelta(minutes=travel_time_minutes)

            schedule.append({
                'location': 0,
                'type': 'depot_end',
                'arrival': current_time.strftime("%H:%M"),
                'departure': ""
            })

        return schedule

    def calculate_truck_stats(self, route):
        """Calcule les statistiques d'une camionnette"""
        total_distance_seconds = 0

        # Calculer distance totale
        for i in range(len(route)-1):
            total_distance_seconds += self.distances[route[i]][route[i+1]]

        # Retour au dépôt
        if route[-1] != 0:
            total_distance_seconds += self.distances[route[-1]][0]

        # Conversions
        total_minutes = total_distance_seconds / 60
        total_hours = total_minutes / 60

        # Approximation: 50 km/h de vitesse moyenne (à ajuster quand vous aurez les vraies distances)
        distance_km = total_hours * 50

        # Calculs carburant avec les constantes imposées
        fuel_consumption = distance_km * self.fuel_consumption_per_100km / 100
        fuel_cost = fuel_consumption * self.diesel_price_per_liter

        return {
            'total_seconds': total_distance_seconds,
            'total_minutes': total_minutes,
            'total_hours': total_hours,
            'distance_km': distance_km,
            'fuel_consumption': fuel_consumption,
            'fuel_cost': fuel_cost
        }

    def generate_truck_pdf(self, truck_route, truck_number, period="morning", output_file=None):
        """Génère le PDF pour une camionnette avec vraie carte GPS"""
        if output_file is None:
            output_file = f"camionnette_{truck_number}_{period}.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        story = []

        # Titre simple
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=15,
            alignment=1  # Centré
        )

        start_time = self.morning_start if period == "morning" else self.afternoon_start
        title = f"Parcours Camionnette {truck_number}"
        story.append(Paragraph(title, title_style))

        # Créer et ajouter la carte directement dans le PDF
        map_image = self.create_static_map_image(truck_route, truck_number)
        if map_image:
            story.append(Image(map_image, width=16*cm, height=12*cm))
            story.append(Spacer(1, 15))

        # Calculer les horaires
        schedule = self.calculate_route_times(truck_route, start_time)

        # Tableau compact et simple
        data = [["Destination", "Adresse", "Arrivée", "Départ"]]

        for item in schedule:
            loc_idx = item['location']
            pharmacy = self.pharmacies.get(loc_idx, {
                'nom': f'Pharmacie {loc_idx}',
                'adresse_complete': 'Adresse inconnue'
            })

            if item['type'] == 'depot_start':
                name = "Départ CERP"
            elif item['type'] == 'depot_end':
                name = "Retour CERP"
            else:
                name = pharmacy['nom']

            data.append([
                name,
                pharmacy['adresse_complete'],
                item['arrival'],
                item['departure'] if item['departure'] else ""
            ])

        # Tableau BEAUCOUP plus large - prend presque toute la largeur A4
        table = Table(data, colWidths=[4*cm, 10*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(table)
        story.append(Spacer(1, 15))

        # Statistiques compactes
        stats = self.calculate_truck_stats(truck_route)

        stats_data = [
            ["Distance totale:", f"{stats['distance_km']:.1f} km"],
            ["Carburant:", f"{stats['fuel_consumption']:.2f} L"],
            ["Coût carburant:", f"{stats['fuel_cost']:.2f} €"],
            ["Durée:", f"{stats['total_hours']:.1f}h ({stats['total_minutes']:.0f} min)"]
        ]

        stats_table = Table(stats_data, colWidths=[4*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        story.append(stats_table)

        # Générer le PDF
        doc.build(story)
        print(f"✅ PDF généré: {output_file}")

        return output_file

    def generate_summary_pdf(self, all_trucks, period="morning", output_file=None):
        """Génère le PDF récapitulatif"""
        if output_file is None:
            output_file = f"recapitulatif_{period}.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4)
        story = []

        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )

        title = f"Récapitulatif CERP - {period.capitalize()}"
        story.append(Paragraph(title, title_style))

        # Statistiques globales
        total_distance = 0
        total_fuel = 0
        total_cost = 0
        total_pharmacies = 0

        summary_data = [["Camionnette", "Pharmacies", "Distance (km)", "Carburant (L)", "Coût (€)"]]

        for truck_num, truck_route in all_trucks.items():
            stats = self.calculate_truck_stats(truck_route)
            total_distance += stats['distance_km']
            total_fuel += stats['fuel_consumption']
            total_cost += stats['fuel_cost']

            pharmacies_count = len([x for x in truck_route if x != 0])
            total_pharmacies += pharmacies_count

            summary_data.append([
                f"Camionnette {truck_num}",
                str(pharmacies_count),
                f"{stats['distance_km']:.1f}",
                f"{stats['fuel_consumption']:.2f}",
                f"{stats['fuel_cost']:.2f}"
            ])

        # Ligne de total
        summary_data.append([
            "TOTAL",
            str(total_pharmacies),
            f"{total_distance:.1f}",
            f"{total_fuel:.2f}",
            f"{total_cost:.2f}"
        ])

        summary_table = Table(summary_data, colWidths=[3*cm, 2*cm, 3*cm, 3*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(summary_table)

        doc.build(story)
        print(f"✅ PDF récapitulatif généré: {output_file}")

        return output_file


def main():
    """Fonction principale"""
    print("=== Générateur de PDF CERP Rouen ===")
    print(f"Dossier courant: {os.getcwd()}")

    # Initialiser le générateur
    generator = CERPDeliveryPDFGenerator()

    if not generator.pharmacies or not generator.distances:
        print("ERREUR: Impossible de charger les données.")
        return

    # Parser le fichier de sortie de votre algorithme
    optimal_route, trucks = generator.parse_route_file()

    if not trucks:
        print("ERREUR: Aucune camionnette trouvée dans route_output.txt")
        return

    print(f"\n🚛 {len(trucks)} camionnette(s) trouvée(s)")

    # Générer les PDF pour chaque camionnette
    period = "morning"  # ou "afternoon"

    for truck_num, truck_route in trucks.items():
        print(f"\n📄 Génération PDF Camionnette {truck_num}")
        generator.generate_truck_pdf(truck_route, truck_num, period)

    # Générer le récapitulatif
    print(f"\n📄 Génération du récapitulatif")
    generator.generate_summary_pdf(trucks, period)

    print(f"\n✅ Terminé! {len(trucks)} PDF + 1 récapitulatif générés")


if __name__ == "__main__":
    main()