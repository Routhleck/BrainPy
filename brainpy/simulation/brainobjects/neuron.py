# -*- coding: utf-8 -*-

from brainpy import errors
from brainpy.simulation import utils
from brainpy.simulation.base import DynamicSystem

__all__ = [
  'NeuGroup',
]


class NeuGroup(DynamicSystem):
  """Neuron Group.

  Parameters
  ----------
  size : int, tuple of int, list of int
      The neuron group geometry.
  steps : function, list of function, tuple of function, dict of (str, function), optional
      The step functions.
  name : str, optional
      The group name.
  """

  def __init__(self, size, name=None, steps=('update',), **kwargs):
    # size
    # ----
    if isinstance(size, (list, tuple)):
      if len(size) <= 0:
        raise errors.ModelDefError('size must be int, or a tuple/list of int.')
      if not isinstance(size[0], int):
        raise errors.ModelDefError('size must be int, or a tuple/list of int.')
      size = tuple(size)
    elif isinstance(size, int):
      size = (size,)
    else:
      raise errors.ModelDefError('size must be int, or a tuple/list of int.')
    self.size = size
    self.num = utils.size2len(size)

    # initialize
    # ----------
    super(NeuGroup, self).__init__(steps=steps, name=name, **kwargs)

  def update(self, _t, _i):
    raise NotImplementedError
