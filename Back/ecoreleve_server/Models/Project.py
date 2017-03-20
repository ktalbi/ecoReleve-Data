from ..Models import Base, Customer, ObjectWithDynProp
from sqlalchemy import Column, Integer, Sequence, String, orm, DateTime,  func,ForeignKey


class Project(Base, ObjectWithDynProp):

    FrontModuleForm = 'ProjectForm'
    __tablename__ = 'Project'
    ID = Column(Integer, Sequence('Region__id_seq'), primary_key=True)
    Name = Column(String(250))
    Project_reference = Column(String(250))
    #Customer_ref = Column(String(250))
    Description = Column(String(250))
    Creation_Date = Column(DateTime, default=func.now())
    #FK_Customer = Column(Integer, ForeignKey('Customer.ID'), nullable=True)
    creator = creator = Column(Integer)
    #Geometry = 

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        ObjectWithDynProp.__init__(self)

    @orm.reconstructor
    def init_on_load(self):
         ''' init_on_load is called on the fetch of object '''
         self.__init__()

    def GetType(self):
        return None

