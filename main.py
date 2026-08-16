from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(
    title="Dynamic Counterpick API",
    description="Calculates a complete 5-hero counterpick composition.",
    version="1.0.0"
)

class EnemyComposition(BaseModel):
    tanks: List[str]
    dps: List[str]
    supports: List[str]

# 1. Map every hero to their respective role along with your meta weights
HERO_ROLES = {
    # Tanks
    "D.Mon": "Tank", "D.Va": "Tank", "Domina": "Tank", "Doomfist": "Tank", 
    "Emre": "Tank", "Hazard": "Tank", "Junker Queen": "Tank", "Mauga": "Tank", 
    "Orisa": "Tank", "Ramattra": "Tank", "Reinhardt": "Tank", "Roadhog": "Tank", 
    "Shion": "Tank", "Sierra": "Tank", "Sigma": "Tank", "Winston": "Tank", 
    "Wrecking Ball": "Tank", "Zarya": "Tank",
    
    # Damage (DPS)
    "Anran": "DPS", "Ashe": "DPS", "Bastion": "DPS", "Cassidy": "DPS", 
    "Echo": "DPS", "Freja": "DPS", "Genji": "DPS", "Hanzo": "DPS", 
    "Junkrat": "DPS", "Mei": "DPS", "Pharah": "DPS", "Reaper": "DPS", 
    "Sojourn": "DPS", "Soldier: 76": "DPS", "Sombra": "DPS", "Symmetra": "DPS", 
    "Torbjörn": "DPS", "Tracer": "DPS", "Vendetta": "DPS", "Venture": "DPS", 
    "Widowmaker": "DPS",
    
    # Support
    "Ana": "Support", "Baptiste": "Support", "Brigitte": "Support", "Illari": "Support", 
    "Jetpack Cat": "Support", "Juno": "Support", "Kiriko": "Support", "Lifeweaver": "Support", 
    "Lúcio": "Support", "Mercy": "Support", "Mizuki": "Support", "Moira": "Support", 
    "Wuyang": "Support", "Zenyatta": "Support"
}

META_WEIGHTS = {
    "D.Mon": 0.8, "Ana": 1.0, "Anran": 1.0, "Ashe": 0.85, "Baptiste": 0.8,
    "Bastion": 1.15, "Brigitte": 1.0, "Cassidy": 1.15, "D.Va": 1.15, "Domina": 0.7,
    "Doomfist": 0.85, "Echo": 1.0, "Emre": 1.15, "Freja": 1.3, "Genji": 0.85,
    "Hanzo": 0.85, "Hazard": 1.0, "Illari": 0.85, "Jetpack Cat": 1.45, "Junker Queen": 0.7,
    "Junkrat": 0.35, "Juno": 1.15, "Kiriko": 1.8, "Lifeweaver": 0.55, "Lúcio": 1.15,
    "Mauga": 1.5, "Mei": 1.15, "Mercy": 0.7, "Mizuki": 1.0, "Moira": 0.7,
    "Orisa": 1.0, "Pharah": 1.15, "Ramattra": 1.45, "Reaper": 1.0, "Reinhardt": 0.7,
    "Roadhog": 0.85, "Shion": 1.15, "Sierra": 0.7, "Sigma": 1.5, "Sojourn": 1.45,
    "Soldier: 76": 0.55, "Sombra": 0.55, "Symmetra": 1.3, "Torbjörn": 0.8, "Tracer": 1.3,
    "Vendetta": 1.15, "Venture": 0.85, "Widowmaker": 1.0, "Winston": 0.7,
    "Wrecking Ball": 1.0, "Wuyang": 1.0, "Zarya": 1.1, "Zenyatta": 0.7
}

MATCHUP_SCORES = {
    "Winston": {"Genji": 50, "Widowmaker": 40, "Reaper": -40, "Bastion": -50},
    "Reaper": {"Winston": 50, "Roadhog": 40, "Pharah": -50, "Domina": 20},
    "Cassidy": {"Tracer": 40, "Genji": 30},
    "Kiriko": {"Ana": 20, "Zenyatta": 30},
    "D.Va": {"Winston": 30, "Pharah": 40}
}

@app.post("/api/v1/calculate-composition/")
def calculate_composition(enemy_team: EnemyComposition):
    enemies = enemy_team.tanks + enemy_team.dps + enemy_team.supports
    
    # Score every single hero in the game against this enemy comp
    scored_heroes = {}
    
    for hero in META_WEIGHTS.keys():
        matchups = MATCHUP_SCORES.get(hero, {})
        score = 0
        
        for enemy in enemies:
            if enemy in matchups:
                score += matchups[enemy]
                
        # Base multiplier + fallback so unmapped heroes are evaluated strictly by meta weight
        meta_multiplier = META_WEIGHTS.get(hero, 1.0)
        final_score = (score + 100) * meta_multiplier # Offset ensures even neutral heroes get ranked by meta
        
        role = HERO_ROLES.get(hero, "Unknown")
        if role not in scored_heroes:
            scored_heroes[role] = []
            
        scored_heroes[role].append({"hero": hero, "score": round(final_score, 1)})
        
    # Sort each role by highest score descending
    for role in scored_heroes:
        scored_heroes[role] = sorted(scored_heroes[role], key=lambda x: x["score"], reverse=True)
        
    # Assemble the ideal 5-player composition (1 Tank, 2 DPS, 2 Supports)
    recommended_comp = {
        "Tank": scored_heroes.get("Tank", [])[:1],
        "DPS": scored_heroes.get("DPS", [])[:2],
        "Support": scored_heroes.get("Support", [])[:2]
    }
    
    return {
        "enemy_analyzed": enemies,
        "recommended_composition": recommended_comp
    }