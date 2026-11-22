"""Local structural tests; the full OpenDBC integration additionally needs cantools."""
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from dashboard_api.app import app
from tiguan_sim.dynamic_dbc import Catalog, DEFAULT_DBC, catalog_detail, catalog_index, fields_for, load_mapping, run_dynamic_scenario
from tiguan_sim.scenarios import vehicle_state


class TestDynamicDBC(unittest.TestCase):
    def test_catalog_reads_all_available_dbc_messages(self):
        cat = Catalog.open(DEFAULT_DBC)
        index = catalog_index(search='WHEEL_SPEED_FR')
        self.assertEqual(index['total'], 1)
        self.assertEqual(index['messages'][0]['name'], 'ESP_NEW_1')
        self.assertEqual(index['dbc']['messages'], len(cat.messages))
        self.assertEqual(catalog_detail('ESP_NEW_1')['mapped_signals'], 4)

    def test_generic_fields_and_roundtrip(self):
        cat = Catalog.open(DEFAULT_DBC)
        msg = next(x for x in cat.messages if x.name == 'ESP_NEW_1')
        values, origins = fields_for(msg, cat, vehicle_state(25, 'abs_fr_sensor'), 50, load_mapping())
        self.assertEqual(values['WHEEL_SPEED_FR'], 0)
        self.assertEqual(origins['WHEEL_SPEED_FR'], 'behavior_model')
        self.assertEqual(origins['XCHECKSUM'], 'placeholder')
        decoded = cat.decode(msg, cat.encode(msg, values))
        self.assertEqual(decoded['WHEEL_SPEED_FR'], 0)

    def test_scenarios_generated_without_fixed_message_list(self):
        with tempfile.TemporaryDirectory() as td:
            o, e = Path(td)/'observations', Path(td)/'evaluation'
            for name in ('healthy','abs_fr_sensor','compound'):
                s = run_dynamic_scenario(name, output_root=o,evaluation_root=e)
                self.assertEqual(s['engine'],'dynamic_dbc')
                self.assertEqual(s['messages_emitted'],3 if name!='compound' else 3)
                self.assertFalse(s['oem_checksum_implemented'])
                rows = [json.loads(x) for x in (o/name/'frames.jsonl').read_text().splitlines()]
                self.assertTrue(all(f['bus_injectable'] is False for f in rows))
                self.assertTrue(all('signal_origin' in f for f in rows))
                self.assertTrue((e/name/'ground_truth.json').is_file())
                self.assertNotIn('ground_truth', (o/name/'summary.json').read_text())
                if name=='compound':
                    self.assertFalse(any(f['message']=='ESP_NEW_1' and f['t_s']>=33 for f in rows))

    def test_api_catalog(self):
        client=TestClient(app)
        r=client.get('/api/dbc/messages?search=ESP_NEW_1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['total'],1)
        r=client.get('/api/dbc/messages/ESP_NEW_1')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['signal_count'],6)
        self.assertEqual(client.get('/api/dbc/messages/NONEXISTENT').status_code,404)
        self.assertFalse(client.get('/api/dbc/messages').json()['dbc']['vehicle_verified'])
        self.assertNotIn('ground_truth',client.get('/api/dbc/messages').text.lower())

    def test_api_rerun_uses_dynamic_generator(self):
        client=TestClient(app)
        r=client.post('/api/runs/healthy')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['summary']['engine'],'dynamic_dbc')


if __name__=='__main__': unittest.main()
