from pathlib import Path
import sys,unittest
import tempfile
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from functions.assessment import parent_distribution,order_tape,renewal_reference,grid_model,source_membership,membership_changes,long_run,increment_covariance_parts,frozen_execution_probe,source_quadrature_probe
from functions.core import external_source,placement_weights
from functions.assessment import continuous_fill_reference
from functions.assessment import response_difference


class AssessmentTests(unittest.TestCase):
    def test_response_comparison_separates_baseline_and_rejects_misalignment(self):
        left=np.zeros((3,13));right=left.copy()
        left[:,0]=right[:,0]=[0,1,2]
        left[:,3]=[2,5,4];right[:,3]=[1,3,3]
        left[:,4]=[10,11,9];right[:,4]=[12,12,13]
        r=response_difference(left,right)
        self.assertEqual(r['spread']['initial_difference'],-2.)
        self.assertEqual(r['spread']['max_absolute_difference'],4.)
        self.assertEqual(r['spread']['max_response_difference'],2.)
        self.assertEqual(r['spread']['response_peak_u'],2.)
        self.assertEqual(r['midpoint']['max_response_difference'],1.)
        right[:,0]+=.1
        with self.assertRaisesRegex(ValueError,'Unmatched control sample times'):
            response_difference(left,right)

    def test_continuous_reference_exact_moments_reflection_and_capacity(self):
        x=np.linspace(-2,2,9);y=x+3;quote=.2;volume=.7
        front=np.sqrt((quote+3)**2+2*volume)-3
        moment=lambda z:z**3/3+1.5*z**2
        expected=(moment(front)-moment(quote))/volume
        result=continuous_fill_reference(x,y,quote,1.,volume,1)
        self.assertAlmostEqual(result['terminal_price'],front,places=13)
        self.assertAlmostEqual(result['mean_log_price'],expected,places=13)
        mirrored=continuous_fill_reference(x,y[::-1],-quote,1.,volume,-1)
        self.assertAlmostEqual(mirrored['mean_log_price'],-expected,places=13)
        refined=np.linspace(-2,2,65)
        finer=continuous_fill_reference(refined,np.interp(refined,x,y),quote,1.,volume,1)
        self.assertAlmostEqual(finer['mean_log_price'],expected,places=13)
        short=continuous_fill_reference(x,y,quote,1.,100.,1)
        self.assertAlmostEqual(short['filled_quantity'],3.7,places=13)
        self.assertAlmostEqual(short['unfilled_quantity'],96.3,places=13)

    def test_frozen_probes_preserve_field_quotes_and_source_normalization(self):
        m=grid_model({'dx':.1,'du':.001},phase=.5)
        rho=np.array([1/(1+np.exp(m.x+3)),1/(1+np.exp(-m.x+3))]);original=rho.copy()
        for subdivision in (1,2,4):
            probe=frozen_execution_probe(m,rho,subdivision,.002,1)
            np.testing.assert_array_equal(rho,original)
            self.assertLess(probe['pre_quote_difference'],2e-14)
            self.assertAlmostEqual(sum(probe['filled_quantities']),.002,places=14)
            self.assertLess(abs(probe['mass_residual']),1e-14)
        for q in ([-6.013,6.007],[-6.,6.]):
            result=source_quadrature_probe(m,q)
            self.assertLess(max(abs(np.array(result['completion_norm_error']))),1e-14)
            self.assertLessEqual(max(abs(np.array(result['external_error']))),m.dx/2+1e-13)
            self.assertLessEqual(max(abs(np.array(result['completion_centroid_error']))),m.dx/2+1e-13)

    def test_covariance_parts_reconstruct_overlapping_pearson_acf(self):
        rng=np.random.default_rng(92);jump=rng.normal(size=30);field=.6*jump+np.arange(30)/10
        rows=increment_covariance_parts(jump,field,[0,1,8])
        for row in rows:
            lag=row['lag'];total=jump+field
            expected=np.corrcoef(total[:len(total)-lag],total[lag:])[0,1]
            self.assertAlmostEqual(sum(row['contributions']),expected,places=13)
            self.assertLess(abs(row['sum_residual']),1e-13)
        with self.assertRaisesRegex(ValueError,'Zero-variance'):
            increment_covariance_parts(jump,-jump,[1])

    def test_diagnostics_and_resume_preserve_the_executed_path(self):
        c={'events':4,'burn_events':2,'beta':1.5,'minimum_parent':2,'parent_cap':32,'event_du':.01,'child_volume':.002}
        job=('short',{'dx':.1,'du':.001},{'phase':.5},c,7,'lmf')
        plain=long_run(job)
        with tempfile.TemporaryDirectory() as directory:
            measured=dict(c,resolution_diagnostics=True,progress_every_events=3,_checkpoint=str(Path(directory)/'resume.npz'))
            observed=long_run((*job[:3],dict(c,resolution_diagnostics=True),*job[4:]))
            original_replace=Path.replace
            def interrupt_after_save(source,target):
                original_replace(source,target)
                raise RuntimeError('Simulated interruption after atomic save')
            with patch.object(Path,'replace',interrupt_after_save):
                with self.assertRaisesRegex(RuntimeError,'Simulated interruption'):
                    long_run((*job[:3],measured,*job[4:]))
            resumed=long_run((*job[:3],measured,*job[4:]))
            for key in ('values','signs','parents','runs','fills','offsets'):
                np.testing.assert_array_equal(plain[key],observed[key]);np.testing.assert_array_equal(observed[key],resumed[key])
            np.testing.assert_array_equal(observed['support'],resumed['support'])
            with self.assertRaisesRegex(ValueError,'Changed resolution checkpoint inputs'):
                long_run((*job[:3],dict(measured,child_volume=.003),*job[4:]))

    def test_support_intervals_match_closed_edge_core_masks(self):
        m=grid_model({'dx':.05,'du':.001},phase=.5)
        previous=None;old_masks=None
        for q in ([m.x[120],m.x[-121]],[-6.,6.],[-6.003,6.009]):
            s=source_membership(m,q);lit,latent=external_source(m,q);g=placement_weights(m,q)
            masks=np.array([(lit+latent)[0,1:-1]>0,(lit+latent)[1,1:-1]>0,g[0,1:-1]>0,g[1,1:-1]>0])
            indices=np.arange(len(m.x)-2)
            expected=np.array([indices<s[0],indices>=s[1],(indices>=s[2])&(indices<s[3]),(indices>=s[4])&(indices<s[5])])
            np.testing.assert_array_equal(masks,expected)
            if previous is not None:
                flips=np.count_nonzero(masks!=old_masks,axis=1)
                self.assertEqual(membership_changes(previous,s),(sum(flips[:2]),sum(flips[2:])))
            previous=s;old_masks=masks

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
