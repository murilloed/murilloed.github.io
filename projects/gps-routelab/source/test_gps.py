import unittest
from gps_routelab import city,route,gps_experiment
class RoutingTests(unittest.TestCase):
    def test_optimality_against_dijkstra(self):
        for factor in (1,2,5):
            n,e=city(congestion=factor)
            for start,goal in ((0,48),(21,27),(14,36)):
                self.assertEqual(route(n,e,start,goal)['travel_seconds'],route(n,e,start,goal,'dijkstra')['travel_seconds'])
    def test_closure(self):
        n,e=city();r=route(n,e,0,1,closed=[(0,1)])
        self.assertEqual(r['travel_seconds'],54)
        self.assertEqual(route(n,e,0,1,closed=[(0,1),(0,7)])['path'],[])
    def test_identity_and_noise(self):
        n,e=city();self.assertEqual(route(n,e,2,2)['path'],[2])
        self.assertEqual(gps_experiment(noise_m=0)['node_match_accuracy'],1)
        self.assertEqual(gps_experiment(),gps_experiment())
if __name__=='__main__':unittest.main()
