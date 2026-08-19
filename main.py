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
            label { font-weight: bold; display: block; margin-top: 10px; }
            input { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
            button { background: #28a745; color: white; border: none; padding: 10px 15px; margin-top: 15px; cursor: pointer; border-radius: 4px; }
            pre { background: #eef; padding: 10px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Overwatch Counterpick Generator</h2>
            <label>Tank (comma-separated):</label>
            <input type="text" id="tank" value="Winston">
            
            <label>DPS (comma-separated):</label>
            <input type="text" id="dps" value="Genji, Tracer">
            
            <label>Supports (comma-separated):</label>
            <input type="text" id="supports" value="Moira, Zenyatta">
            
            <button onclick="calculate()">Get Counter Composition</button>
            
            <h3>Recommended Team:</h3>
            <pre id="output">Submit team above to calculate...</pre>
        </div>

        <script>
            async function calculate() {
                const tank = document.getElementById('tank').value.split(',').map(s => s.trim());
                const dps = document.getElementById('dps').value.split(',').map(s => s.trim());
                const supports = document.getElementById('supports').value.split(',').map(s => s.trim());

                const response = await fetch('/api/v1/calculate-composition/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tanks: tank, dps: dps, supports: supports })
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