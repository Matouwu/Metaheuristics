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
import matplotlib.pyplot as plt
from PIL import Image as PILImage

try:
    import contextily as ctx
    from pyproj import Transformer

    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False


class CERPDeliveryPDFGenerator:
    def __init__(self):
        """Initialise le générateur de PDF"""
        self.depot_address = "600 Rue des Madeleines, 77100 Mareuil-lès-Meaux"
        self.styles = getSampleStyleSheet()

        # Configuration des horaires
        self.morning_start = "09:00"
        self.afternoon_start = "15:00"
        self.delivery_duration = 3  # minutes par livraison

        # Constantes imposées
        self.fuel_consumption_per_100km = 6.5  # L/100km
        self.diesel_price_per_liter = 1.72  # €/L

        # Chemins des fichiers
        pharmacies_file = os.path.join("sources", "pharmacies_coordonnees.csv")
        time_file = os.path.join("sources", "time.csv")
        meters_file = os.path.join("sources", "meters.csv")

        print(f"Chargement pharmacies: {pharmacies_file}")
        print(f"Chargement temps: {time_file}")
        print(f"Chargement distances: {meters_file}")

        self.pharmacies = self.load_pharmacies(pharmacies_file)
        self.time_matrix = self.load_time_matrix(time_file)
        self.distance_matrix = self.load_distance_matrix(meters_file)

    def load_pharmacies(self, file_path):
        """Charge les pharmacies avec coordonnées GPS"""
        pharmacies = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Dépôt à l'index 0
                pharmacies[0] = {
                    'nom': 'Dépôt CERP Rouen',
                    'adresse': '600 Rue des Madeleines',
                    'code_postal': '77100',
                    'ville': 'Mareuil-lès-Meaux',
                    'adresse_complete': self.depot_address,
                    'latitude': 48.9341,
                    'longitude': 2.8738
                }

                # Pharmacies index 1 à 84
                for i, row in enumerate(reader, 1):
                    pharmacies[i] = {
                        'nom': row['nom'].strip(),
                        'adresse': row['adresse'].strip(),
                        'code_postal': str(row['code_postal']).strip(),
                        'ville': row['ville'].strip(),
                        'adresse_complete': f"{row['adresse'].strip()}, {row['code_postal']} {row['ville'].strip()}",
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude'])
                    }

        except Exception as e:
            print(f"ERREUR chargement pharmacies: {e}")
            return {}

        print(f"✅ Chargé {len(pharmacies) - 1} pharmacies + 1 dépôt")
        return pharmacies

    def load_distances(self, file_path):
        """Charge la matrice des distances"""
        distances = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                for row in reader:
                    distances.append([int(float(x)) for x in row])

        except Exception as e:
            print(f"ERREUR chargement distances: {e}")
            return []

        print(f"✅ Matrice distances: {len(distances)}x{len(distances[0]) if distances else 0}")
        return distances

    def load_time_matrix(self, file_path):
        """Charge la matrice des temps depuis time.csv"""
        time_matrix = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                for row in reader:
                    # Convertir de secondes en minutes
                    time_matrix.append([float(x) / 60 for x in row[1:]])  # Skip première colonne, convertir sec->min

        except Exception as e:
            print(f"ERREUR chargement time.csv: {e}")
            return []

        print(f"✅ Matrice temps: {len(time_matrix)}x{len(time_matrix[0]) if time_matrix else 0}")
        return time_matrix

    def load_distance_matrix(self, file_path):
        """Charge la matrice des distances depuis meters.csv"""
        distance_matrix = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                for row in reader:
                    # Convertir en kilomètres
                    distance_matrix.append([float(x) / 1000.0 for x in row[1:]])  # Skip première colonne, convertir m->km

        except Exception as e:
            print(f"ERREUR chargement meters.csv: {e}")
            return []

        print(f"✅ Matrice distances: {len(distance_matrix)}x{len(distance_matrix[0]) if distance_matrix else 0}")
        return distance_matrix

    def parse_route_file(self, route_file=os.path.join("..", "data", "output.txt")):
        """Parse le nouveau format output.txt avec une ligne par camionnette"""
        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            lines = content.split('\n')
            print(f"Contenu du fichier output.txt:")
            for i, line in enumerate(lines):
                print(f"  Ligne {i}: {line}")

            trucks = {}
            all_routes = []

            # Chaque ligne = une camionnette
            for truck_num, line in enumerate(lines, 1):
                if line.strip():
                    # Parser [17,7,2,14,6,15,1,20,11]
                    route_str = line.strip('[]')
                    route = [int(x.strip()) for x in route_str.split(',') if x.strip()]

                    # Ajouter le dépôt au début
                    truck_route = [0] + route
                    trucks[truck_num] = truck_route
                    all_routes.extend(route)

                    print(f"Camionnette {truck_num}: {truck_route}")

            return all_routes, trucks

        except FileNotFoundError:
            print(f"ERREUR: Fichier {route_file} non trouvé")
            print("Format attendu:")
            print("[17,7,2,14,6,15,1,20,11]")
            print("[5,10,18,8,19,9,16,12,13]")
            print("[3,4]")
            return [], {}
        except Exception as e:
            print(f"ERREUR parsing: {e}")
            return [], {}

    def get_route_coordinates_osrm(self, start_coords, end_coords):
        """Récupère le trajet routier via OSRM"""
        try:
            start_lon, start_lat = start_coords[1], start_coords[0]
            end_lon, end_lat = end_coords[1], end_coords[0]

            url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            params = {'overview': 'full', 'geometries': 'geojson'}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'routes' in data and len(data['routes']) > 0:
                    coordinates = data['routes'][0]['geometry']['coordinates']
                    route_coords = [[coord[1], coord[0]] for coord in coordinates]
                    return route_coords

            return None

        except Exception as e:
            print(f"Erreur OSRM: {e}")
            return None

    def create_map_image(self, route, truck_number):
        """Crée une carte avec trajets routiers OSRM"""
        if not route or len(route) < 2:
            return None

        # Récupérer les coordonnées
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

        if len(points) < 2:
            return None

        # Calculer les limites
        lats = [p['lat'] for p in points]
        lons = [p['lon'] for p in points]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Marges
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        margin_lat = max(0.01, lat_range * 0.15)
        margin_lon = max(0.01, lon_range * 0.15)

        min_lat -= margin_lat
        max_lat += margin_lat
        min_lon -= margin_lon
        max_lon += margin_lon

        # Créer la figure
        fig, ax = plt.subplots(figsize=(12, 10))

        # Essayer contextily pour vraie carte
        use_contextily = CONTEXTILY_AVAILABLE

        if use_contextily:
            try:
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

                west, south = transformer.transform(min_lon, min_lat)
                east, north = transformer.transform(max_lon, max_lat)

                ax.set_xlim(west, east)
                ax.set_ylim(south, north)

                # Carte plus plate vue du dessus
                ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.CartoDB.Positron, zoom=12)

                # Convertir points en Web Mercator
                for point in points:
                    point['x'], point['y'] = transformer.transform(point['lon'], point['lat'])

                # Dessiner trajets OSRM
                for i in range(len(points) - 1):
                    start_point = points[i]
                    end_point = points[i + 1]

                    start_coords = [start_point['lat'], start_point['lon']]
                    end_coords = [end_point['lat'], end_point['lon']]

                    route_coords = self.get_route_coordinates_osrm(start_coords, end_coords)

                    if route_coords and len(route_coords) > 1:
                        route_x, route_y = [], []
                        for coord in route_coords:
                            x, y = transformer.transform(coord[1], coord[0])
                            route_x.append(x)
                            route_y.append(y)

                        ax.plot(route_x, route_y, 'blue', linewidth=3, alpha=0.8, zorder=5)
                    else:
                        ax.plot([start_point['x'], end_point['x']],
                                [start_point['y'], end_point['y']],
                                'blue', linestyle='--', linewidth=2, alpha=0.6, zorder=5)

                # Retour au dépôt
                if len(points) > 1 and not points[-1]['is_depot']:
                    last_point = points[-1]
                    depot_point = points[0]

                    start_coords = [last_point['lat'], last_point['lon']]
                    end_coords = [depot_point['lat'], depot_point['lon']]

                    route_coords = self.get_route_coordinates_osrm(start_coords, end_coords)

                    if route_coords and len(route_coords) > 1:
                        route_x, route_y = [], []
                        for coord in route_coords:
                            x, y = transformer.transform(coord[1], coord[0])
                            route_x.append(x)
                            route_y.append(y)
                        ax.plot(route_x, route_y, 'red', linestyle='--', linewidth=2, alpha=0.7, zorder=5)

                # Dessiner les points
                for i, point in enumerate(points):
                    if point['is_depot']:
                        ax.plot(point['x'], point['y'], 'o', color='red', markersize=15,
                                markeredgecolor='darkred', markeredgewidth=2, zorder=10)
                    else:
                        ax.plot(point['x'], point['y'], 'o', color='blue', markersize=10,
                                markeredgecolor='darkblue', markeredgewidth=1, zorder=10)

                    ax.annotate(str(i + 1), (point['x'], point['y']),
                                xytext=(8, 8), textcoords='offset points',
                                fontsize=9, fontweight='bold', color='black', zorder=11,
                                bbox=dict(boxstyle="circle,pad=0.3", facecolor="white",
                                          edgecolor="black", alpha=0.9))

                ax.set_xticks([])
                ax.set_yticks([])

            except Exception as e:
                print(f"Erreur contextily: {e}")
                use_contextily = False

        # Fallback carte simple
        if not use_contextily:
            ax.set_xlim(min_lon, max_lon)
            ax.set_ylim(min_lat, max_lat)
            ax.set_facecolor('#e6f3ff')

            # Trajets OSRM en coordonnées géographiques
            for i in range(len(points) - 1):
                start_point = points[i]
                end_point = points[i + 1]

                start_coords = [start_point['lat'], start_point['lon']]
                end_coords = [end_point['lat'], end_point['lon']]

                route_coords = self.get_route_coordinates_osrm(start_coords, end_coords)

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

                route_coords = self.get_route_coordinates_osrm(start_coords, end_coords)

                if route_coords and len(route_coords) > 1:
                    route_lats = [coord[0] for coord in route_coords]
                    route_lons = [coord[1] for coord in route_coords]
                    ax.plot(route_lons, route_lats, 'red', linestyle='--', linewidth=2, alpha=0.7)

            # Points
            for i, point in enumerate(points):
                if point['is_depot']:
                    ax.plot(point['lon'], point['lat'], 'o', color='red', markersize=12,
                            markeredgecolor='darkred', markeredgewidth=2)
                else:
                    ax.plot(point['lon'], point['lat'], 'o', color='blue', markersize=8,
                            markeredgecolor='darkblue', markeredgewidth=1)

                ax.annotate(str(i + 1), (point['lon'], point['lat']),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.grid(True, alpha=0.3)

        # Sauvegarder
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close()

        # Compression
        try:
            img = PILImage.open(img_buffer)
            compressed_buffer = io.BytesIO()
            img.save(compressed_buffer, format='PNG', optimize=True, compress_level=6)
            compressed_buffer.seek(0)
            return compressed_buffer
        except Exception as e:
            print(f"Erreur compression: {e}")
            return img_buffer

    def calculate_route_times(self, route, start_time_str):
        """Calcule les horaires d'arrivée et de départ"""
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
            current_loc = route[i - 1]
            next_loc = route[i]

            travel_time_minutes = self.time_matrix[current_loc][next_loc]

            current_time += timedelta(minutes=travel_time_minutes)
            arrival_time = current_time.strftime("%H:%M")

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
            travel_time_minutes = self.time_matrix[last_loc][0]
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
        total_time_minutes = 0
        total_distance_km = 0

        for i in range(len(route) - 1):
            total_time_minutes += self.time_matrix[route[i]][route[i + 1]]
            total_distance_km += self.distance_matrix[route[i]][route[i + 1]]

        if route[-1] != 0:
            total_time_minutes += self.time_matrix[route[-1]][0]
            total_distance_km += self.distance_matrix[route[-1]][0]

        pharmacies_count = len([x for x in route if x != 0])
        total_time_minutes += pharmacies_count * self.delivery_duration

        total_hours = total_time_minutes / 60

        fuel_consumption = total_distance_km * self.fuel_consumption_per_100km / 100
        fuel_cost = fuel_consumption * self.diesel_price_per_liter

        return {
            'total_minutes': total_time_minutes,
            'total_hours': total_hours,
            'distance_km': total_distance_km,
            'fuel_consumption': fuel_consumption,
            'fuel_cost': fuel_cost
        }

    def generate_truck_pdf(self, truck_route, truck_number, period="morning"):
        """Génère le PDF pour une camionnette"""
        # Créer le dossier de sortie
        os.makedirs("../generated", exist_ok=True)
        output_file = f"../generated/parcours_camionnette_{truck_number}.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4, topMargin=1 * cm, bottomMargin=1 * cm,
                                leftMargin=1.5 * cm, rightMargin=1.5 * cm)
        story = []

        # Logo CERP en haut à gauche
        try:
            logo_path = os.path.join("..", "data", "CERP_logo.png")
            if os.path.exists(logo_path):
                logo_table_data = [
                    [Image(logo_path, width=2 * cm, height=1.5 * cm), ""]
                ]
                logo_table = Table(logo_table_data, colWidths=[3.5 * cm, 15 * cm])
                logo_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(logo_table)
                story.append(Spacer(1, 10))
        except Exception as e:
            print(f"Impossible de charger le logo: {e}")

        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=15,
            alignment=1
        )

        start_time = self.morning_start if period == "morning" else self.afternoon_start
        title = f"Parcours Camionnette {truck_number}"
        story.append(Paragraph(title, title_style))

        # Carte
        map_image = self.create_map_image(truck_route, truck_number)
        if map_image:
            story.append(Image(map_image, width=14 * cm, height=10.5 * cm))
            story.append(Spacer(1, 10))

        # Horaires
        schedule = self.calculate_route_times(truck_route, start_time)

        # Tableau avec colonnes ajustées : destination plus large, adresse plus petite avec police réduite
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

        # Tableau avec destination plus large, adresse plus petite
        table = Table(data, colWidths=[5.5 * cm, 8.5 * cm, 2.5 * cm, 2.5 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            # Police plus petite pour les adresses (colonne 1)
            ('FONTSIZE', (1, 1), (1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

        # Sous-titre "Informations générales" aligné à gauche
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            alignment=0  # Aligné à gauche
        )

        story.append(Paragraph("Informations générales", subtitle_style))

        # Statistiques dans un tableau aligné à gauche
        stats = self.calculate_truck_stats(truck_route)

        stats_data = [
            ["Distance totale:", f"{stats['distance_km']:.1f} km"],
            ["Carburant:", f"{stats['fuel_consumption']:.2f} L"],
            ["Coût carburant:", f"{stats['fuel_cost']:.2f} €"],
            ["Durée:", f"{int(stats['total_hours'])}h{int(stats['total_minutes'] % 60):02d}"]
        ]

        # Tableau des stats plus petit et aligné à gauche
        stats_table = Table(stats_data, colWidths=[5 * cm, 4 * cm])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ]))

        story.append(stats_table)

        doc.build(story)
        print(f"✅ PDF généré: {output_file}")

        return output_file

    def generate_summary_pdf(self, all_trucks, period="morning"):
        """Génère le PDF récapitulatif"""
        # Créer le dossier de sortie
        os.makedirs("../generated", exist_ok=True)
        output_file = f"../generated/recapitulatif_parcours.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4)
        story = []

        # Logo CERP en haut à gauche
        try:
            logo_path = os.path.join("..", "data", "CERP_logo.png")
            if os.path.exists(logo_path):
                logo_table_data = [
                    [Image(logo_path, width=3 * cm, height=2 * cm), ""]
                ]
                logo_table = Table(logo_table_data, colWidths=[3.5 * cm, 15 * cm])
                logo_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(logo_table)
                story.append(Spacer(1, 15))
        except Exception as e:
            print(f"Impossible de charger le logo: {e}")

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )

        title = f"Récapitulatif CERP - {period.capitalize()}"
        story.append(Paragraph(title, title_style))

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

        summary_data.append([
            "TOTAL",
            str(total_pharmacies),
            f"{total_distance:.1f}",
            f"{total_fuel:.2f}",
            f"{total_cost:.2f}"
        ])

        summary_table = Table(summary_data, colWidths=[3 * cm, 2 * cm, 3 * cm, 3 * cm, 3 * cm])
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


def generate_pdf():
    """Fonction principale"""
    print("=== Générateur de PDF CERP Rouen ===")

    generator = CERPDeliveryPDFGenerator()

    if not generator.pharmacies or not generator.time_matrix or not generator.distance_matrix:
        print("❌ ERREUR: Impossible de charger les données")
        return

    optimal_route, trucks = generator.parse_route_file()

    if not trucks:
        print("❌ ERREUR: Aucune camionnette trouvée dans output.txt")
        return

    print(f"\n🚛 {len(trucks)} camionnette(s) trouvée(s)")

    period = "morning"

    for truck_num, truck_route in trucks.items():
        print(f"\n📄 Génération PDF Camionnette {truck_num}")
        generator.generate_truck_pdf(truck_route, truck_num, period)

    print(f"\n📄 Génération du récapitulatif")
    generator.generate_summary_pdf(trucks, period)

    print(f"\n✅ Terminé! {len(trucks)} PDF + 1 récapitulatif générés dans ../generated/")


if __name__ == "__generate_pdf__":
    generate_pdf()