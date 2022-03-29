# -*- coding: utf-8 -*-


from typing import Dict

from brainpy import math as bm
from brainpy.errors import DiffEqError
from brainpy.integrators import constants, utils
from brainpy.integrators.base import Integrator
from brainpy.integrators.constants import DT
from brainpy.tools.checking import check_dict_data

__all__ = [
  'ODEIntegrator',
]


def f_names(f):
  func_name = constants.unique_name('ode')
  if f.__name__.isidentifier():
    func_name += '_' + f.__name__
  return func_name


class ODEIntegrator(Integrator):
  """Numerical Integrator for Ordinary Differential Equations (ODEs).

  Parameters
  ----------
  f : callable
    The derivative function.
  var_type: str
    The type for each variable.
  dt: float, int
    The numerical precision.
  name: str
    The integrator name.
  """

  def __init__(
      self,
      f,
      var_type=None,
      dt=None,
      name=None,
      show_code=False,
      state_delays: Dict[str, bm.AbstractDelay] = None,
      neutral_delays: Dict[str, bm.NeutralDelay] = None
  ):

    dt = bm.get_dt() if dt is None else dt
    parses = utils.get_args(f)
    variables = parses[0]  # variable names, (before 't')
    parameters = parses[1]  # parameter names, (after 't')
    arguments = parses[2]  # function arguments

    # super initialization
    super(ODEIntegrator, self).__init__(name=name,
                                        variables=variables,
                                        parameters=parameters,
                                        arguments=arguments,
                                        dt=dt,
                                        state_delays=state_delays)

    # others
    self.show_code = show_code
    self.var_type = var_type  # variable type

    # derivative function
    self.derivative = {constants.F: f}
    self.f = f

    # code scope
    self.code_scope = {constants.F: f}

    # code lines
    self.func_name = f_names(f)
    self.code_lines = [f'def {self.func_name}({", ".join(self.arguments)}):']

    # neutral delays
    self._neutral_delays = dict()
    if neutral_delays is not None:
      check_dict_data(neutral_delays, key_type=str, val_type=bm.NeutralDelay)
      for key, delay in neutral_delays.items():
        if key not in self.variables:
          raise DiffEqError(f'"{key}" is not defined in the variables: {self.variables}')
        self._neutral_delays[key] = delay
    self.register_implicit_nodes(self._neutral_delays)

  @property
  def neutral_delays(self):
    """neutral delays."""
    return self._neutral_delays

  @neutral_delays.setter
  def neutral_delays(self, value):
    raise ValueError('Cannot set "neutral_delays" by users.')

  def __call__(self, *args, **kwargs):
    assert self.integral is not None, 'Please build the integrator first.'

    # check arguments
    for i, arg in enumerate(args):
      kwargs[self.arguments[i]] = arg

    # integral
    new_vars = self.integral(**kwargs)
    if len(self.variables) == 1:
      dict_vars = {self.variables[0]: new_vars}
    else:
      dict_vars = {k: new_vars[i] for i, k in enumerate(self.variables)}

    dt = kwargs.pop(DT, self.dt)
    # update neutral delay variables
    if len(self.neutral_delays):
      kwargs.update(dict_vars)
      new_devs = self.f(**kwargs)
      if len(self.variables) == 1:
        new_devs = {self.variables[0]: new_devs}
      else:
        new_devs = {k: new_devs[i] for i, k in enumerate(self.variables)}
      for key, delay in self.neutral_delays.items():
        if isinstance(delay, bm.LengthDelay):
          delay.update(new_devs[key])
        elif isinstance(delay, bm.TimeDelay):
          delay.update(kwargs['t'] + dt, new_devs[key])
        else:
          raise ValueError('Unknown delay variable. We only supports '
                           'brainpy.math.LengthDelay, brainpy.math.TimeDelay, '
                           'brainpy.math.NeutralDelay. '
                           f'While we got {delay}')

    # update state delay variables
    for key, delay in self.state_delays.items():
      if isinstance(delay, bm.LengthDelay):
        delay.update(dict_vars[key])
      elif isinstance(delay, bm.TimeDelay):
        delay.update(kwargs['t'] + dt, dict_vars[key])
      else:
        raise ValueError('Unknown delay variable. We only supports '
                         'brainpy.math.LengthDelay, brainpy.math.TimeDelay, '
                         'brainpy.math.NeutralDelay. '
                         f'While we got {delay}')

    return new_vars
