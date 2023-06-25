# -*- coding: utf-8 -*-


import brainpy as bp
import brainpy.math as bm
from brainpy import rates
from absl.testing import parameterized
from brainpy._src.synapses import delay_couplings


class Test_delay_couplings(parameterized.TestCase):
  def test_DiffusiveCoupling(self):
    areas = bp.rates.FHN(80, x_ou_sigma=0.01, y_ou_sigma=0.01, name='fhn1')
    conn = bp.synapses.DiffusiveCoupling(areas.x, areas.x, areas.input,
                                         conn_mat=bp.conn.All2All(pre=areas.num, post=areas.num).require('conn_mat'),
                                         initial_delay_data = bp.init.Uniform(0, 0.05))
    net = bp.Network(areas, conn)

    # 运行模拟
    runner = bp.DSRunner(net,
                         monitors=['fhn1.x'],
                         inputs=('fhn1.input', 35.))
    runner(10.)
    self.assertTupleEqual(runner.mon['fhn1.x'].shape, (100, 80))

  def test_AdditiveCoupling(self):
    areas = bp.rates.FHN(80, x_ou_sigma=0.01, y_ou_sigma=0.01, name='fhn2')
    conn = bp.synapses.AdditiveCoupling(areas.x, areas.input,
                                        conn_mat=bp.conn.All2All(pre=areas.num, post=areas.num).require('conn_mat'),
                                        initial_delay_data=bp.init.Uniform(0, 0.05))
    net = bp.Network(areas, conn)

    # 运行模拟
    runner = bp.DSRunner(net,
                         monitors=['fhn2.x'],
                         inputs=('fhn2.input', 35.))
    runner(10.)
    self.assertTupleEqual(runner.mon['fhn2.x'].shape, (100, 80))
