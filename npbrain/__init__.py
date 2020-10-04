# -*- coding: utf-8 -*-

__version__ = "1.0.0"

# "profile" module
from . import profile, inputs

# "core" module
from . import core
from .integrator import integrator
from .integrator.integrator import integrate
from .core.network import *
from .core.neuron_group import *
from .core.synapse_connection import *
from .core import types


#
# # reload functions
# def _reload():
#     global judge_spike
#     global clip
#
#     judge_spike = get_spike_judger()
#     clip = get_clip()
#
#

