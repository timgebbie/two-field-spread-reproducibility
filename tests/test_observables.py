from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from functions.core import Model
from functions.observables import trade_record,finish_tape,lag_correlation


class ObservableTests(unittest.TestCase):
    def fixture(self):
        m=Model(x_min=-2,x_max=2,dx=.5)
        removed=np.zeros((2,len(m.x)));removed[1,5:7]=[2,1]
        r={'step':9,'u_end':.02,'pre_p_b':-.5,'pre_p_a':.5,'midpoint':.2,'p_b':-.5,'p_a':.9,'spread':1.4,
           'q_b':-1.,'q_a':1.,'Sigma':2.,'mu':0.,'Q_B_quote':0.,'Q_A_quote':0.,'Q_B_post':1.5,'Q_A_post':0.,
           'requested_buy':1.5,'unfilled_buy':0.}
        return m,r,removed

    def test_execution_price_uses_actual_fill_volumes(self):
        m,r,removed=self.fixture();trade,fills=trade_record(m,r,removed,1,7)
        self.assertAlmostEqual(trade['filled_quantity'],1.5)
        self.assertAlmostEqual(trade['execution_log_price'],2/3)
        self.assertAlmostEqual(trade['execution_price_vwap'],(2*np.exp(.5)+np.exp(1))/3)
        self.assertGreater(trade['execution_price_vwap'],trade['execution_price_geometric'])
        self.assertAlmostEqual(sum(f['filled_quantity'] for f in fills),trade['filled_quantity'])
        self.assertEqual(trade['parent_order_id'],7)

    def test_no_invented_trade_or_hidden_simultaneous_ordering(self):
        m,r,removed=self.fixture()
        with self.assertRaises(ValueError):trade_record(m,r,removed*0,1,0)
        removed[0,2]=1
        with self.assertRaises(ValueError):trade_record(m,r,removed,1,0)

    def test_aggressor_quote_and_tick_labels_remain_distinct(self):
        m,r,removed=self.fixture();trade,_=trade_record(m,r,removed,1,0)
        self.assertEqual(trade['aggressor_sign'],1);self.assertEqual(trade['quote_midpoint_sign'],1)
        rows=[dict(trade,execution_log_price=z) for z in [1,2,2,1,1]];finish_tape(rows)
        self.assertEqual([x['tick_rule_sign'] for x in rows],[0,1,1,-1,-1])
        self.assertIsNone(rows[0]['trade_log_increment'])
        self.assertEqual(rows[3]['abs_trade_log_increment'],1)

    def test_lag_direction_slice_centering_and_pair_counts(self):
        x=np.array([3,0,4,1,7,2,5.]);y=np.r_[11,x[:-1]]
        actual,count=lag_correlation(x,y,[-1,0,1])
        self.assertAlmostEqual(actual[2],1);np.testing.assert_array_equal(count,[6,7,6])
        self.assertAlmostEqual(actual[0],np.corrcoef(x[1:],y[:-1])[0,1])
        acf,_=lag_correlation(x,x,[0,1,2]);self.assertAlmostEqual(acf[0],1)
        self.assertAlmostEqual(acf[2],np.corrcoef(x[:-2],x[2:])[0,1])

    def test_degenerate_or_missing_correlations_are_not_zero_filled(self):
        for x in (np.ones(6),np.array([1,2,np.nan,4,5,6])):
            with self.assertRaises(ValueError):lag_correlation(x,x,[0,1])
        with self.assertRaises(ValueError):lag_correlation(np.arange(6),np.arange(6),[5])


if __name__=='__main__':unittest.main()
