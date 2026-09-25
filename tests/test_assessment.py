from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from functions.assessment import parent_distribution,order_tape,renewal_reference,grid_model


class AssessmentTests(unittest.TestCase):
    def test_stationary_renewal_reference_and_cap(self):
        lengths,p=parent_distribution(1.5,2,512)
        self.assertTrue(np.all(p>=0));self.assertAlmostEqual(p.sum(),1.)
        self.assertEqual(p[0],0.);self.assertAlmostEqual(p[-1],(2/512)**1.5)
        mean=float(lengths@p);ref=renewal_reference([0,1,512],1.5,2,512)
        np.testing.assert_allclose(ref,[1,1-1/mean,0],rtol=0,atol=5e-16)

    def test_parent_identity_survives_same_sign_adjacency(self):
        signs,parents,runs=order_tape(10000,19,1.5,2,512)
        self.assertEqual(len(signs),10000);self.assertEqual(set(signs),{-1,1})
        self.assertTrue(np.all(np.diff(parents)>=0))
        boundaries=np.flatnonzero(np.diff(parents)>0)
        self.assertTrue(np.any(signs[boundaries]==signs[boundaries+1]))
        self.assertTrue(np.all(runs[:,2]<=512));self.assertEqual(runs[:,4].sum(),10000)
        self.assertTrue(np.all(runs[1:-1,2]==runs[1:-1,4]))
        again=order_tape(10000,19,1.5,2,512)
        np.testing.assert_array_equal(again[0],signs)

    def test_half_cell_phase_keeps_reflection_and_places_edges_between_nodes(self):
        m=grid_model({'dx':.05,'du':.001},phase=.5)
        np.testing.assert_allclose(m.x,-m.x[::-1],atol=4e-15,rtol=0)
        self.assertGreater(np.min(abs(m.x-6)),.024)


if __name__=='__main__':unittest.main()
