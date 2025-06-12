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
        self.depot_address = "600 Rue des Madeleines, 77100 Mareuil-lès-Meaux"
        self.styles = getSampleStyleSheet()

        self.morning_start = "09:00"
        self.afternoon_start = "15:00"
        self.delivery_duration = 3

        self.fuel_consumption_per_100km = 6.5  # L/100km
        self.diesel_price_per_liter = 1.72  # €/L

        # TODO : REPLACE par le code en commentaire POUR LANCER AVEC STREAMLIT
        pharmacies_file = os.path.join("Python", "sources", "pharmacies_coordonnees.csv")
        time_file = os.path.join("Python", "sources", "time.csv")
        meters_file = os.path.join("Python", "sources", "meters.csv")

        # pharmacies_file = os.path.join("sources", "pharmacies_coordonnees.csv")
        # time_file = os.path.join("sources", "time.csv")
        # meters_file = os.path.join("sources", "meters.csv")

        print(f"Chargement pharmacies: {pharmacies_file}")
        print(f"Chargement temps: {time_file}")
        print(f"Chargement distances: {meters_file}")

        self.pharmacies = self.load_pharmacies(pharmacies_file)
        self.time_matrix = self.load_time_matrix(time_file)
        self.distance_matrix = self.load_distance_matrix(meters_file)

        self.all_routes_data = {}

    def load_pharmacies(self, file_path):
        pharmacies = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                pharmacies[0] = {
                    'nom': 'Dépôt CERP Rouen',
                    'adresse': '600 Rue des Madeleines',
                    'code_postal': '77100',
                    'ville': 'Mareuil-lès-Meaux',
                    'adresse_complete': self.depot_address,
                    'latitude': 48.9341,
                    'longitude': 2.8738
                }

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

        return pharmacies

    def load_distances(self, file_path):
        distances = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)

                for row in reader:
                    distances.append([int(float(x)) for x in row])

        except Exception as e:
            print(f"ERREUR chargement distances: {e}")
            return []

        return distances

    def load_time_matrix(self, file_path):
        time_matrix = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)

                for row in reader:
                    time_matrix.append([float(x) / 60 for x in row[1:]])

        except Exception as e:
            print(f"ERREUR chargement time.csv: {e}")
            return []

        return time_matrix

    def load_distance_matrix(self, file_path):
        distance_matrix = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)

                for row in reader:
                    distance_matrix.append([float(x) / 1000.0 for x in row[1:]])

        except Exception as e:
            print(f"ERREUR {e}")
            return []

        return distance_matrix

    # TODO : ENELVER ".." POUR LANCER AVEC STREAMLIT
    def parse_route_file(self, route_file=os.path.join("data", "output.txt")):
        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            lines = content.split('\n')
            print(f"Contenu du fichier output.txt:")
            for i, line in enumerate(lines):
                print(f"  Ligne {i}: {line}")

            trucks = {}
            all_routes = []

            for truck_num, line in enumerate(lines, 1):
                if line.strip():
                    route_str = line.strip('[]')
                    route = [int(x.strip()) for x in route_str.split(',') if x.strip()]

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

    def decode_polyline(self, encoded):
        """
        Décode une polyline encodée au format Google
        Retourne une liste de coordonnées [lat, lon]
        """
        coordinates = []
        index = 0
        len_encoded = len(encoded)
        lat = 0
        lng = 0

        while index < len_encoded:
            # Décoder la latitude
            b = 0
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break

            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat

            # Décoder la longitude
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break

            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lng += dlng

            # Ajouter les coordonnées (lat/lon en degrés * 1e5)
            coordinates.append([lat * 1e-5, lng * 1e-5])

        return coordinates

    def fetch_all_routes_openrouteservice(self, all_trucks):
        """
        Récupère les routes détaillées via l'API OpenRouteService
        """
        API_KEY = "5b3ce3597851110001cf62482cb15bb058ef4ee5b65525786431e0cb"

        if API_KEY == "VOTRECLEAPI":
            print("⚠️ Clé API non configurée.")
            return

        for truck_num, truck_route in all_trucks.items():
            print(f"\n📍 Traitement camionnette {truck_num}...")

            # Construire la liste des coordonnées
            coordinates = []
            for loc_idx in truck_route:
                if loc_idx in self.pharmacies:
                    pharmacy = self.pharmacies[loc_idx]
                    coordinates.append([pharmacy['longitude'], pharmacy['latitude']])

            # Ajouter le retour au dépôt si nécessaire
            if truck_route[-1] != 0:
                depot = self.pharmacies[0]
                coordinates.append([depot['longitude'], depot['latitude']])

            if len(coordinates) < 2:
                print(f"⚠️ Pas assez de points pour la camionnette {truck_num}")
                continue

            try:
                # Configuration de la requête
                url = "https://api.openrouteservice.org/v2/directions/driving-car"

                headers = {
                    'Authorization': API_KEY,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8'
                }

                # Corps de la requête
                body = {
                    "coordinates": coordinates,
                    "elevation": False,
                    "geometry": True  # On veut la géométrie
                }

                print(f"  Envoi requête avec {len(coordinates)} points")

                # Envoi de la requête
                response = requests.post(url, json=body, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    # Vérifier la structure de la réponse
                    if 'routes' in data and len(data['routes']) > 0:
                        route_data = data['routes'][0]

                        # Récupérer et traiter la géométrie
                        if 'geometry' in route_data:
                            geometry = route_data['geometry']

                            # Cas 1: Polyline encodée (string)
                            if isinstance(geometry, str):
                                print(f"  Décodage polyline pour camionnette {truck_num}")
                                decoded_coords = self.decode_polyline(geometry)
                                self.all_routes_data[truck_num] = decoded_coords
                                print(f"  ✓ Route décodée: {len(decoded_coords)} points")

                            # Cas 2: GeoJSON (dict avec coordinates)
                            elif isinstance(geometry, dict) and 'coordinates' in geometry:
                                route_coords = [[coord[1], coord[0]] for coord in geometry['coordinates']]
                                self.all_routes_data[truck_num] = route_coords
                                print(f"  ✓ Route GeoJSON: {len(route_coords)} points")

                            # Cas 3: Liste de coordonnées directe
                            elif isinstance(geometry, list):
                                route_coords = [[coord[1], coord[0]] for coord in geometry]
                                self.all_routes_data[truck_num] = route_coords
                                print(f"  ✓ Route directe: {len(route_coords)} points")

                            else:
                                print(f"  ⚠️ Format de géométrie non reconnu: {type(geometry)}")
                                # Fallback: utiliser les points de passage
                                self._use_fallback_route(truck_num, truck_route)

                        # Afficher les statistiques de la route
                        if 'summary' in route_data:
                            summary = route_data['summary']
                            distance_km = summary.get('distance', 0) / 1000
                            duration_min = summary.get('duration', 0) / 60
                            print(f"  📊 Distance: {distance_km:.1f} km, Durée: {duration_min:.0f} min")

                    else:
                        print(f"  ⚠️ Pas de route trouvée dans la réponse")
                        self._use_fallback_route(truck_num, truck_route)

                elif response.status_code == 401:
                    print(f"  ❌ Erreur d'authentification. Vérifiez votre clé API.")
                    self._use_fallback_route(truck_num, truck_route)

                elif response.status_code == 429:
                    print(f"  ❌ Limite de requêtes atteinte. Réessayez plus tard.")
                    self._use_fallback_route(truck_num, truck_route)

                else:
                    print(f"  ❌ Erreur API: {response.status_code}")
                    print(f"  Réponse: {response.text[:200]}...")
                    self._use_fallback_route(truck_num, truck_route)

            except requests.exceptions.Timeout:
                print(f"  ⏱️ Timeout pour camionnette {truck_num}")
                self._use_fallback_route(truck_num, truck_route)

            except requests.exceptions.ConnectionError:
                print(f"  🌐 Erreur de connexion pour camionnette {truck_num}")
                self._use_fallback_route(truck_num, truck_route)

            except Exception as e:
                print(f"  ❌ Erreur inattendue pour camionnette {truck_num}: {e}")
                import traceback
                traceback.print_exc()
                self._use_fallback_route(truck_num, truck_route)

        print(f"\n✅ Traitement terminé. {len(self.all_routes_data)} routes récupérées.")

    def _use_fallback_route(self, truck_num, truck_route):
        """
        Utilise une route simplifiée en cas d'échec de l'API
        """
        print(f"  → Utilisation route simplifiée pour camionnette {truck_num}")
        simple_coords = []
        for loc_idx in truck_route:
            if loc_idx in self.pharmacies:
                pharmacy = self.pharmacies[loc_idx]
                simple_coords.append([pharmacy['latitude'], pharmacy['longitude']])

        if truck_route[-1] != 0:
            depot = self.pharmacies[0]
            simple_coords.append([depot['latitude'], depot['longitude']])

        self.all_routes_data[truck_num] = simple_coords

    def create_map_image(self, route, truck_number):
        if not route or len(route) < 2:
            return None

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

        lats = [p['lat'] for p in points]
        lons = [p['lon'] for p in points]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        margin_lat = max(0.01, lat_range * 0.15)
        margin_lon = max(0.01, lon_range * 0.15)

        min_lat -= margin_lat
        max_lat += margin_lat
        min_lon -= margin_lon
        max_lon += margin_lon

        fig, ax = plt.subplots(figsize=(12, 10))
        use_contextily = CONTEXTILY_AVAILABLE

        if use_contextily:
            try:
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

                west, south = transformer.transform(min_lon, min_lat)
                east, north = transformer.transform(max_lon, max_lat)

                ax.set_xlim(west, east)
                ax.set_ylim(south, north)

                ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.CartoDB.Positron, zoom=12)

                for point in points:
                    point['x'], point['y'] = transformer.transform(point['lon'], point['lat'])

                if truck_number in self.all_routes_data:
                    route_geometry = self.all_routes_data[truck_number]
                    route_x, route_y = [], []
                    for coord in route_geometry:
                        x, y = transformer.transform(coord[1], coord[0])
                        route_x.append(x)
                        route_y.append(y)
                    ax.plot(route_x, route_y, 'blue', linewidth=3, alpha=0.8, zorder=5)

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
                use_contextily = False

        if not use_contextily:
            ax.set_xlim(min_lon, max_lon)
            ax.set_ylim(min_lat, max_lat)
            ax.set_facecolor('#e6f3ff')

            if truck_number in self.all_routes_data:
                route_geometry = self.all_routes_data[truck_number]
                route_lats = [coord[0] for coord in route_geometry]
                route_lons = [coord[1] for coord in route_geometry]
                ax.plot(route_lons, route_lats, 'blue', linewidth=3, alpha=0.8)

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

        ax.set_title(f'Parcours Camionnette {truck_number}', fontsize=14, fontweight='bold', pad=20)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close()

        try:
            img = PILImage.open(img_buffer)
            compressed_buffer = io.BytesIO()
            img.save(compressed_buffer, format='PNG', optimize=True, compress_level=6)
            compressed_buffer.seek(0)
            return compressed_buffer
        except Exception as e:
            return img_buffer

    def calculate_route_times(self, route, start_time_str):
        schedule = []
        current_time = datetime.strptime(start_time_str, "%H:%M")

        # Départ -> dépôt
        schedule.append({
            'location': route[0],
            'type': 'depot_start',
            'arrival': current_time.strftime("%H:%M"),
            'departure': current_time.strftime("%H:%M")
        })

        # Livraison pharma
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

        # Retour -> dépôt
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
        os.makedirs("generated", exist_ok=True)
        output_file = f"generated/parcours_camionnette_{truck_number}.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4, topMargin=1 * cm, bottomMargin=1 * cm,
                                leftMargin=1.5 * cm, rightMargin=1.5 * cm)
        story = []

        try:
            # TODO : ENELVER ".." POUR LANCER AVEC STREAMLIT
            logo_path = os.path.join("data", "CERP_logo.png")
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
            print(f"{e}")

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

        map_image = self.create_map_image(truck_route, truck_number)
        if map_image:
            story.append(Image(map_image, width=14 * cm, height=10.5 * cm))
            story.append(Spacer(1, 10))

        schedule = self.calculate_route_times(truck_route, start_time)

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

        table = Table(data, colWidths=[5.5 * cm, 8.5 * cm, 2.5 * cm, 2.5 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
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

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            alignment=0
        )

        story.append(Paragraph("Informations générales", subtitle_style))

        stats = self.calculate_truck_stats(truck_route)

        stats_data = [
            ["Distance totale:", f"{stats['distance_km']:.1f} km"],
            ["Carburant:", f"{stats['fuel_consumption']:.2f} L"],
            ["Coût carburant:", f"{stats['fuel_cost']:.2f} €"],
            ["Durée:", f"{int(stats['total_hours'])}h{int(stats['total_minutes'] % 60):02d}"]
        ]

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

        return output_file

    def generate_summary_pdf(self, all_trucks, period="morning"):
        os.makedirs("generated", exist_ok=True)
        output_file = f"generated/recapitulatif_parcours.pdf"

        doc = SimpleDocTemplate(output_file, pagesize=A4)
        story = []

        try:
            # TODO : ENELVER ".." POUR LANCER AVEC STREAMLIT
            logo_path = os.path.join("data", "CERP_logo.png")
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
            print(f"{e}")

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )

        title = f"Récapitulatif Parcours CERP"
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

        return output_file

    # TODO : REPLACE main PAR generate_pdf

# TODO : MAXIME jsp comment on modifie le main

def main():
    print("🚚 Génération des PDF de tournées CERP Rouen")
    print("=" * 50)

    generator = CERPDeliveryPDFGenerator()

    if not generator.pharmacies or not generator.time_matrix or not generator.distance_matrix:
        print("Impossible de charger les données.")
        return

    optimal_route, trucks = generator.parse_route_file()

    if not trucks:
        print("❌ Aucune camionnette trouvée dans le fichier output")
        return

    print(f"\n📡 Récupération des itinéraires GPS via OpenRouteService...")
    generator.fetch_all_routes_openrouteservice(trucks)

    period = "morning"

    print(f"\n📄 Génération des PDF...")
    for truck_num, truck_route in trucks.items():
        output_file = generator.generate_truck_pdf(truck_route, truck_num, period)
        print(f"  ✓ Camionnette {truck_num}: {output_file}")

    summary_file = generator.generate_summary_pdf(trucks, period)
    print(f"  ✓ Récapitulatif: {summary_file}")

    print(f"\n✅ Les {len(trucks)} PDF et le récapitulatif ont été générés avec succès!")


# TODO : REPLACE main PAR generate_pdf

if __name__ == "__main__":
    main()