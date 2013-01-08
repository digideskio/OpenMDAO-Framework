import numpy as np

from openmdao.main.api import Component
from openmdao.lib.datatypes.api import Float, Array

class LinearDistribution(Component): 
    """takes two Float inputs, and provides n Float outputs with a linear 
    variation between them. Units can be optionally provided """ 

    def __init__(self, n=3 ,units=None): 
        super(LinearDistribution,self).__init__()
        
        self._n = n

        self.add('offset',Float(0.0,iotype="in",desc="offset applied to the linear distribution outputs",units=units))
        self.add('start',Float(iotype='in',desc="input closest to the hub",units=units))
        self.add('end',Float(iotype='in',desc="input closest to the tip",units=units))

        self.add('delta',Float(iotype='out',desc='step size for each of the %d levels'%n, units=units))
        self.add('output',Array(iotype='out',desc='linearly spaced values from start to end inclusive of the bounds', 
                          default_value=np.ones(n),shape=(n,),dtype=Float,units=units))
        

    def execute(self): 
        
        out = np.linspace(self.start,self.end,self._n) + self.offset
        self.output = out
        self.delta = out[1]-out[0]