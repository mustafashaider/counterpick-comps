from main import SessionLocal, Hero, Matchup, engine, Base

# Updated Hero Roles
HERO_ROLES = {
    # Tank
    "D.Mon": "Tank", "D.Va": "Tank", "Domina": "Tank", "Doomfist": "Tank", 
    "Hazard": "Tank", "Junker Queen": "Tank", "Mauga": "Tank", 
    "Orisa": "Tank", "Ramattra": "Tank", "Reinhardt": "Tank", "Roadhog": "Tank", 
    "Sigma": "Tank", "Winston": "Tank", "Wrecking Ball": "Tank", "Zarya": "Tank",
    
    # Hitscan (DPS)
    "Ashe": "Hitscan", "Bastion": "Hitscan", "Cassidy": "Hitscan", "Emre": "Hitscan", "Hanzo": "Hitscan", 
    "Sojourn": "Hitscan", "Soldier: 76": "Hitscan", "Sierra": "Hitscan", "Freja": "Hitscan", "Widowmaker": "Hitscan",
    
    # Flex (DPS)
    "Anran": "Flex", "Echo": "Flex", "Sombra": "Flex", "Genji": "Flex", 
    "Reaper": "Flex", "Junkrat": "Flex", "Mei": "Flex", "Pharah": "Flex", "Shion": "Flex", 
    "Symmetra": "Flex", "Torbjörn": "Flex", "Vendetta": "Flex", "Venture": "Flex",
    "Tracer": "Flex",
    
    # Support
    "Ana": "Support", "Baptiste": "Support", "Brigitte": "Support", "Illari": "Support", 
    "Jetpack Cat": "Support", "Juno": "Support", "Kiriko": "Support", "Lifeweaver": "Support", 
    "Lúcio": "Support", "Mercy": "Support", "Mizuki": "Support", "Moira": "Support", 
    "Wuyang": "Support", "Zenyatta": "Support"
}

# Updated Meta Weights
META_WEIGHTS = {
    "D.Mon": 0.8, "Ana": 1.0, "Anran": 1.0, "Ashe": 0.85, "Baptiste": 0.8,
    "Bastion": 1.15, "Brigitte": 1.0, "Cassidy": 1.15, "D.Va": 1.15, "Domina": 0.7,
    "Doomfist": 0.85, "Echo": 1.0, "Emre": 1.15, "Freja": 1.3, "Genji": 0.85,
    "Hanzo": 0.85, "Hazard": 1.0, "Illari": 0.85, "Jetpack Cat": 1.35, "Junker Queen": 0.7,
    "Junkrat": 0.45, "Juno": 1.15, "Kiriko": 1.8, "Lifeweaver": 0.55, "Lúcio": 1.15,
    "Mauga": 1.5, "Mei": 1.15, "Mercy": 0.7, "Mizuki": 1.0, "Moira": 0.7,
    "Orisa": 1.0, "Pharah": 1.15, "Ramattra": 1.45, "Reaper": 1.0, "Reinhardt": 0.7,
    "Roadhog": 0.85, "Shion": 1.25, "Sierra": 0.7, "Sigma": 1.5, "Sojourn": 1.45,
    "Soldier: 76": 0.55, "Sombra": 0.55, "Symmetra": 1.15, "Torbjörn": 0.8, "Tracer": 1.25,
    "Vendetta": 1.15, "Venture": 0.85, "Widowmaker": 1.0, "Winston": 0.7,
    "Wrecking Ball": 1.0, "Wuyang": 1.0, "Zarya": 1.1, "Zenyatta": 0.7
}

MATCHUP_SCORES = {
    # Tanks
    "D.Mon": {"Sigma": 50, "Ramattra": -50},
    "D.Va": {"Winston": 30, "Pharah": 40, "Bastion": 20, "Mauga": 20, "Zarya": -60, "Anran": -20, "Echo": -15, "Vendetta": -15, "Brigitte": -30, "Mizuki": -25, "Jetpack Cat": 25},
    "Domina": {"Mauga": -40, "Ramattra": -40, "Reaper": -20},
    "Doomfist": {"Sigma": -40, "Brigitte": -30, "Mizuki": -20},
    "Hazard": {"Winston": 40, "Orisa": -30, "Brigitte": 25, "Mizuki": -20},
    "Junker Queen": {"Winston": 30},
    "Mauga": {"Reaper": -30, "Sigma": -40, "D.Va": -20, "Mei": -30, "Domina": 40, "Ramattra": 30, "Roadhog": 70, "Winston": 70, "Sojourn": -30, "Bastion": 20, "Pharah": 30, "Jetpack Cat": 30},
    "Orisa": {"Zarya": -40, "Hazard": 30, "Reinhardt": 60, "Roadhog": 50},
    "Ramattra": {"Domina": 40, "D.Mon": 50, "Mauga": -30, "Reinhardt": 50, "Zarya": 30, "Sigma": 30},
    "Reinhardt": {"Sigma": 50, "Zarya": 20, "Orisa": -60, "Roadhog": -30, "Ramattra": -50, "Bastion": -40, "Ana": -25, "Zenyatta": -30},
    "Roadhog": {"Reinhardt": 30, "Mauga": -70, "Reaper": -20, "Sigma": -20, "Winston": 40, "Orisa": -50, "Ana": -60, "Zenyatta": -25},
    "Sigma": {"Zarya": -50, "Mauga": 40, "D.Mon": -50, "Doomfist": 40, "Reinhardt": -50, "Roadhog": 20, "Symmetra": -40, "Ramattra": -30},
    "Winston": {"D.Va": -30, "Roadhog": -40, "Genji": 40, "Widowmaker": 40, "Reaper": -40, "Bastion": -50, "Hazard": -40, "Junker Queen": -30, "Mauga": -70, "Wrecking Ball": -10, "Jetpack Cat": -10, "Cassidy": -20, "Freja": -30, "Torbjörn": -40, "Vendetta": -20, "Brigitte": -40, "Soldier: 76": 15, "Mizuki": -30},
    "Wrecking Ball": {"Winston": 10, "Sombra": -50, "Brigitte": -30, "Mizuki": -30},
    "Zarya": {"D.Va": 60, "Sigma": 50, "Reinhardt": -20, "Orisa": 40, "Genji": 30, "Ramattra": -30},

    # Hitscan DPS 
    "Ashe": {"Jetpack Cat": 30, "Pharah": 40},
    "Bastion": {"Jetpack Cat": 20, "Reinhardt": 40, "Winston": 50, "D.Va": -20, "Pharah": 30, "Mauga": -20},
    "Cassidy": {"Tracer": 40, "Winston": 20, "Venture": 30, "Jetpack Cat": 15, "Reaper": 30},
    "Emre": {"Jetpack Cat": 20, "Pharah": 40},
    "Freja": {"Winston": 30, "Pharah": 30},
    "Hanzo": {},
    "Sierra": {},
    "Sojourn": {"Mauga": 30},
    "Soldier: 76": {"Winston": -15, "Pharah": 40},
    "Widowmaker": {"Winston": -40, "Pharah": 30},

    # Flex DPS
    "Anran": {"Genji": 20, "D.Va": 20, "Mizuki": -20},
    "Echo": {"D.Va": 15, "Junkrat": 40, "Mizuki": -20},
    "Genji": {"Zarya": -30, "Winston": -40, "Anran": -20, "Venture": -50, "Juno": -50, "Moira": -30, "Mizuki": -10},
    "Junkrat": {"Pharah": -50, "Echo": -40},
    "Mei": {"Pharah": -40, "Mauga": 30},
    "Pharah": {"D.Va": -40, "Ashe": -40, "Bastion": -30, "Emre": -40, "Widowmaker": -30, "Freja": -30, "Soldier: 76": -40, "Junkrat": 50, "Mei": 40, "Reaper": 50, "Shion": -20, "Mauga": -30, "Jetpack Cat": -30},
    "Reaper": {"Winston": 40, "Roadhog": 20, "Pharah": -50, "Domina": 20, "Mauga": 30, "Cassidy": -30, "Mizuki": -20},
    "Shion": {"Pharah": 20, "Mizuki": -20},
    "Sombra": {"Wrecking Ball": 50, "Mizuki": -20},
    "Symmetra": {"Sigma": 40},
    "Tracer": {"Cassidy": -40, "Mizuki": -20},
    "Torbjörn": {"Winston": 40},
    "Vendetta": {"Winston": 20, "D.Va": 15, "Mizuki": -20},
    "Venture": {"Cassidy": -30, "Genji": 50, "Mizuki": -20},

    # Support
    "Ana": {"Reinhardt": 25, "Roadhog": 60, "Kiriko": -20},
    "Baptiste": {},
    "Brigitte": {"Winston": 40, "Wrecking Ball": 30, "D.Va": 30, "Doomfist": 30, "Hazard": -25},
    "Illari": {},
    "Jetpack Cat": {"Emre": -20, "Ashe": -30, "Bastion": -20, "Cassidy": -15, "Winston": 10, "Pharah": 30, "Mauga": -30, "D.Va": -25},
    "Juno": {"Genji": 50},
    "Kiriko": {"Ana": 20, "Zenyatta": 30},
    "Lifeweaver": {},
    "Lúcio": {},
    "Mercy": {},
    "Mizuki": {
        "Wrecking Ball": 30, 
        "Winston": 30, 
        "D.Va": 25, 
        "Doomfist": 20, 
        "Hazard": 20, 
        "Anran": 20, 
        "Tracer": 20,
        "Reaper": 20, 
        "Sombra": 20, 
        "Genji": 10, 
        "Venture": 20, 
        "Echo": 20, 
        "Vendetta": 20, 
        "Shion": 20
    },
    "Moira": {"Genji": 30},
    "Wuyang": {},
    "Zenyatta": {"Reinhardt": 30, "Roadhog": 25, "Kiriko": -30}
}

def seed_db():

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # delete old data
        print("Deleting old data...")
        db.query(Matchup).delete()
        db.query(Hero).delete()
        db.commit()

        # add roles and weights
        print("Adding new heroes and matchups...")
        for hero_name, role in HERO_ROLES.items():
            weight = META_WEIGHTS.get(hero_name, 1.0)
            db.add(Hero(name=hero_name, role=role, meta_weight=weight))
        db.commit()

        # add matchups
        for hero_name, matchups in MATCHUP_SCORES.items():
            for enemy_name, score in matchups.items():
                db.add(Matchup(hero_name=hero_name, enemy_name=enemy_name, score_modifier=score))
        db.commit()

        print("Seed successful!")

    except Exception as e:
        print(f"ERROR SEEDING: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()