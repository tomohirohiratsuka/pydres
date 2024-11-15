# **pydres: Python Dependency Resolver**

[![PyPI version](https://badge.fury.io/py/pydres.svg)](https://badge.fury.io/py/pydres)

`pydres` (Python Dependency Resolver) is a lightweight and flexible library to instantiate Python classes with resolved dependencies. It supports hierarchical, string-based, and custom class annotations for dependency injection. With `pydres`, you can easily manage and override dependencies for your Python classes, even when dealing with complex dependency chains.

---

## **Features**

- Resolves both class and string-based type annotations.
- Enables dependency overriding by parameter name or type.
- Recursively instantiates classes based on their constructors.
- Provides utility functions for inspecting and resolving dependencies.

---

## **Installation**

Install `pydres` via pip:

```bash
pip install pydres
```

Or via Poetry:

```bash
poetry add pydres
```

---

## **Usage**

### **Basic Dependency Resolution**

```python
from pydres import instantiate_with_dependencies

class B:
    def __init__(self, message: str = "default message"):
        self.message = message

class A:
    def __init__(self, b: B):
        self.b = b

# Automatically resolves and instantiates dependencies
instance = instantiate_with_dependencies(A)
print(instance.b.message)  # Output: default message
```

---

### **Overriding Dependencies**

```python
overrides = {
    "message": "custom message"
}

instance = instantiate_with_dependencies(B, overrides)
print(instance.message)  # Output: custom message
```

---

### **Resolving String-Based Annotations**

```python
class C:
    pass

class B:
    def __init__(self, c: "C"):
        self.c = c

instance = instantiate_with_dependencies(B)
print(isinstance(instance.c, C))  # Output: True
```

---

### **Handling Circular Dependencies**

`pydres` handles most dependency chains but will raise an error for unresolved circular dependencies.

```python
class J:
    def __init__(self, k: "K"):
        self.k = k

class K:
    def __init__(self, j: J):
        self.j = j

# This will raise a RecursionError
instantiate_with_dependencies(J)
```

---

### **Resolving Multiple Levels of Dependencies**

```python
class Inner:
    def __init__(self, x: int):
        self.x = x

class Outer:
    def __init__(self, inner: Inner):
        self.inner = inner

overrides = {"x": 42}
instance = instantiate_with_dependencies(Outer, overrides)
print(instance.inner.x)  # Output: 42
```

---

## **Utilities**

`pydres` also includes helper methods to inspect and manipulate dependency structures.

- `get_first_custom_init(cls: Type[Any]) -> Optional[Callable[..., None]]`: Get the first custom `__init__` in the inheritance chain.
- `is_builtin_type(param_type: Any) -> bool`: Check if a type is a built-in Python type.
- `is_custom_class(param_type: Any) -> bool`: Check if a type is a user-defined class.
- `resolve_dependency(...)`: Resolve a single dependency using overrides or recursive instantiation.

---

## **Testing**

`pydres` includes comprehensive tests with `pytest`.

To run the tests locally:

```bash
pytest --cov=pydres --cov-report=html
```

---

## **Contributing**

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

---

## **License**

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## **Acknowledgments**

Special thanks to the open-source community for providing the inspiration and tools necessary to build this project.