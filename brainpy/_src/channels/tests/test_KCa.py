# -*- coding: utf-8 -*-


import brainpy as bp
import brainpy.math as bm
from absl.testing import parameterized
from brainpy._src.channels import KCa, Ca

class Test_KCa(parameterized.TestCase):
  def test_KCa(self):
    class Neuron(bp.CondNeuGroup):
      def __init__(self, size):
        super(Neuron, self).__init__(size, V_initializer=bp.init.Uniform(-70, -50.))
        self.Ca = Ca.CalciumDetailed(size, KCa=KCa.IAHP_De1994(size))

    model = Neuron(1)
    runner = bp.DSRunner(model,
                         monitors=['V', 'Ca.KCa.p'],
                         progress_bar=False)
    runner.run(10.)
    self.assertTupleEqual(runner.mon['V'].shape, (100, 1))
    self.assertTupleEqual(runner.mon['Ca.KCa.p'].shape, (100, 1))