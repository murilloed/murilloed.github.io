import unittest
from voltswarm import simulate,demand,train_model,distance
class EnergyTests(unittest.TestCase):
    def test_energy_and_requests_conserved(self):
        for policy in ('nearest','reservation','bandit'):
            r=simulate('storm',12,policy);m=r['metrics']
            self.assertAlmostEqual(m['energy_balance_error_kwh'],0,places=7)
            self.assertEqual(m['requests'],m['completed']+m['active']+m['expired']+m['pending'])
            self.assertGreaterEqual(m['minimum_battery_kwh'],0)
            for f in r['trace']:
                self.assertEqual(len(f['vehicles']),12)
                self.assertTrue(all(0<=v['soc']<=1 for v in f['vehicles']))
                if 65<=f['minute']<105:self.assertEqual(next(s['ports'] for s in f['stations'] if s['zone']==7),0)
    def test_kinematics(self):
        trace=simulate()['trace']
        for a,b in zip(trace,trace[1:]):
            for x,y in zip(a['vehicles'],b['vehicles']):self.assertLessEqual(distance(x['zone'],y['zone']),1)
    def test_training_and_reproducibility(self):
        self.assertTrue(train_model('balanced'));self.assertEqual(demand('balanced',7),demand('balanced',7))
    def test_invalid_policy(self):
        with self.assertRaises(ValueError):simulate(policy='magic')
if __name__=='__main__':unittest.main()
