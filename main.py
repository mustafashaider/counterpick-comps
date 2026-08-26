import os
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

templates = Jinja2Templates(directory="templates")

app = FastAPI(
    title="Dynamic Counterpick API",
    description="Calculates the ideal 5-hero counterpick composition.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

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
def get_ui(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

@app.post("/api/v1/calculate-composition/")
def calculate_composition(enemy_team: EnemyComposition, db: Session = Depends(get_db)):
    enemies = enemy_team.tanks + enemy_team.dps + enemy_team.supports
    
    all_heroes = db.query(Hero).all()
    relevant_matchups = db.query(Matchup).filter(Matchup.enemy_name.in_(enemies)).all()

    matchup_dict = {}
    for m in relevant_matchups:
        if m.hero_name not in matchup_dict:
            matchup_dict[m.hero_name] = 0
        matchup_dict[m.hero_name] += m.score_modifier
        
    scored_heroes = {}
    
    for hero in all_heroes:
        score = matchup_dict.get(hero.name, 0)
        final_score = (score + 100) * hero.meta_weight
        
        if hero.role not in scored_heroes:
            scored_heroes[hero.role] = []
            
        scored_heroes[hero.role].append({"hero": hero.name, "score": round(final_score, 1)})
        
    for role in scored_heroes:
        scored_heroes[role] = sorted(scored_heroes[role], key=lambda x: x["score"], reverse=True)
        
    top_hitscan = scored_heroes.get("Hitscan", [])[:1]
    top_flex = scored_heroes.get("Flex", [])[:1]
    
    ideal_dps = sorted(top_hitscan + top_flex, key=lambda x: x["score"], reverse=True)
        
    comp_format = {
        "Tank": scored_heroes.get("Tank", [])[:1],
        "DPS": ideal_dps,
        "Support": scored_heroes.get("Support", [])[:2]
    }
    
    return {
        "enemy_analyzed": enemies,
        "recommended_composition": comp_format
    }