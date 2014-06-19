def registry_metaclass(storage):
    class RegistryMeta(type):
        def __init__(cls, name, bases, attrs):
            super(RegistryMeta, cls).__init__(name, bases, attrs)

            id = getattr(cls, 'id', None)
            if not id:
                return

            if id in storage:
                raise KeyError("Already registered: %s" % name)

            storage[id] = cls

    return RegistryMeta
