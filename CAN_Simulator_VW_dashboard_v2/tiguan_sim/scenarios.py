"""Reproducible scenario traces. Fault injection metadata is evaluation-only."""
from __future__ import annotations
import math

SCENARIOS = {
 'healthy': ('Healthy', 'Trafic normal, fără defecte'),
 'abs_fr_sensor': ('ABS · față dreapta', 'Senzor viteză FR indică 0 km/h'),
 'abs_fr_encoder': ('ABS · encoder FR', 'Semnal periodic eronat la roata față dreapta'),
 'dpf_restriction': ('DPF · presiune', 'Presiune diferențială excesivă'),
 'egr_flow': ('EGR · debit', 'Debit EGR actual sub cererea ECU'),
 'dsg_overheat': ('DSG · temperatură', 'Temperatură ridicată la transmisie'),
 'awd_clutch': ('4MOTION · cuplare', 'Cerere AWD fără transferul așteptat'),
 'low_voltage': ('Sistem 12 V', 'Tensiune mică de alimentare'),
 'compound': ('Defecte corelate', 'Tensiune 12 V redusă și pierderi comunicație ABS'),
}
DURATION = 55.0
DT = 0.5

def vehicle_state(t: float, scenario: str) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError('Scenario not defined')
    # A simple drive cycle: idle -> accelerating -> steady -> slowing -> idle.
    if t < 5: speed = 0.0
    elif t < 18: speed = (t-5) * 3.8
    elif t < 38: speed = 49.4 + 1.2 * math.sin((t-18)/4)
    elif t < 49: speed = max(0, 49.4 - (t-38)*4.5)
    else: speed = 0.0
    speed = round(speed, 2)
    gear = 1 if speed < 12 else 2 if speed < 25 else 3 if speed < 37 else 4
    if speed < .1: gear = 1
    rpm = round(790 + speed*26 + 65*math.sin(t/6),1)
    wheels = {
        'wheel_fl':max(0, speed + .14*math.sin(t*.5)),
        'wheel_fr':max(0, speed + .13*math.cos(t*.4)),
        'wheel_rl':max(0, speed + .10*math.cos(t*.31)),
        'wheel_rr':max(0, speed + .11*math.sin(t*.35)),
    }
    coolant = 87 + 2.1*math.sin(t/12)
    voltage = 14.1 + .1 * math.sin(t/5)
    dpf_pressure = 7 + speed*.62 + rpm*.012
    soot = 18.0
    egr_command = 32 if speed > 15 else 15
    egr_actual = egr_command + 1.5*math.sin(t/7)
    dsg_temp = 74 + speed*.25
    awd_requested = 18 if speed > 15 else 5
    awd_actual = awd_requested - 1
    abs_online = True
    if t >= 22:
        if scenario == 'abs_fr_sensor':
            wheels['wheel_fr'] = 0.0
        if scenario == 'abs_fr_encoder':
            wheels['wheel_fr'] = max(0, speed - (20 if int((t-22)*2)%4==0 else 2))
        if scenario == 'dpf_restriction':
            dpf_pressure += 155 + max(0,t-22)*2.0
            soot = 74 + max(0,t-22)*.2
        if scenario == 'egr_flow':
            egr_actual = max(0,egr_command-27)
        if scenario == 'dsg_overheat':
            dsg_temp = 97 + (t-22)*2.2
        if scenario == 'awd_clutch':
            awd_requested = 58
            awd_actual = 7
        if scenario == 'low_voltage':
            voltage = max(10.9,14.0-(t-22)*.19)
        if scenario == 'compound':
            voltage = max(10.7,14.0-(t-22)*.24)
            if t >= 33: abs_online = False
    return {
      't_s':round(t,2), 'speed':speed,'rpm':rpm,'coolant':round(coolant,2),
      'voltage':round(voltage,2),'gear':gear,'dpf_pressure':round(dpf_pressure,1),
      'soot':round(soot,1),'egr_command':round(egr_command,1),'egr_actual':round(egr_actual,1),
      'dsg_temp':round(dsg_temp,1),'awd_requested':round(awd_requested,1),
      'awd_actual':round(awd_actual,1),'abs_online':abs_online,
      **{k:round(v,2) for k,v in wheels.items()}
    }

# Evaluation-only; not exposed by the API (even indirectly).
GROUND_TRUTH = {
 'healthy':[],
 'abs_fr_sensor':['wheel_speed_sensor_fr_signal_loss'],
 'abs_fr_encoder':['wheel_encoder_fr_irregular_signal'],
 'dpf_restriction':['simulated_dpf_restriction'],
 'egr_flow':['simulated_egr_flow_restriction'],
 'dsg_overheat':['simulated_transmission_cooling_limitation'],
 'awd_clutch':['simulated_rear_coupling_underresponse'],
 'low_voltage':['simulated_12v_supply_drop'],
 'compound':['simulated_12v_supply_drop','simulated_abs_ecu_dropout'],
}
