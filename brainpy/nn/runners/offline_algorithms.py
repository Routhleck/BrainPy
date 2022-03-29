# -*- coding: utf-8 -*-

import brainpy.math as bm
from brainpy.base import Base

__all__ = [
  # base class for offline training algorithm
  'OfflineAlgorithm',

  'RidgeRegression',
  'LinearRegression',

  'LassoRegression',
  'elastic_net_regression',
  'logistic_regression',
  'polynomial_regression',
  'stepwise_regression',

  'get_supported_offline_methods',
  'register_offline_method',
]

name2func = dict()


class OfflineAlgorithm(Base):
  """Base class for offline training algorithm."""

  def __init__(self, name=None):
    super(OfflineAlgorithm, self).__init__(name=name)

  def __call__(self, x, y):
    """The training procedure.

    Parameters
    ----------
    x: JaxArray, jax.numpy.ndarray, numpy.ndarray
      The input data with the shape of `(num_time, num_feature)`.
    y: JaxArray, jax.numpy.ndarray, numpy.ndarray
      The target data with the shape of `(num_time, num_feature)`.

    Returns
    -------
    weight: JaxArray
      The weights after fit.
    """
    raise NotImplementedError('Must implement the __call__ function by the subclass itself.')

  def __repr__(self):
    return self.__class__.__name__


class RidgeRegression(OfflineAlgorithm):
  """Training algorithm of ridge regression.

  Parameters
  ----------
  beta: float
    The regularization coefficient.
  """

  def __init__(self, beta=1e-7, name=None):
    super(RidgeRegression, self).__init__(name=name)
    self.beta = beta

  def __call__(self, x, y):
    # checking
    x = bm.asarray(x)
    y = bm.asarray(y)
    assert x.ndim == 2, f'"x" must be a 2d tensor, but got the shape of {x.shape}.'
    assert y.ndim == 2, f'"y" must be a 2d tensor, but got the shape of {y.shape}.'
    assert x.shape[0] == y.shape[0], (f'The first axis (num_time) of "x" and "y" must be the '
                                      f'same, but we got {x.shape[0]} != {y.shape[0]}')
    # solving
    temp = x.T @ x
    if self.beta > 0.:
      temp += self.beta * bm.eye(x.shape[-1])
    weights = bm.linalg.pinv(temp) @ (x.T @ y)
    return weights

  def __repr__(self):
    return f'{self.__class__.__name__}(beta={self.beta})'


name2func['ridge'] = RidgeRegression


class LinearRegression(OfflineAlgorithm):
  """Training algorithm of least-square regression."""

  def __init__(self, name=None):
    super(LinearRegression, self).__init__(name=name)

  def __call__(self, x, y):
    # checking
    x = bm.asarray(x)
    y = bm.asarray(y)
    assert x.ndim == 2, f'"x" must be a 2d tensor, but got the shape of {x.shape}.'
    assert y.ndim == 2, f'"y" must be a 2d tensor, but got the shape of {y.shape}.'
    assert x.shape[0] == y.shape[0], (f'The first axis (num_time) of "x" and "y" must be the '
                                      f'same, but we got {x.shape[0]} != {y.shape[0]}')
    # solving
    weights = bm.linalg.lstsq(x, y)
    return weights[0]


name2func['linear'] = LinearRegression
name2func['lstsq'] = LinearRegression


class LassoRegression(OfflineAlgorithm):
  """Lasso regression method for offline training.

  Parameters
  ----------
  alpha: float
    Constant that multiplies the L1 term. Defaults to 1.0.
    `alpha = 0` is equivalent to an ordinary least square.
  max_iter: int
    The maximum number of iterations.
  """
  def __init__(self, alpha=1.0, max_iter=1000, name=None):
    super(LassoRegression, self).__init__(name=name)
    self.alpha = alpha
    self.max_iter = max_iter

  def __call__(self, *args, **kwargs):
    pass


name2func['lasso'] = LassoRegression


def elastic_net_regression(x, y, train_pars):
  pass


name2func['elastic_net'] = elastic_net_regression


def logistic_regression(x, y, train_pars):
  pass


name2func['logistic'] = logistic_regression


def polynomial_regression(x, y, train_pars):
  pass


name2func['polynomial'] = polynomial_regression


def stepwise_regression(x, y, train_pars):
  pass


name2func['stepwise'] = stepwise_regression


def get_supported_offline_methods():
  """Get all supported offline training methods."""
  return tuple(name2func.keys())


def register_offline_method(name, method):
  """Register a new ODE integrator.

  Parameters
  ----------
  name: str
    The method name.
  method: callable
    The function method.
  """
  if name in name2func:
    raise ValueError(f'"{name}" has been registered in offline training methods.')
  if not callable(method):
    raise ValueError(f'"method" must be an instance of callable function, but we got {type(method)}')
  name2func[name] = method


def get(name):
  """Get the training function according to the training method name."""
  if name not in name2func:
    raise ValueError(f'All offline methods are: {get_supported_offline_methods()}.\n'
                     f'But we got {name}.')
  return name2func[name]