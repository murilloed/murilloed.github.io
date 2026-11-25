import unittest
from civicshield import path,edges,simulate,learn_rates,cvar_loss
class CivicTests(unittest.TestCase):
    def test_topologies_and_closures(self):
        for city in ('grid','river','ladder'):
            for a in range(16):self.assertTrue(path(city,0,a))
            for closed in edges(city):
                route=path(city,0,15,closed)
                self.assertTrue(all(set((a,b))!=set(closed) for a,b in zip(route,route[1:])))
    def test_conservation_and_movement(self):
        for policy in ('nearest','equity','robust'):
            r=simulate(policy=policy);m=r['metrics']
            self.assertEqual(m['requests'],m['completed']+m['active']+m['pending']+m['expired'])
            self.assertTrue(0<=m['worst_zone_completion_rate']<=1)
            for a,b in zip(r['trace'],r['trace'][1:]):
                for x,y in zip(a['vehicles'],b['vehicles']):
                    if x['zone']!=y['zone']:
                        self.assertIn(tuple(sorted((x['zone'],y['zone']))),edges('river'))
                        self.assertNotEqual(set((x['zone'],y['zone'])),set(b['closed'] or []))
    def test_demand_learning_and_tail(self):
        self.assertEqual(learn_rates('grid'),learn_rates('grid'));self.assertEqual(cvar_loss([.1,.2,.3,.8]),.8)
if __name__=='__main__':unittest.main()
