from ..Models import (
    Project,
    Base,
    ProjectList
)
from sqlalchemy import select, desc, join
from collections import OrderedDict
from sqlalchemy.exc import IntegrityError
from ..controllers.security import RootCore , context_permissions
from . import DynamicObjectView, DynamicObjectCollectionView, CustomView
from ..Models import Project


prefix = 'projects'


class ProjectView(DynamicObjectView):

    model = Project

    def __init__(self, ref, parent):
        DynamicObjectView.__init__(self, ref, parent)

    def __getitem__(self, ref):
        if ref in self.actions:
            self.retrieve = self.actions.get(ref)
            return self
        return self.get(ref)


class ProjectsView(DynamicObjectCollectionView):

    Collection = ProjectList
    item = ProjectView
    formModuleName = 'ProjectForm'
    gridModuleName = 'ProjectFilter'

    def __init__(self, ref, parent):
        DynamicObjectCollectionView.__init__(self, ref, parent)
        self.__acl__ = context_permissions[ref]


    # def getForm(self, objectType=None, moduleName=None, mode='edit'):
    #     if objectType is None:
    #         objectType = self.request.params['ObjectType']
    #     Conf = self.getConf(moduleName)
    #     self.setType(int(objectType))
    #     schema = self.objectDB.GetDTOWithSchema(Conf, mode)
    #     return schema

    # def insert(self):
    #     try:
    #         response = DynamicObjectCollectionView.insert(self)
    #     except IntegrityError as e:
    #         self.session.rollback()
    #         self.request.response.status_code = 520
    #         response = self.request.response
    #         response.text = "This identifier is already used for another project"
    #         pass
    #     return response


RootCore.listChildren.append(('projects', ProjectsView))