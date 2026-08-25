#!/usr/bin/env python3
"""
Generate sample cached data for offline demo mode.
Creates realistic ARGO-like data for Arabian Sea and Bay of Bengal.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Set seed for reproducibility
np.random.seed(42)

# Output directory
CACHE_DIR = Path(__file__).parent.parent / "data" / "cached"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Region definitions
REGIONS = {
    "arabian_sea": {"min_lat": 8.0, "max_lat": 25.0, "min_lon": 60.0, "max_lon": 78.0},
    "bay_of_bengal": {"min_lat": 5.0, "max_lat": 22.0, "min_lon": 80.0, "max_lon": 100.0},
    "kerala_coast": {"min_lat": 8.0, "max_lat": 13.0, "min_lon": 74.0, "max_lon": 77.0},
}

# Generate float positions
def generate_floats(region_name: str, n_floats: int) -> pd.DataFrame:
    region = REGIONS[region_name]
    floats = []
    for i in range(n_floats):
        platform = 1900000 + hash(f"{region_name}_{i}") % 10000
        lat = np.random.uniform(region["min_lat"], region["max_lat"])
        lon = np.random.uniform(region["min_lon"], region["max_lon"])
        floats.append({
            "platform_number": platform,
            "deployment_lat": lat,
            "deployment_lon": lon,
            "deployment_date": "2020-01-15",
            "status": "active",
            "wmo_inst_type": "846",
            "project_name": "ARGO",
        })
    return pd.DataFrame(floats)

# Generate profiles for a float (reduced: only 2024-2025)
def generate_profiles(float_df: pd.DataFrame, start_date: str, end_date: str, cycle_interval_days: int = 10) -> pd.DataFrame:
    profiles = []
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    for _, float_row in float_df.iterrows():
        platform = float_row["platform_number"]
        base_lat = float_row["deployment_lat"]
        base_lon = float_row["deployment_lon"]
        
        current = start
        cycle = 1
        while current <= end:
            lat = base_lat + np.random.normal(0, 0.1)
            lon = base_lon + np.random.normal(0, 0.1)
            
            lat = np.clip(lat, -30, 30)
            lon = np.clip(lon, 30, 120)
            
            profiles.append({
                "platform_number": platform,
                "cycle_number": cycle,
                "profile_time": current.isoformat(),
                "latitude": lat,
                "longitude": lon,
                "direction": "A" if cycle % 2 == 1 else "D",
                "data_mode": "D",
                "position_qc": 1,
            })
            current += timedelta(days=cycle_interval_days)
            cycle += 1
    
    return pd.DataFrame(profiles)

# Generate observations for profiles (reduced: 30 levels per profile)
def generate_observations(profiles_df: pd.DataFrame, max_depth: int = 2000) -> pd.DataFrame:
    observations = []
    
    for _, profile in profiles_df.iterrows():
        n_levels = 30  # Fixed small number
        depths = np.linspace(0, max_depth, n_levels)
        
        month = datetime.fromisoformat(profile["profile_time"]).month
        surface_temp = 28 + 2 * np.sin((month - 6) * np.pi / 6) + np.random.normal(0, 0.5)
        
        for depth in depths:
            temp = surface_temp * np.exp(-depth / 500) + 2 + np.random.normal(0, 0.2)
            temp = max(temp, 2.0)
            
            sal = 35.0 + 0.5 * np.exp(-depth / 200) + np.random.normal(0, 0.05)
            
            oxy = 200 * np.exp(-depth / 300) + np.random.normal(0, 10)
            oxy = max(oxy, 0)
            
            chl = 0.5 * np.exp(-depth / 50) + np.random.exponential(0.1)
            
            pressure = depth / 1.0197
            
            observations.append({
                "profile_id": None,
                "pressure_dbar": round(pressure, 1),
                "depth_m": round(depth, 1),
                "temperature_c": round(temp, 2),
                "salinity_psu": round(sal, 2),
                "oxygen_umol_kg": round(oxy, 1),
                "chlorophyll": round(chl, 3),
                "temperature_qc": np.random.choice([1, 2], p=[0.85, 0.15]),
                "salinity_qc": np.random.choice([1, 2], p=[0.9, 0.1]),
                "oxygen_qc": np.random.choice([1, 2], p=[0.8, 0.2]),
            })
    
    return pd.DataFrame(observations)

# Main generation
def main():
    print("Generating sample ARGO data for demo mode...")
    
    all_profiles = []
    all_observations = []
    profile_id_counter = 1
    
    # Reduced date range for faster generation
    for region_name, n_floats in [("arabian_sea", 8), ("bay_of_bengal", 5), ("kerala_coast", 3)]:
        print(f"  Generating {region_name} ({n_floats} floats)...")
        
        floats = generate_floats(region_name, n_floats)
        profiles = generate_profiles(floats, "2024-01-01", "2025-12-31")
        
        profiles["id"] = range(profile_id_counter, profile_id_counter + len(profiles))
        profile_id_counter += len(profiles)
        
        all_profiles.append(profiles)
        
        obs = generate_observations(profiles)
        profile_id_map = dict(zip(
            zip(profiles["platform_number"], profiles["cycle_number"]),
            profiles["id"]
        ))
        obs["profile_id"] = obs.apply(
            lambda row: profile_id_map.get((row.get("platform_number"), row.get("cycle_number")), 1),
            axis=1
        )
        obs = obs.drop(columns=["platform_number", "cycle_number"], errors="ignore")
        
        all_observations.append(obs)
    
    profiles_df = pd.concat(all_profiles, ignore_index=True)
    observations_df = pd.concat(all_observations, ignore_index=True)
    
    observations_df["id"] = range(1, len(observations_df) + 1)
    observations_df["ingested_at"] = datetime.utcnow().isoformat()
    
    profiles_df["source"] = "argo_gdac"
    profiles_df["source_url"] = "https://data-argo.ifremer.fr/argo"
    profiles_df["qc_status"] = "recommended"
    profiles_df["created_at"] = datetime.utcnow().isoformat()
    
    # Save as Parquet
    profiles_path = CACHE_DIR / "demo_profiles.parquet"
    observations_path = CACHE_DIR / "demo_observations.parquet"
    
    profiles_df.to_parquet(profiles_path, compression="snappy")
    observations_df.to_parquet(observations_path, compression="snappy")
    
    print(f"Saved {len(profiles_df)} profiles to {profiles_path}")
    print(f"Saved {len(observations_df)} observations to {observations_path}")
    
    # Generate manifest
    manifest = {
        "dataset_name": "argo_indian_ocean_demo",
        "version": "1.0.0",
        "description": "Demo dataset for FloatChat MVP - Indian Ocean ARGO profiles 2024-2025",
        "region": "Indian Ocean (30°S-30°N, 30°E-120°E) - Focus: Arabian Sea, Bay of Bengal, Kerala Coast",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2025-12-31T23:59:59Z",
        "source": "Synthetic demo data (based on ARGO climatology)",
        "source_version": "demo-2026",
        "record_count": int(len(observations_df)),
        "profile_count": int(len(profiles_df)),
        "float_count": int(profiles_df["platform_number"].nunique()),
        "ingested_at": datetime.utcnow().isoformat(),
        "checksum": hashlib.md5(
            f"{len(profiles_df)}_{len(observations_df)}".encode()
        ).hexdigest(),
        "status": "active",
        "supported_demo_questions": [
            "Show temperature profiles in the Arabian Sea during July 2025",
            "What is the salinity trend near Kerala coast?",
            "Compare oxygen levels in Bay of Bengal vs Arabian Sea",
            "നാളെ 40 കിലോമീറ്റർ കടലിലേക്ക് പോകുന്നത് സുരക്ഷിതമാണോ?",
            "Explain unusual warming at 100m depth in Arabian Sea",
            "What if current warming continues for 5 years?",
        ],
        "files": {
            "profiles": "demo_profiles.parquet",
            "observations": "demo_observations.parquet",
        }
    }
    
    manifest_path = CACHE_DIR / "demo_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    
    print(f"Saved manifest to {manifest_path}")
    print("\nDemo data generation complete!")
    print(f"Total floats: {manifest['float_count']}")
    print(f"Total profiles: {manifest['profile_count']}")
    print(f"Total observations: {manifest['record_count']}")

if __name__ == "__main__":
    main()