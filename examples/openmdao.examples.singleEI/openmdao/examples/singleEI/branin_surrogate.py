from openmdao.main.api import Assembly, Component

from openmdao.lib.components.metamodel import MetaModel
from openmdao.lib.components.kriging_surrogate import KrigingSurrogate
from openmdao.lib.components.pareto_filter import ParetoFilter
from openmdao.lib.drivers.doedriver import DOEdriver
from openmdao.lib.drivers.single_crit_ei import SingleCritEI
from openmdao.lib.doegenerators.optlh import OptLatinHypercube
from openmdao.lib.doegenerators.full_factorial import FullFactorial
from openmdao.lib.caserecorders.dbcaserecorder import DBCaseRecorder
from openmdao.lib.caseiterators.dbcaseiter import DBCaseIterator
from openmdao.lib.traits.float import Float
from openmdao.main.api import SequentialWorkflow

from openmdao.main.uncertain_distributions import convert_norm_dist

from openmdao.examples.singleEI.branin_component import BraninComponent

class Broadcaster(Component): 
    x_in = Float(iotype="in",low=-5,high=10)
    x_out = Float(iotype="out")
    
    y_in = Float(iotype="in",low=0,high=15)
    y_out = Float(iotype="out")
    
    def execute(self): 
        self.x_out = self.x_in
        self.y_out = self.y_in

class Analysis(Assembly): 
    def __init__(self,*args,**kwargs):
        super(Analysis,self).__init__(self,*args,**kwargs)
        
        #Drivers
        self.add("DOE_trainer",DOEdriver())
        self.DOE_trainer.DOEgenerator = OptLatinHypercube(12,2)

        #Components
        self.add("branin_meta_model",MetaModel())
        self.branin_meta_model.surrogate = KrigingSurrogate()
        self.branin_meta_model.model = BraninComponent()
        self.branin_meta_model.recorder = DBCaseRecorder('branin_meta_model.db')
        
        self.add("filter",ParetoFilter())
        self.filter.criteria = ['f_xy']
        self.filter.case_set = DBCaseIterator('branin_meta_model.db')

        #Driver Configuration
        self.DOE_trainer.add_parameter("branin_meta_model.x")
        self.DOE_trainer.add_parameter("branin_meta_model.y")
        self.DOE_trainer.add_event("branin_meta_model.train_next")
        self.DOE_trainer.case_outputs = ["branin_meta_model.f_xy"]
        self.DOE_trainer.recorder = DBCaseRecorder('trainer.db')
        
        self.add("EI_driver",SingleCritEI())
        self.EI_driver.workflow.add(self.branin_meta_model)
        self.EI_driver.add_parameter("branin_meta_model.x")
        self.EI_driver.add_parameter("branin_meta_model.y")
        
        self.EI_driver.criterion = "branin_meta_model.f_xy"
        
        #Iteration Heirarchy                
        self.DOE_trainer.workflow.add(self.branin_meta_model)
        
        self.driver.workflow.add(self.DOE_trainer)
        self.driver.workflow.add(self.filter)
        self.driver.workflow.add(self.EI_driver)
        
        #Data Connections
        self.connect("filter.pareto_set","EI_driver.best_case")
        
if __name__ == "__main__":
    from openmdao.main.api import set_as_top
    from openmdao.util.plot import case_db_to_dict
    from matplotlib import pyplot as py, cm 
    from mpl_toolkits.mplot3d import Axes3D
    from numpy import meshgrid,array
    
    analysis = Analysis()
    set_as_top(analysis)
    analysis.run()
    
    data_train = case_db_to_dict('trainer.db',['broadcaster.y_in','broadcaster.x_in','branin_meta_model.f_xy'])
    
    #convert the database data to python objects
    data_train['branin_meta_model.f_xy'] = [convert_norm_dist(x).mu for x in data_train['branin_meta_model.f_xy']]
    
    print [x.inputs for x in analysis.EI_driver.next_case]
    
   