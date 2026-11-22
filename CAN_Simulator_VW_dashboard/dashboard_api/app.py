"""Local offline FastAPI dashboard server, no hardware access and no arbitrary file paths."""
from __future__ import annotations
from threading import Lock
from fastapi import FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware

from tiguan_sim.runner import run_scenario,DBC_PATH
from tiguan_sim.scenarios import SCENARIOS
from .data import get_scenario,get_frames,scenario_index

app=FastAPI(title='CAN Lab Tiguan III 2025 – offline research',version='0.5.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],
                   allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
_lock=Lock()

@app.get('/api/health')
def health():
    return {'ok':True,'vehicle':'VW Tiguan III CT 2025 2.0 TDI DSG 4MOTION',
            'reference_dbc_present':DBC_PATH.is_file(),
            'ai_connected':False,'mcp_connected':False,'real_can_connected':False,
            'oem_crc_supported':False}

@app.get('/api/scenarios')
def scenarios(): return {'scenarios':scenario_index()}

@app.get('/api/scenarios/{scenario}')
def scenario_data(scenario: str):
    if scenario not in SCENARIOS: raise HTTPException(404,'Scenariu necunoscut')
    try:return get_scenario(scenario)
    except (FileNotFoundError,ValueError) as e: raise HTTPException(404,str(e)) from e

@app.get('/api/scenarios/{scenario}/frames')
def frames(scenario: str,at:float=Query(0,ge=0,le=3600),limit:int=Query(40,ge=1,le=150),q:str=Query('',max_length=80)):
    if scenario not in SCENARIOS: raise HTTPException(404,'Scenariu necunoscut')
    try:return get_frames(scenario,at,limit,q)
    except (FileNotFoundError,ValueError) as e: raise HTTPException(404,str(e)) from e

@app.post('/api/runs/{scenario}')
def run(scenario:str):
    if scenario not in SCENARIOS: raise HTTPException(404,'Scenariu necunoscut')
    if not _lock.acquire(blocking=False): raise HTTPException(409,'O simulare este deja în curs')
    try:return {'ok':True,'summary':run_scenario(scenario)}
    except (OSError,RuntimeError,ValueError) as e: raise HTTPException(422,str(e)) from e
    finally:_lock.release()
