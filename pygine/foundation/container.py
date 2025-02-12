from typing import Any, Type, Union


class Container:
    _instance = None  # The singleton instance of the container

    def __new__(cls) -> "Container":
        if not hasattr(cls, "_instance") or not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__bindings = {}
            cls._instance.__instances = {}
            cls._instance.__resolved = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Container":
        return cls()

    @classmethod
    def set_instance(cls, container: "Container" = None) -> "Container":
        cls._instance = container or cls()
        return cls._instance

    def singleton(self, abstract: str, concrete: Union[None, callable, Type] = None) -> "Container":
        return self._bind(abstract, concrete, True)

    def singleton_if(self, abstract: str, concrete: Union[None, callable, Type] = None) -> "Container":
        return self if self.bound(abstract) else self.singleton(abstract, concrete)

    def regular(self, abstract: str, concrete: Union[None, callable, Type] = None) -> "Container":
        return self._bind(abstract, concrete)

    def regular_if(self, abstract: str, concrete: Union[None, callable, Type] = None) -> "Container":
        return self if self.bound(abstract) else self.regular(abstract, concrete)

    def instance(self, abstract: str, obj: Union[object, Type]) -> "Container":
        self.__instances[abstract] = obj
        return self

    def create(self, abstract: str) -> Any:
        if self.has(abstract):
            return self.resolve(abstract)

        return self.build(abstract)

    def has(self, abstract: str) -> bool:
        return self.bound(abstract) or self.instantiated(abstract)

    def bound(self, abstract: str) -> bool:
        return abstract in self.__bindings

    def resolved(self, abstract: str) -> bool:
        return abstract in self.__resolved or abstract in self.__instances

    def is_shared(self, abstract: str) -> bool:
        return abstract in self.__instances or (
            abstract in self.__bindings and self.__bindings[abstract]["shared"]
        )

    def instantiated(self, abstract: str) -> bool:
        return abstract in self.__instances

    def build(self, abstract: str) -> Any:
        try:
            ref_class = globals()[abstract]
        except KeyError:
            raise ValueError(f"Class {abstract} not found")

        if not hasattr(ref_class, "__init__"):
            raise ValueError(f"Class {abstract} is not instantiable.")

        constructor = getattr(ref_class, "__init__")
        parameters = constructor.__code__.co_varnames[1:]

        resolved_dependencies = [
            self.build(parameter)
            if (parameter_type := constructor.__annotations__.get(parameter))
            and (
                parameter_class := globals().get(parameter_type)
            )  # Assume the class is defined globally
            and parameter_class
            else None
            for parameter in parameters
        ]

        return ref_class(*resolved_dependencies)

    def resolve(self, abstract: str) -> Any:
        if self.instantiated(abstract):
            return self.__instances[abstract]

        concrete = self.__bindings[abstract]["concrete"]
        concrete = concrete() if callable(concrete) else concrete

        self.__instances[abstract] = concrete
        return concrete

    def forget_instance(self, abstract: str) -> None:
        self.__instances.pop(abstract, None)

    def forget_instances(self) -> None:
        self.__instances = {}

    def flush(self) -> None:
        self.__bindings = {}
        self.__instances = {}
        self.__resolved = {}

    def __contains__(self, offset: Any) -> bool:
        return self.has(offset)

    def __getitem__(self, offset: Any) -> Any:
        return self.create(offset)

    def __setitem__(self, offset: Any, value: Any) -> None:
        self._bind(offset, lambda _: value)

    def __delitem__(self, offset: Any) -> None:
        self.__bindings.pop(offset, None)
        self.__instances.pop(offset, None)

    def _bind(self, abstract: str, concrete: Union[None, callable, Type] = None, shared: bool = False) -> "Container":
        self._forget_instance(abstract)

        if concrete is None:
            concrete = abstract

        if not callable(concrete):
            if not isinstance(concrete, str):
                raise ValueError("Argument 'concrete' must be of type callable or str.")
            if concrete not in globals():
                raise ValueError("Argument 'concrete' must be instantiable.")
            concrete = lambda: globals()[concrete]()

        self.__bindings[abstract] = {"concrete": concrete, "shared": shared}

        return self

    def _forget_instance(self, abstract: str) -> None:
        self.__instances.pop(abstract, None)
