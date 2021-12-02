# -*- coding: utf-8 -*-

r"""This module provides exponential integrators for ODEs.

Exponential integrators are a large class of methods from numerical analysis is based on
the exact integration of the linear part of the initial value problem. Because the linear
part is integrated exactly, this can help to mitigate the stiffness of a differential
equation.

We consider initial value problems of the form,

.. math:: u'(t)=f(u(t)),\qquad u(t_{0})=u_{0},

which can be decomposed of

.. math:: u'(t)=Lu(t)+N(u(t)),\qquad u(t_{0})=u_{0},

where :math:`L={\frac {\partial f}{\partial u}}` (the Jacobian of f) is composed of
linear terms, and :math:`N=f(u)-Lu` is composed of the non-linear terms.

This procedure enjoys the advantage, in each step, that
:math:`{\frac {\partial N_{n}}{\partial u}}(u_{n})=0`.
This considerably simplifies the derivation of the order conditions and improves the
stability when integrating the nonlinearity :math:`N(u(t))`.

Exact integration of this problem from time 0 to a later time :math:`t` can be performed
using `matrix exponentials <https://en.wikipedia.org/wiki/Matrix_exponential>`_ to define
an integral equation for the exact solution:

.. math:: u(t)=e^{Lt}u_{0}+\int _{0}^{t}e^{L(t-\tau )}N\left(t+\tau, u\left(\tau \right)\right)\,d\tau .

This representation of the exact solution is also called as *variation-of-constant formula*.
In the case of :math:`N\equiv 0`, this formulation is the exact solution to the linear
differential equation.


**Exponential Rosenbrock methods**

Exponential Rosenbrock methods were shown to be very efficient in solving large systems
of stiff ODEs. Applying the variation-of-constants formula gives the exact solution at
time :math:`t_{n+1}` with the numerical solution :math:`u_n` as

.. math::
    u(t_{n+1})=e^{h_{n}L}u(t_{n})+\int _{0}^{h_{n}}e^{(h_{n}-\tau )L}N(t_n+\tau, u(t_{n}+\tau ))d\tau .
    :label: discrete-variation-of-constants-formula

where :math:`h_n=t_{n+1}-t_n`.

The idea now is to approximate the integral in :eq:`discrete-variation-of-constants-formula`
by some quadrature rule with nodes :math:`c_{i}` and weights :math:`b_{i}(h_{n}L)`
(:math:`1\leq i\leq s`). This yields the following class of *s-stage* explicit exponential
Rosenbrock methods:

.. math::
    \begin{align}
    U_{ni}=&e^{c_{i}h_{n}L}u_n+h_{n}\sum_{j=1}^{i-1}a_{ij}(h_{n}L)N(U_{nj}),  \\
    u_{n+1}=&e^{h_{n}L}u_n+h_{n}\sum_{i=1}^{s}b_{i}(h_{n}L)N(U_{ni})
    \end{align}

where :math:`U_{ni}\approx u(t_{n}+c_{i}h_{n})`.

The coefficients :math:`a_{ij}(z),b_{i}(z)` are usually chosen as linear combinations of
the entire functions :math:`\varphi _{k}(c_{i}z),\varphi _{k}(z)`, respectively, where

.. math::
    \begin{align}
    \varphi _{k}(z)=&\int _{0}^{1}e^{(1-\theta )z}{\frac {\theta ^{k-1}}{(k-1)!}}d\theta ,\quad k\geq 1, \\
    \varphi _{0}(z)=&e^{z},\\
    \varphi _{k+1}(z)=&{\frac {\varphi_{k}(z)-\varphi _{k}(0)}{z}},\ k\geq 0.
    \end{align}

By introducing the difference :math:`D_{ni}=N(U_{ni})-N(u_{n})`, they can be reformulated
in a more efficient way for implementation as

.. math::
    \begin{align}
    U_{ni}=&u_{n}+c_{i}h_{n}\varphi _{1}(c_{i}h_{n}L)f(u_{n})+h_{n}\sum _{j=2}^{i-1}a_{ij}(h_{n}L)D_{nj}, \\
    u_{n+1}=&u_{n}+h_{n}\varphi _{1}(h_{n}L)f(u_{n})+h_{n}\sum _{i=2}^{s}b_{i}(h_{n}L)D_{ni}.
    \end{align}

where :math:`\varphi_{1}(z)=\frac{e^z-1}{z}`.

In order to implement this scheme with adaptive step size, one can consider, for the purpose
of local error estimation, the following embedded methods

.. math:: {\bar {u}}_{n+1}=u_{n}+h_{n}\varphi _{1}(h_{n}L)f(u_{n})+h_{n}\sum _{i=2}^{s}{\bar {b}}_{i}(h_{n}L)D_{ni},

which use the same stages :math:`U_{ni}` but with weights :math:`{\bar {b}}_{i}`.

For convenience, the coefficients of the explicit exponential Rosenbrock methods together
with their embedded methods can be represented by using the so-called reduced Butcher
tableau as follows:

.. math::
    \begin{array}{c|ccccc}
    c_{2} & & & & & \\
    c_{3} & a_{32} & & & & \\
    \vdots & \vdots & & \ddots & & \\
    c_{s} & a_{s 2} & a_{s 3} & \cdots & a_{s, s-1} \\
    \hline & b_{2} & b_{3} & \cdots & b_{s-1} & b_{s} \\
    & \bar{b}_{2} & \bar{b}_{3} & \cdots & \bar{b}_{s-1} & \bar{b}_{s}
    \end{array}

.. [1] https://en.wikipedia.org/wiki/Exponential_integrator
.. [2] Hochbruck, M., & Ostermann, A. (2010). Exponential integrators. Acta Numerica, 19, 209-286.
"""

import inspect
import logging

import sympy

from brainpy import math, errors, tools
from brainpy.integrators import analysis_by_sympy
from brainpy.integrators import constants as C, utils
from brainpy.integrators.analysis_by_ast import separate_variables
from brainpy.integrators.ode.base import ODEIntegrator

vector_grad = None
logger = logging.getLogger('brainpy.integrators.ode.exponential')

__all__ = [
  'ExponentialEuler',
  'ExponentialAuto',
]


class ExponentialEuler(ODEIntegrator):
  r"""The exponential Euler method for ODEs.

  The simplest exponential Rosenbrock method is the exponential
  Rosenbrock–Euler scheme, which has order 2.

  For an ODE equation of the form

  .. math::

      u^{\prime}=f(u), \quad u(0)=u_{0}

  its schema is given by

  .. math::

      u_{n+1}= u_{n}+h \varphi(hL) f (u_{n})

  where :math:`L=f^{\prime}(u_{n})` and :math:`\varphi(z)=\frac{e^{z}-1}{z}`.

  For a linear ODE system: :math:`u^{\prime} = Ay + B`,
  the above equation is equal to :math:`u_{n+1}= u_{n}e^{hA}-B/A(1-e^{hA})`,
  which is the exact solution for this ODE system.

  Parameters
  ----------
  f : function
    The derivative function.
  dt : optional, float
    The numerical precision.
  var_type : optional, str
    The variable type.
  show_code : bool
    Whether show the code.
  """

  def __init__(self, f, var_type=None, dt=None, name=None, show_code=False,
               timeout=5):
    super(ExponentialEuler, self).__init__(f=f, var_type=var_type, dt=dt,
                                           name=name, show_code=show_code)

    self.timeout = timeout

    # keyword checking
    keywords = {
      C.F: 'the derivative function',
      C.DT: 'the precision of numerical integration',
      'exp': 'the exponential function',
      'math': 'the math module',
    }
    for v in self.variables:
      keywords[f'{v}_new'] = 'the intermediate value'
    utils.check_kws(self.arguments, keywords)

    # build the integrator
    self.build()

  def build(self):
    # check bound method
    if hasattr(self.f, '__self__'):
      self.code_lines = [f'def {self.func_name}({", ".join(["self"] + list(self.arguments))}):']

    # code scope
    closure_vars = inspect.getclosurevars(self.f)
    self.code_scope.update(closure_vars.nonlocals)
    self.code_scope.update(dict(closure_vars.globals))
    self.code_scope['math'] = math

    analysis = separate_variables(self.f)
    variables_for_returns = analysis['variables_for_returns']
    expressions_for_returns = analysis['expressions_for_returns']
    for vi, (key, all_var) in enumerate(variables_for_returns.items()):
      # separate variables
      sd_variables = []
      for v in all_var:
        if len(v) > 1:
          raise ValueError(f'Cannot analyze multi-assignment code line: {v}.')
        sd_variables.append(v[0])
      expressions = expressions_for_returns[key]
      var_name = self.variables[vi]
      diff_eq = analysis_by_sympy.SingleDiffEq(var_name=var_name,
                                               variables=sd_variables,
                                               expressions=expressions,
                                               derivative_expr=key,
                                               scope=self.code_scope,
                                               func_name=self.func_name)
      var = sympy.Symbol(diff_eq.var_name, real=True)
      try:
        s_df_part = tools.timeout(self.timeout)(self.solve)(diff_eq, var)
      except KeyboardInterrupt:
        raise errors.DiffEqError(
          f'{self.__class__} solve {self.f} failed, because '
          f'symbolic differentiation of SymPy timeout due to {self.timeout} s limit. '
          f'Instead, you can use {ExponentialAuto} to make Exponential Euler '
          f'integration due to due to it is capable of '
          f'performing automatic differentiation.'
        )
      # update expression
      update = var + s_df_part

      # The actual update step
      self.code_lines.append(f'  {diff_eq.var_name}_new = {analysis_by_sympy.sympy2str(update)}')
      self.code_lines.append('')

    self.code_lines.append(f'  return {", ".join([f"{v}_new" for v in self.variables])}')
    self.integral = utils.compile_code(code_scope={k: v for k, v in self.code_scope.items()},
                                       code_lines=self.code_lines,
                                       show_code=self.show_code,
                                       func_name=self.func_name)

    if hasattr(self.f, '__self__'):
      host = self.f.__self__
      self.integral = self.integral.__get__(host, host.__class__)

  def solve(self, diff_eq, var):
    f_expressions = diff_eq.get_f_expressions(substitute_vars=diff_eq.var_name)

    # code lines
    self.code_lines.extend([f"  {str(expr)}" for expr in f_expressions[:-1]])

    # get the linear system using sympy
    f_res = f_expressions[-1]
    if len(f_res.code) > 500:
      raise errors.DiffEqError(
        f'Too complex differential equation:\n\n'
        f'{f_res.code}\n\n'
        f'SymPy cannot analyze. Please use {ExponentialAuto} to '
        f'make Exponential Euler integration due to it is capable of '
        f'performing automatic differentiation.'
      )
    df_expr = analysis_by_sympy.str2sympy(f_res.code).expr.expand()
    s_df = sympy.Symbol(f"{f_res.var_name}")
    self.code_lines.append(f'  {s_df.name} = {analysis_by_sympy.sympy2str(df_expr)}')

    # get df part
    s_linear = sympy.Symbol(f'_{diff_eq.var_name}_linear')
    s_linear_exp = sympy.Symbol(f'_{diff_eq.var_name}_linear_exp')
    s_df_part = sympy.Symbol(f'_{diff_eq.var_name}_df_part')
    if df_expr.has(var):
      # linear
      linear = sympy.diff(df_expr, var, evaluate=True)
      # TODO: linear has unknown symbol
      self.code_lines.append(f'  {s_linear.name} = {analysis_by_sympy.sympy2str(linear)}')
      # linear exponential
      self.code_lines.append(f'  {s_linear_exp.name} = math.exp({s_linear.name} * {C.DT})')
      # df part
      df_part = (s_linear_exp - 1) / s_linear * s_df
      self.code_lines.append(f'  {s_df_part.name} = {analysis_by_sympy.sympy2str(df_part)}')
    else:
      # df part
      self.code_lines.append(f'  {s_df_part.name} = {s_df.name} * {C.DT}')
    return s_df_part


class ExponentialEuler2(ODEIntegrator):
  r"""The exponential Euler method for ODEs.

  The simplest exponential Rosenbrock method is the exponential
  Rosenbrock–Euler scheme, which has order 2.

  For an ODE equation of the form

  .. math::

      u^{\prime}=f(u), \quad u(0)=u_{0}

  its schema is given by

  .. math::

      u_{n+1}= u_{n}+h \varphi(hL) f (u_{n})

  where :math:`L=f^{\prime}(u_{n})` and :math:`\varphi(z)=\frac{e^{z}-1}{z}`.

  For a linear ODE system: :math:`u^{\prime} = Ay + B`,
  the above equation is equal to :math:`u_{n+1}= u_{n}e^{hA}-B/A(1-e^{hA})`,
  which is the exact solution for this ODE system.

  Parameters
  ----------
  f : function
    The derivative function.
  dt : optional, float
    The numerical precision.
  var_type : optional, str
    The variable type.
  show_code : bool
    Whether show the code.
  """

  def __init__(self, f, var_type=None, dt=None, name=None, show_code=False,
               timeout=5):
    super(ExponentialEuler, self).__init__(f=f, var_type=var_type, dt=dt,
                                           name=name, show_code=show_code)

    self.timeout = timeout

    # keyword checking
    keywords = {
      C.F: 'the derivative function',
      C.DT: 'the precision of numerical integration',
      'exp': 'the exponential function',
      'math': 'the math module',
    }
    for v in self.variables:
      keywords[f'{v}_new'] = 'the intermediate value'
    utils.check_kws(self.arguments, keywords)

    # build the integrator
    self.build()

  def build(self):
    # check bound method
    if hasattr(self.f, '__self__'):
      self.code_lines = [f'def {self.func_name}({", ".join(["self"] + list(self.arguments))}):']

    # code scope
    closure_vars = inspect.getclosurevars(self.f)
    self.code_scope.update(closure_vars.nonlocals)
    self.code_scope.update(dict(closure_vars.globals))
    self.code_scope['math'] = math

    analysis = separate_variables(self.f)
    variables_for_returns = analysis['variables_for_returns']
    expressions_for_returns = analysis['expressions_for_returns']
    for vi, (key, all_var) in enumerate(variables_for_returns.items()):
      # separate variables
      sd_variables = []
      for v in all_var:
        if len(v) > 1:
          raise ValueError('Cannot analyze multi-assignment code line.')
        sd_variables.append(v[0])
      expressions = expressions_for_returns[key]
      var_name = self.variables[vi]
      diff_eq = analysis_by_sympy.SingleDiffEq(var_name=var_name,
                                               variables=sd_variables,
                                               expressions=expressions,
                                               derivative_expr=key,
                                               scope=self.code_scope,
                                               func_name=self.func_name)

      f_expressions = diff_eq.get_f_expressions(substitute_vars=diff_eq.var_name)

      # code lines
      self.code_lines.extend([f"  {str(expr)}" for expr in f_expressions[:-1]])

      # get the linear system using sympy
      f_res = f_expressions[-1]
      df_expr = analysis_by_sympy.str2sympy(f_res.code).expr.expand()
      s_df = sympy.Symbol(f"{f_res.var_name}")
      self.code_lines.append(f'  {s_df.name} = {analysis_by_sympy.sympy2str(df_expr)}')
      var = sympy.Symbol(diff_eq.var_name, real=True)

      # get df part
      s_linear = sympy.Symbol(f'_{diff_eq.var_name}_linear')
      s_linear_exp = sympy.Symbol(f'_{diff_eq.var_name}_linear_exp')
      s_df_part = sympy.Symbol(f'_{diff_eq.var_name}_df_part')
      if df_expr.has(var):
        # linear
        f = tools.timeout(self.timeout)(lambda: sympy.diff(df_expr, var, evaluate=True))
        try:
          linear = f()
        except KeyboardInterrupt:
          raise errors.DiffEqError(
            f'{self.__class__.__name__} solve {self.f} failed, because '
            f'symbolic differentiation fo SymPy timeout due to {self.timeout} s limit. '
            f'Instead, you can use {ExponentialAuto.__name__} to make Exponential Euler '
            f'integration due to '
          )

        self.code_lines.append(f'  {s_linear.name} = {analysis_by_sympy.sympy2str(linear)}')
        # linear exponential
        self.code_lines.append(f'  {s_linear_exp.name} = math.exp({s_linear.name} * {C.DT})')
        # df part
        df_part = (s_linear_exp - 1) / s_linear * s_df
        self.code_lines.append(f'  {s_df_part.name} = {analysis_by_sympy.sympy2str(df_part)}')
      else:
        # df part
        self.code_lines.append(f'  {s_df_part.name} = {s_df.name} * {C.DT}')

      # update expression
      update = var + s_df_part

      # The actual update step
      self.code_lines.append(f'  {diff_eq.var_name}_new = {analysis_by_sympy.sympy2str(update)}')
      self.code_lines.append('')

    self.code_lines.append(f'  return {", ".join([f"{v}_new" for v in self.variables])}')
    self.integral = utils.compile_code(
      code_scope={k: v for k, v in self.code_scope.items()},
      code_lines=self.code_lines,
      show_code=self.show_code,
      func_name=self.func_name)

    if hasattr(self.f, '__self__'):
      host = self.f.__self__
      self.integral = self.integral.__get__(host, host.__class__)


class ExponentialAuto(ODEIntegrator):
  def __init__(self, f, var_type=None, dt=None, name=None, show_code=False, dyn_var=None, has_aux=False):
    super(ExponentialAuto, self).__init__(f=f, var_type=var_type, dt=dt,
                                          name=name, show_code=show_code)

    self.dyn_var = dyn_var
    self.has_aux = has_aux

    # keyword checking
    keywords = {
      C.F: 'the derivative function',
      C.DT: 'the precision of numerical integration',
      'exp': 'the exponential function',
      'math': 'the math module',
    }
    for v in self.variables:
      keywords[f'{v}_new'] = 'the intermediate value'
    utils.check_kws(self.arguments, keywords)

    # build the integrator
    self.build()

  def build(self):
    global vector_grad
    if vector_grad is None: from brainpy.math.autograd import vector_grad

    assert len(self.variables) == 1

    # TODO : argnums
    value_and_grad = vector_grad(self.f, argnums=0, dyn_vars=self.dyn_var, return_value=True, has_aux=self.has_aux)

    def _int(v, t, *args, dt=math.get_dt(), **kwargs):
      linear, derivative = value_and_grad(v, t, *args, **kwargs)
      z = dt * linear
      phi = (math.exp(z) - 1) / z
      return v + dt * phi * derivative

    self.code_lines = []
    self.code_scope = {}
    self.integral = _int
