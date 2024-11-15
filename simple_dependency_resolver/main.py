import importlib
import inspect
from inspect import Parameter
from typing import Any, Type, Dict, Union, Optional, Callable, TypeVar

from simple_dependency_resolver.const import BUILTIN_TYPES, SPECIAL_TYPES
from simple_dependency_resolver.regexp import special_type_pattern

T = TypeVar("T", bound=Any)
DependencyResolverOverrides = Dict[Union[Type, str], Any]


def get_first_custom_init(original_class: Type[Any]) -> Optional[Callable[..., None]]:
	"""
	Get the first custom __init__ method in the class hierarchy
	"""
	for cls in inspect.getmro(original_class):
		init_method = cls.__dict__.get('__init__')
		if init_method and not isinstance(init_method, type(object.__init__)):
			return init_method
	return None


def is_builtin_type(param_type: Any) -> bool:
	"""Check if a param type is a built-in type"""
	return inspect.isclass(param_type) and param_type.__name__ in BUILTIN_TYPES


def is_custom_class(param_type: Any) -> bool:
	"""
	Check if a param type is a custom class.
	It must not be a built-in type or a special type like Union or Optional.
	"""

	if not inspect.isclass(param_type):
		return False

	if is_builtin_type(param_type):
		return False

	if param_type.__name__ in SPECIAL_TYPES:
		return False

	return True


def is_custom_class_string_annotation(param: Parameter) -> bool:
	"""
	Check if a parameter is a string type annotation for a custom class,
	excluding special types and built-in types.
	"""
	annotation = param.annotation
	if not isinstance(annotation, str):
		return False

	# Check if it's a built-in type or special type using exact matches
	if annotation in BUILTIN_TYPES or special_type_pattern.search(annotation):
		return False

	# If it's not built-in or special, it's likely a custom class string annotation
	return True


def find_class_in_module(parent_class: Type[Any], class_name: str) -> Optional[Type[Any]]:
	"""
	Find a class by name within the module of the given parent class.

	Args:
		parent_class (Type[Any]): The reference class to determine the module.
		class_name (str): The name of the class to find as a string.

	Returns:
		Type[Any]: The resolved class if found and it is indeed a class.

	Raises:
		AttributeError: If the class is not found in the module or is not a valid class.
	"""
	# Get the module where `parent_class` is defined
	module = importlib.import_module(parent_class.__module__)

	# Try to retrieve `class_name` from the module
	potential_class = getattr(module, class_name, None)

	# Raise an error if the class is not found
	if potential_class is None:
		raise AttributeError(f"Class '{class_name}' not found in module '{parent_class.__module__}'")

	# Check if the retrieved attribute is a class
	if not inspect.isclass(potential_class):
		raise AttributeError(f"Found '{class_name}' in module '{parent_class.__module__}', but it is not a class.")

	# Return the resolved class if valid
	return potential_class


def resolve_dependency_from_overrides(
		original_class: Type[Any],
		name: str,
		param: Parameter,
		overrides: DependencyResolverOverrides
) -> Optional[Any]:
	"""
	Check if dependency is provided in overrides by name or type
	Raises: AttributeError: If the dependency is a string reference and the class is not found
	"""
	if name in overrides:  # Check if the dependency is provided by name
		return overrides[name]
	elif param.annotation in overrides:  # Check if the dependency is provided by type
		return overrides[param.annotation]
	elif is_custom_class_string_annotation(param):  # Check if the dependency is a string reference
		referenced_class = find_class_in_module(original_class, param.annotation)
		if referenced_class in overrides:
			return overrides[referenced_class]

	return None


def resolve_dependency(
		original_class: Type[T], name: str, param: Parameter, overrides: DependencyResolverOverrides
) -> Any:
	"""Resolve a single dependency, either from overrides or by recursively creating it."""
	if name == "self":
		return None

	# Step 1: Check if an override exists for this dependency
	override = resolve_dependency_from_overrides(original_class, name, param, overrides)
	if override is not None:
		return override

	# Step 2: Resolve string-based class references to actual types
	dependency = param.annotation
	if is_custom_class_string_annotation(param):
		dependency = find_class_in_module(original_class, dependency)

	# Step 3: Recursively resolve the dependency if it's a non-builtin class
	if is_custom_class(dependency):
		return instantiate_with_dependencies(dependency, overrides)

	# Step 5: Use the default parameter if available
	return param.default if param.default is not param.empty else None


def instantiate_with_dependencies(
		original_class: Type[T],
		overrides: DependencyResolverOverrides = None
) -> T:
	"""
	Create a service with dependencies
	This method will recursively resolve dependencies for the service.
	And classes will be resolved with overrides if provided.
	Overrides can be specified as a dictionary with class references or strings as parameter name.
	"""
	if overrides is None:
		overrides = {}

	# Check if __init__ is overridden by user
	init_method = get_first_custom_init(original_class)

	if not init_method:
		# If __init__ is not overridden, directly instantiate the class
		return original_class()

	# Get the constructor arguments
	signature = inspect.signature(init_method)
	kwargs = {}

	for name, param in signature.parameters.items():
		resolved = resolve_dependency(original_class, name, param, overrides)
		if resolved is not None:
			kwargs[name] = resolved

	return original_class(**kwargs)
