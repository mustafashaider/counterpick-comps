import os
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI(
    title="Dynamic Counterpick API",
    description="Calculates the ideal 5-hero counterpick composition.",
    version="1.0.0"
)

# load .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# engine creates a connection to the database
# create a session factory, which creates new database session objects
# create a base class for our models
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Hero(Base):
    __tablename__ = "heroes"
    name = Column(String, primary_key=True, index=True)
    role = Column(String)
    meta_weight = Column(Float)

class Matchup(Base):
    __tablename__ = "matchups"
    id = Column(Integer, primary_key=True, index=True)
    hero_name = Column(String, ForeignKey("heroes.name"))
    enemy_name = Column(String, ForeignKey("heroes.name"))
    score_modifier = Column(Integer)

class EnemyComposition(BaseModel):
    tanks: List[str]
    dps: List[str]
    supports: List[str]
    

@app.get("/ui", response_class=HTMLResponse)
def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Overwatch Counterpick Generator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
            .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            label { font-weight: bold; display: block; margin-top: 15px; }
            select { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border-radius: 4px; }
            button { background: #28a745; color: white; border: none; padding: 10px 15px; margin-top: 20px; cursor: pointer; border-radius: 4px; width: 100%; font-size: 16px; }
            button:hover { background: #218838; }
            pre { background: #eef; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }
            .role-group { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Enemy Composition</h2>
            
            <div class="role-group">
                <label>Tank:</label>
                <select id="tank1"></select>
            </div>
            
            <div class="role-group">
                <label>DPS 1:</label>
                <select id="dps1"></select>
                
                <label>DPS 2:</label>
                <select id="dps2"></select>
            </div>
            
            <div class="role-group">
                <label>Support 1:</label>
                <select id="sup1"></select>
                
                <label>Support 2:</label>
                <select id="sup2"></select>
            </div>
            
            <button onclick="calculate()">Get Counter Composition</button>
            
            <h3>Recommended Team:</h3>
            <pre id="output">Submit team above to calculate...</pre>
        </div>

        <script>
            // Hero rosters for dynamic population
            const tanks = ["D.Mon", "D.Va", "Domina", "Doomfist", "Hazard", "Junker Queen", "Mauga", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya"];
            const dps = ["Anran", "Ashe", "Bastion", "Cassidy", "Echo", "Emre", "Freja", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Shion", "Sierra", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Vendetta", "Venture", "Widowmaker"];
            const supports = ["Ana", "Baptiste", "Brigitte", "Illari", "Jetpack Cat", "Juno", "Kiriko", "Lifeweaver", "Lúcio", "Mercy", "Mizuki", "Moira", "Wuyang", "Zenyatta"];

            // Populates a select element with options
            function populateDropdown(elementId, heroList) {
                const select = document.getElementById(elementId);
                heroList.sort().forEach(hero => {
                    const option = document.createElement("option");
                    option.value = hero;
                    option.textContent = hero;
                    select.appendChild(option);
                });
            }

            // Populate on page load
            window.onload = () => {
                populateDropdown("tank1", tanks);
                populateDropdown("dps1", dps);
                populateDropdown("dps2", dps);
                populateDropdown("sup1", supports);
                populateDropdown("sup2", supports);
                
                // Set some default selections so they aren't all identical
                document.getElementById('dps2').selectedIndex = 1;
                document.getElementById('sup2').selectedIndex = 1;
            };

            async function calculate() {
                // Grab the selected values and format them into the required arrays
                const tankArr = [document.getElementById('tank1').value];
                const dpsArr = [document.getElementById('dps1').value, document.getElementById('dps2').value];
                const supportsArr = [document.getElementById('sup1').value, document.getElementById('sup2').value];

                const response = await fetch('/api/v1/calculate-composition/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tanks: tankArr, dps: dpsArr, supports: supportsArr })
                });

                const data = await response.json();
                document.getElementById('output').textContent = JSON.stringify(data.recommended_composition, null, 2);
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/v1/calculate-composition/")
def calculate_composition(enemy_team: EnemyComposition, db: Session = Depends(get_db)):
    enemies = enemy_team.tanks + enemy_team.dps + enemy_team.supports # enemies is a list of strings
    
    all_heroes = db.query(Hero).all()
    
    # relevant_matchups only grabs the matchups where the enemy is in the provided enemy composition (enemies)
    relevant_matchups = db.query(Matchup).filter(Matchup.enemy_name.in_(enemies)).all()

    # 3. Group the matchup scores for fast lookup
    matchup_dict = {}
    for m in relevant_matchups:
        if m.hero_name not in matchup_dict:
            matchup_dict[m.hero_name] = 0
        matchup_dict[m.hero_name] += m.score_modifier
        
    scored_heroes = {}
    
    # 4. Calculate scores using database objects
    for hero in all_heroes:
        # Get the accumulated score from the database matchups, default to 0
        score = matchup_dict.get(hero.name, 0)
        
        final_score = (score + 100) * hero.meta_weight
        
        if hero.role not in scored_heroes:
            scored_heroes[hero.role] = []
            
        scored_heroes[hero.role].append({"hero": hero.name, "score": round(final_score, 1)})
        
    # 5. Sort the results
    for role in scored_heroes:
        scored_heroes[role] = sorted(scored_heroes[role], key=lambda x: x["score"], reverse=True)
        
    top_hitscan = scored_heroes.get("Hitscan", [])[:1]
    top_flex = scored_heroes.get("Flex", [])[:1]
    
    ideal_dps = sorted(top_hitscan + top_flex, key=lambda x: x["score"], reverse=True)
        
    # 6. Format the 1 Tank, 2 DPS, 2 Support output
    comp_format = {
        "Tank": scored_heroes.get("Tank", [])[:1],
        "DPS": ideal_dps,
        "Support": scored_heroes.get("Support", [])[:2]
    }
    
    return {
        "enemy_analyzed": enemies,
        "recommended_composition": comp_format
    }