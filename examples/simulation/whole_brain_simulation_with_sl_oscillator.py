# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np

import brainpy as bp
import brainpy.math as bm

bp.check.turn_off()


def bifurcation_analysis():
  model = bp.dyn.StuartLandauOscillator(1, method='exp_auto')
  pp = bp.analysis.Bifurcation2D(
    model,
    target_vars={'x': [-2, 2], 'y': [-2, 2]},
    pars_update={'x_ext': 0., 'y_ext': 0., 'w': 0.2},
    target_pars={'a': [-2, 2]},
    resolutions={'a': 0.01}
  )
  pp.plot_bifurcation()
  pp.show_figure()


class Network(bp.dyn.Network):
  def __init__(self):
    super(Network, self).__init__()

    # Please download the processed data "hcp.npz" of the
    # ConnectomeDB of the Human Connectome Project (HCP)
    # from the following link:
    # - https://share.weiyun.com/wkPpARKy
    hcp = np.load('hcp.npz')
    conn_mat = bm.asarray(hcp['Cmat'])
    bm.fill_diagonal(conn_mat, 0)
    gc = 0.6  # global coupling strength

    self.sl = bp.dyn.StuartLandauOscillator(80, x_ou_sigma=0.14, y_ou_sigma=0.14,
                                            name='sl', method='exp_auto')
    self.coupling = bp.dyn.DiffusiveDelayCoupling(self.sl, self.sl,
                                                  'x->input',
                                                  conn_mat=conn_mat * gc,
                                                  delay_initializer=bp.init.Uniform(0, 0.05))

  def update(self, _t, _dt):
    self.coupling.update(_t, _dt)
    self.sl.update(_t, _dt)


def simulation():
  net = Network()
  runner = bp.dyn.DSRunner(net, monitors=['sl.x'])
  runner.run(6e3)

  plt.rcParams['image.cmap'] = 'plasma'
  fig, axs = plt.subplots(1, 2, figsize=(12, 4))
  fc = bp.measure.functional_connectivity(runner.mon['sl.x'])
  ax = axs[0].imshow(fc)
  plt.colorbar(ax, ax=axs[0])
  axs[1].plot(runner.mon.ts, runner.mon['sl.x'][:, ::5], alpha=0.8)
  plt.tight_layout()
  plt.show()


if __name__ == '__main__':
  bifurcation_analysis()
  simulation()