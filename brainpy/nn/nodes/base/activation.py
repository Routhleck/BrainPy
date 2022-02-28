# -*- coding: utf-8 -*-

from typing import Dict, Optional, Any

from brainpy.math import activations
from brainpy.nn.base import Node

__all__ = [
  'Activation'
]


class Activation(Node):
  """Activation node.

  Parameters
  ----------
  activation : str
    The name of the activation function.
  fun_setting : optional, dict
    The settings for the activation function.
  """

  def __init__(self,
               activation: str = 'relu',
               fun_setting: Optional[Dict[str, Any]] = None,
               name: str = None,
               **kwargs):
    if name is None:
      name = self.unique_name(type_=f'{activation}_activation')
    super(Activation, self).__init__(name=name, **kwargs)

    self._activation = activations.get(activation)
    self._fun_setting = dict() if fun_setting is None else fun_setting
    assert isinstance(self._fun_setting, dict), '"fun_setting" must be a dict.'

  def ff_init(self):
    assert len(self.input_shapes) == 1, f'{type(self).__name__} only support receiving one input. '
    self.set_output_shape(self.input_shapes[0])

  def call(self, ff, **kwargs):
    return self._activation(ff[0], **self._fun_setting)
