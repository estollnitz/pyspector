# External imports:
import json

class Config:
    '''A configuration object encapsulating all user-selectable options.'''

    def __init__(self, filename):
        '''Initializes a Config instance.'''
        self._filename = filename
        try:
            with open(filename) as fp:
                settings = json.load(fp)
        except:
            settings = {}
        self._matchCase = settings.get('matchCase', False)
        self._includePrivateMembers = settings.get('includePrivateMembers', False)
        self._includeInheritedMembers = settings.get('includeInheritedMembers', False)
        self._sortByType = settings.get('sortByType', True)
        self._moduleNames = settings.get('moduleNames', ['builtins'])

    @property
    def matchCase(self) -> bool:
        '''Whether or not case-sensitive matching is used.'''
        return self._matchCase

    @matchCase.setter
    def matchCase(self, value: bool) -> None:
        self._matchCase = value
        self._save()

    @property
    def includePrivateMembers(self) -> bool:
        '''Whether or not private members (beginning with "_") are included in the tree.'''
        return self._includePrivateMembers

    @includePrivateMembers.setter
    def includePrivateMembers(self, value: bool) -> None:
        self._includePrivateMembers = value
        self._save()

    @property
    def includeInheritedMembers(self) -> bool:
        '''Whether or not inherited members are included in the tree.'''
        return self._includeInheritedMembers

    @includeInheritedMembers.setter
    def includeInheritedMembers(self, value: bool) -> None:
        self._includeInheritedMembers = value
        self._save()

    @property
    def sortByType(self) -> bool:
        '''Whether or not  members are sorted by type.'''
        return self._sortByType

    @sortByType.setter
    def sortByType(self, value: bool) -> None:
        self._sortByType = value
        self._save()

    @property
    def moduleNames(self) -> list:
        '''The names of all modules that are included in the tree.'''
        return self._moduleNames

    @moduleNames.setter
    def moduleNames(self, value: list) -> None:
        self._moduleNames = value
        self._save()

    def _save(self):
        '''Tries to save the current configuration. Errors are silently ignored.'''
        settings = {
            'matchCase': self.matchCase,
            'includePrivateMembers': self.includePrivateMembers,
            'includeInheritedMembers': self.includeInheritedMembers,
            'sortByType': self.sortByType,
            'moduleNames': self.moduleNames,
        }
        try:
            with open(self._filename, 'w') as fp:
                json.dump(settings, fp)
        except:
            pass
