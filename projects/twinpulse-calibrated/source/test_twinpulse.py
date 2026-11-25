import datetime as dt
import unittest
import tempfile
from pathlib import Path
from twinpulse import experiment,fit,predict,quantile,queue_rollout,load
class TwinTests(unittest.TestCase):
    def test_real_temporal_split_and_finite_metrics(self):
        r=experiment(Path(__file__).with_name('observed.csv'));p=r['protocol']
        self.assertLess(p['train_end'],p['calibration_start']);self.assertLess(p['calibration_end'],p['test_start'])
        for m in r['models']:
            self.assertGreaterEqual(m['metrics']['rmse'],0);self.assertTrue(0<=m['metrics']['coverage']<=1)
    def test_queue_mass_conservation(self):
        rows=[{'predicted':5000,'timestamp':str(i)} for i in range(15)]
        r=queue_rollout(rows)
        for f in r['trace']:self.assertEqual(f['entered_total'],f['exited_total']+sum(f['queues']))
    def test_calibration_quantile(self):self.assertEqual(quantile(list(range(1,10))),9)
    def test_constant_signal_fit(self):
        rows=[(dt.datetime(2020,1,1)+dt.timedelta(hours=i),1000,1000) for i in range(120)]
        self.assertLess(abs(predict(fit(rows),rows[-1][0],1000)-1000),10)
    def test_reject_duplicate_or_nonhourly_only_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'counts.csv';start=dt.datetime(2020,1,1)
            path.write_text('timestamp,volume\n'+'\n'.join(f'{(start+dt.timedelta(days=i)).isoformat()},100' for i in range(100)))
            with self.assertRaises(ValueError):experiment(path)
            path.write_text('timestamp,volume\n'+'\n'.join(f'{start.isoformat()},100' for _ in range(100)))
            with self.assertRaises(ValueError):load(path)
if __name__=='__main__':unittest.main()
