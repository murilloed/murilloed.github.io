import unittest
from carflow import simulate
class TrafficTests(unittest.TestCase):
    def test_conservation_and_no_overlap(self):
        for n in (12,32,64):
            r=simulate(n,duration=70)
            self.assertFalse(r['metrics']['collision'])
            self.assertGreater(r['metrics']['min_gap_m'],0)
            for f in r['trace']:
                self.assertEqual(len(f['positions']),n)
                self.assertTrue(all(0<=x<1200 for x in f['positions']))
                self.assertTrue(all(v>=0 for v in f['speeds']))
    def test_density_reduces_speed(self):
        self.assertGreater(simulate(12,duration=80)['metrics']['mean_speed_kmh'],simulate(64,duration=80)['metrics']['mean_speed_kmh'])
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):simulate(100)
        with self.assertRaises(ValueError):simulate(dt=1)
if __name__=='__main__':unittest.main()
