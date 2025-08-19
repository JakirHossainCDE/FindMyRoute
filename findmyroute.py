"""
FindMyRoute - Extract Tourist Attractions from OpenStreetMap
Improved version to ensure exactly 20 attractions with valid names
"""
import os
import json
import csv
import osmnx as ox
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Configure OSMnx settings
ox.settings.use_cache = True
ox.settings.cache_folder = "./osmnx_cache"
ox.settings.log_console = True

@dataclass
class TouristAttraction:
    """Represents a tourist attraction with extended information"""
    id: int
    name: str
    lat: float
    lng: float
    category: str
    icon: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.lat,
            'lng': self.lng,
            'category': self.category,
            'icon': self.icon
        }
    
    def to_list(self):
        return [
            self.id,
            self.name,
            self.lat,
            self.lng,
            self.category,
            self.icon
        ]

def determine_category(tags: Dict) -> Tuple[str, str]:
    """Determine category and icon based on OSM tags"""
    if isinstance(tags, str):
        return 'Attraction', 'info'
        
    if 'tourism' in tags:
        if tags['tourism'] == 'museum':
            return 'Museum', 'museum'
        elif tags['tourism'] == 'attraction':
            return 'Landmark', 'landmark'
        elif tags['tourism'] == 'gallery':
            return 'Museum', 'museum'
        elif tags['tourism'] == 'viewpoint':
            return 'Viewpoint', 'binoculars'
    
    if 'historic' in tags:
        if tags['historic'] == 'castle':
            return 'Historic Site', 'historic'
        elif tags['historic'] == 'monument':
            return 'Landmark', 'landmark'
        elif tags['historic'] == 'memorial':
            return 'Memorial', 'memorial'
    
    if 'shop' in tags:
        return 'Shopping', 'shop'
    
    if 'amenity' in tags and tags['amenity'] == 'place_of_worship':
        return 'Religious Site', 'religious'
    
    if 'leisure' in tags and tags['leisure'] == 'park':
        return 'Park', 'park'
    
    return 'Attraction', 'info'

def get_valid_name(tags: Dict, idx: int) -> Optional[str]:
    """Extract a valid name from tags or generate one"""
    name = tags.get('name', None)
    
    if name and isinstance(name, str) and name.strip():
        return name.strip()
    
    # Try alternative name fields
    for field in ['name:en', 'official_name', 'short_name', 'alt_name']:
        if field in tags and isinstance(tags[field], str) and tags[field].strip():
            return tags[field].strip()
    
    # Generate a name based on category if possible
    category, _ = determine_category(tags)
    if category != 'Attraction':
        return f"{category} {idx}"
    
    return None

def load_city_attractions(city_name: str, max_attractions: int = 20) -> List[TouristAttraction]:
    """
    Load exactly 20 tourist attractions from OpenStreetMap with valid names
    
    Args:
        city_name: Name of the city to load data for
        max_attractions: Maximum number of attractions to return
        
    Returns:
        List of TouristAttraction objects
    """
    try:
        print(f"Loading attractions for {city_name}...")
        tags = {
            'tourism': ['attraction', 'museum', 'gallery', 'viewpoint', 'zoo', 'theme_park'],
            'historic': ['monument', 'castle', 'memorial', 'archaeological_site'],
            'amenity': ['place_of_worship', 'fountain', 'theatre'],
            'leisure': ['park', 'garden', 'nature_reserve'],
            'building': ['church', 'cathedral', 'mosque', 'temple'],
            'shop': ['gift', 'souvenir', 'art']
        }
        
        gdf = ox.features_from_place(city_name, tags)
        attractions = []
        idx = 1
        
        for _, row in gdf.iterrows():
            if len(attractions) >= max_attractions:
                break
                
            if hasattr(row.geometry, 'y') and hasattr(row.geometry, 'x'):
                tags_dict = dict(row.dropna())
                name = get_valid_name(tags_dict, idx)
                
                if name is None:
                    continue
                    
                category, icon = determine_category(tags_dict)
                
                attractions.append(
                    TouristAttraction(
                        id=idx,
                        name=name,
                        lat=row.geometry.y,
                        lng=row.geometry.x,
                        category=category,
                        icon=icon
                    )
                )
                idx += 1
                
        # If we didn't get enough attractions, try with broader tags
        if len(attractions) < max_attractions:
            print(f"Only found {len(attractions)} attractions, trying with broader search...")
            backup_tags = {'tourism': True, 'historic': True, 'amenity': True}
            backup_gdf = ox.features_from_place(city_name, backup_tags)
            
            for _, row in backup_gdf.iterrows():
                if len(attractions) >= max_attractions:
                    break
                    
                if hasattr(row.geometry, 'y') and hasattr(row.geometry, 'x'):
                    tags_dict = dict(row.dropna())
                    if 'id' in tags_dict:  # Skip if it's just a node/way without proper tags
                        continue
                        
                    name = get_valid_name(tags_dict, idx)
                    if name is None:
                        continue
                        
                    # Skip if we already have this attraction
                    if any(a.name == name for a in attractions):
                        continue
                        
                    category, icon = determine_category(tags_dict)
                    
                    attractions.append(
                        TouristAttraction(
                            id=idx,
                            name=name,
                            lat=row.geometry.y,
                            lng=row.geometry.x,
                            category=category,
                            icon=icon
                        )
                    )
                    idx += 1
        
        if len(attractions) < max_attractions:
            print(f"Warning: Only found {len(attractions)} valid attractions")
            
        return attractions[:max_attractions]
    
    except Exception as e:
        raise RuntimeError(f"Failed to load city attractions: {str(e)}")

def save_to_json(attractions: List[TouristAttraction], filename: str) -> None:
    """
    Save attractions information to JSON file
    
    Args:
        attractions: List of attractions to save
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([a.to_dict() for a in attractions], f, indent=2, ensure_ascii=False)

def save_to_csv(attractions: List[TouristAttraction], filename: str) -> None:
    """
    Save attractions information to CSV file
    
    Args:
        attractions: List of attractions to save
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['id', 'name', 'latitude', 'longitude', 'category', 'icon'])
        # Write data
        for attraction in attractions:
            writer.writerow(attraction.to_list())

def extract_attractions(city: str = "Salzburg, Austria", output_dir: str = 'output') -> None:
    """
    Main function to extract exactly 20 tourist attractions with valid data
    
    Args:
        city: City name to extract attractions from
        output_dir: Directory to save outputs
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        attractions = load_city_attractions(city)
        
        base_name = city.replace(', ', '_').replace(' ', '_').lower()
        
        # Save to JSON
        json_file = f"{output_dir}/{base_name}_attractions.json"
        save_to_json(attractions, json_file)
        
        # Save to CSV
        csv_file = f"{output_dir}/{base_name}_attractions.csv"
        save_to_csv(attractions, csv_file)
        
        print(f"\n✓ Successfully extracted {len(attractions)} attractions")
        print(f"JSON file saved to: {json_file}")
        print(f"CSV file saved to: {csv_file}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    extract_attractions()