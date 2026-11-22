import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from tiguan_sim.dbc_codec import load_dbc,encode,decode
from tiguan_sim.runner import DBC_PATH,run_scenario
from tiguan_sim.scenarios import SCENARIOS
from dashboard_api.app import app

class TestSimulator(unittest.TestCase):
 def test_dbc_roundtrip(self):
    db=load_dbc(DBC_PATH)
    self.assertEqual(db['Motor_04'].can_id,263)
    self.assertEqual(db['ESP_NEW_1'].size,48)
    for name,fields in [('Motor_04',{'MO_Anzeigedrehz':1500,'MO_Istgang':4}),
                         ('ESP_NEW_1',{'WHEEL_SPEED_FR':43.5,'WHEEL_SPEED_FL':44.5}),
                         ('Getriebe_11',{'GE_Fahrstufe':8,'GE_Zielgang':4})]:
        decoded=decode(db[name],encode(db[name],fields))
        for key,val in fields.items(): self.assertAlmostEqual(decoded[key],val,delta=3 if key=='MO_Anzeigedrehz' else .01)

 def test_all_scenarios_and_private_truth(self):
    with tempfile.TemporaryDirectory() as d:
      obs=Path(d)/'observations'; ev=Path(d)/'evaluation'
      for scenario in SCENARIOS:
        r=run_scenario(scenario,obs,ev)
        self.assertGreater(r['frames_sent'],250)
        self.assertTrue((ev/scenario/'ground_truth.json').is_file())
        self.assertFalse('ground_truth' in (obs/scenario/'summary.json').read_text())
        self.assertFalse(r['real_vehicle_capture'])
        self.assertFalse(r['oem_checksum_implemented'])
      self.assertEqual(json.loads((obs/'healthy'/'summary.json').read_text())['events_detected'],[])
      self.assertIn('ABS_FR_SIGNAL_LOSS',json.loads((obs/'abs_fr_sensor'/'summary.json').read_text())['events_detected'])
      self.assertIn('ABS_FR_IMPLAUSIBLE',json.loads((obs/'abs_fr_encoder'/'summary.json').read_text())['events_detected'])
      self.assertIn('DPF_DIFFERENTIAL_PRESSURE_HIGH',json.loads((obs/'dpf_restriction'/'summary.json').read_text())['events_detected'])
      self.assertIn('EGR_FLOW_MISMATCH',json.loads((obs/'egr_flow'/'summary.json').read_text())['events_detected'])
      self.assertIn('DSG_OIL_TEMPERATURE_HIGH',json.loads((obs/'dsg_overheat'/'summary.json').read_text())['events_detected'])
      self.assertIn('AWD_COUPLING_UNDERRESPONSE',json.loads((obs/'awd_clutch'/'summary.json').read_text())['events_detected'])
      self.assertIn('ABS_ECU_TIMEOUT',json.loads((obs/'compound'/'summary.json').read_text())['events_detected'])
      frames=[json.loads(x) for x in (obs/'compound'/'frames.jsonl').read_text().splitlines()]
      self.assertFalse(any(f['message']=='ESP_NEW_1' and f['t_s']>=33 for f in frames))

class TestDashboard(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.client=TestClient(app)
 def test_health(self):
    r=self.client.get('/api/health')
    self.assertEqual(r.status_code,200)
    self.assertFalse(r.json()['ai_connected'])
 def test_all_diagnoses_and_evidence(self):
    for scenario in SCENARIOS:
      with self.subTest(scenario=scenario):
        r=self.client.get(f'/api/scenarios/{scenario}')
        self.assertEqual(r.status_code,200)
        d=r.json()
        self.assertFalse(d['limitations']['tiguan_2025_dbc_verified'])
        self.assertNotIn('ground_truth',json.dumps(d).lower())
        self.assertEqual(len(d['telemetry']),15)
        for e in d['events']:
            self.assertTrue(e['hypothesis'] and e['reason'])
            self.assertGreaterEqual(len(e['alternatives']),2)
            self.assertGreaterEqual(len(e['checks']),2)
 def test_synthetic_abs_is_precise_but_not_certain(self):
    d=self.client.get('/api/scenarios/abs_fr_sensor').json()
    self.assertEqual(d['events'][0]['zone'],'wheel_fr')
    self.assertIn('nu este confirmată',d['events'][0]['certainty'])
    self.assertEqual(d['dtcs'][0]['code'],'C101B')
    self.assertIn('simul',d['dtcs'][0]['status'])
 def test_no_access_to_ground_truth(self):
    for path in ['/api/evaluation/abs_fr_sensor','/api/ground_truth','/api/scenarios/../../evaluation','/api/scenarios/healthy/../evaluation']:
      self.assertIn(self.client.get(path).status_code,(404,422))
 def test_frames_window(self):
    r=self.client.get('/api/scenarios/abs_fr_sensor/frames?at=27&limit=40')
    self.assertEqual(r.status_code,200)
    d=r.json()
    self.assertTrue(d['frames'])
    self.assertTrue(all(abs(f['t_s']-27)<=.751 for f in d['frames']))
    self.assertTrue(any(f['is_fd'] and f['length']==48 for f in d['frames']))
 def test_rerun(self):
    r=self.client.post('/api/runs/healthy')
    self.assertEqual(r.status_code,200)
    self.assertEqual(r.json()['summary']['confirmed_dtcs'],[])

if __name__=='__main__':unittest.main()
