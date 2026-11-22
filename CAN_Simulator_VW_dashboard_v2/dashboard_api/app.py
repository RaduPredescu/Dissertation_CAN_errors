"""Local offline FastAPI dashboard server, no hardware access and no arbitrary file paths."""
from __future__ import annotations
from threading import Lock
from pathlib import Path
import os
from fastapi import FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware

from tiguan_sim.runner import run_scenario
from tiguan_sim.dynamic_dbc import (run_dynamic_scenario, catalog_index, catalog_detail, DEFAULT_DBC)
from tiguan_sim.scenarios import SCENARIOS
from .data import get_scenario,get_frames,scenario_index

app=FastAPI(title='CAN Lab Tiguan III 2025 – Dynamic DBC Research',version='0.6.0')
DBC_PATH=Path(os.environ.get('CAN_LAB_DBC_PATH', str(DEFAULT_DBC))).resolve()
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],
                   allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
_lock=Lock()

@app.get('/api/health')
def health():
    return {'ok':True,'vehicle':'VW Tiguan III CT 2025 2.0 TDI DSG 4MOTION',
            'reference_dbc_present':DBC_PATH.is_file(), 'dbc_filename':DBC_PATH.name,
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
    try:return {'ok':True,'summary':run_dynamic_scenario(scenario,dbc_path=DBC_PATH)}
    except (OSError,RuntimeError,ValueError) as e: raise HTTPException(422,str(e)) from e
    finally:_lock.release()


@app.get('/api/dbc/messages')
def dbc_messages(search:str=Query('',max_length=120),offset:int=Query(0,ge=0),limit:int=Query(40,ge=1,le=100)):
    try: return catalog_index(dbc_path=DBC_PATH,search=search,offset=offset,limit=limit)
    except (OSError,RuntimeError,ValueError) as e: raise HTTPException(422,str(e)) from e


@app.get('/api/dbc/messages/{message_name}')
def dbc_message(message_name:str):
    try: return catalog_detail(message_name,dbc_path=DBC_PATH)
    except KeyError: raise HTTPException(404,'Message not present in DBC')
    except (OSError,RuntimeError,ValueError) as e: raise HTTPException(422,str(e)) from e
