import csv
import tempfile
import unittest
from pathlib import Path
from fleetmind import requests,simulate,train_q,validate_csv,distance,load_requests,export_requests
class FleetTests(unittest.TestCase):
    def test_seeded_requests(self):self.assertEqual(requests(seed=7),requests(seed=7))
    def test_conservation(self):
        for policy in ('random','nearest','qlearning'):
            r=simulate(requests(),8,policy);m=r['metrics']
            self.assertEqual(m['requests'],m['completed']+m['active']+m['pending']+m['expired'])
            for frame in r['trace']:self.assertEqual(len(frame['vehicles']),8)
            for a,b in zip(r['trace'],r['trace'][1:]):
                for x,y in zip(a['vehicles'],b['vehicles']):self.assertLessEqual(distance(x['zone'],y['zone']),1)
    def test_empty_demand(self):self.assertEqual(simulate([])['metrics']['completed'],0)
    def test_training_changes_values(self):self.assertTrue(any(v!=0 for v in train_q(episodes=2).values()))
    def test_csv_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'counts.csv';path.write_text('minute,observed,simulated\n0,10,12\n1,4,2\n')
            r=validate_csv(path);self.assertEqual(r['mae'],2);self.assertEqual(r['rmse'],2)
            path.write_text('minute,observed,simulated\n0,nan,2\n')
            with self.assertRaises(ValueError):validate_csv(path)
    def test_request_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'requests.csv';data=requests()
            export_requests(data,path);self.assertEqual(load_requests(path),data)
            path.write_text('minute,origin,destination\n0,9,1\n')
            with self.assertRaises(ValueError):load_requests(path)
if __name__=='__main__':unittest.main()
