# External imports:
import pkgutil
import sys

class ModuleData:
    '''Provides the name and location of a module, as well as a list of submodules.'''

    def __init__(self, name, location):
        '''Initializes a ModuleData instance.'''
        self.name = name
        self.location = location
        self.children = []

class ModuleSelectionModel:
    '''
    Represents a hierarchical list of all available modules.

    Includes built-in modules as well as modules available to import from the system path.
    '''

    def __init__(self):
        '''Initializes a ModuleSelectionModel instance.'''
        # Create root node.
        self._rootModuleData = ModuleData('root', None)

        # Include all built-in modules.
        for moduleName in sys.builtin_module_names:
            self._addModule(self._rootModuleData, moduleName, 'built-in')

        # Walk all available modules.
        for moduleInfo in pkgutil.walk_packages(onerror = self._handleError):
            location = ''
            if hasattr(moduleInfo.module_finder, 'path'):
                location = moduleInfo.module_finder.path
            parentData = self._findParentData(moduleInfo.name)
            self._addModule(parentData, moduleInfo.name, location)

    @property
    def allModules(self):
        '''The list of root-level module data.'''
        return self._rootModuleData.children

    def _handleError(self, packageName: str):
        '''Ignores any errors encountered while importing a package.'''
        pass

    def _findParentData(self, moduleName: str) -> ModuleData:
        '''Determines the module data to use as a parent for the given module name.'''
        parts = moduleName.split(sep = '.')
        parentData = self._rootModuleData
        name = None
        for part in parts:
            name = part if name == None else f'{name}.{part}'
            data = self._findData(parentData, name)
            if data == None:
                break
            parentData = data
        return parentData

    def _findData(self, parentData: ModuleData, name: str) -> ModuleData:
        '''Returns the first child of parentData that has the given name, or None.'''
        return next((childData for childData in parentData.children if childData.name == name), None)

    def _addModule(self, parentData: ModuleData, name: str, location: str) -> None:
        '''Appends module data to the specified parent.'''
        moduleData = ModuleData(name, location)
        parentData.children.append(moduleData)
