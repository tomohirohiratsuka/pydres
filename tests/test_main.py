import inspect
from typing import  Any, Optional, Union, List, Dict, Set, Tuple
from unittest.mock import patch

import pytest
from datetime import datetime

from simple_dependency_resolver.main import get_first_custom_init, is_custom_class_string_annotation, \
	resolve_dependency_from_overrides, find_class_in_module, is_builtin_type, is_custom_class, resolve_dependency, \
	instantiate_with_dependencies


class B:
	def __init__(self, c: 'C', message: str = "default message"):
		self.c = c
		self.message = message


class AWithStringAnnotation:
	def __init__(self, b: 'B'):
		self.b = b


class AWithDirectTypeAnnotation:
	def __init__(self, b: B):
		self.b = b


class C:
	pass


class J:
	def __init__(self, k: "K"):
		self.k = k


class K:
	def __init__(self, j: J):
		self.j = j


sample_const = 'sample'


class TestInstantiateWithDependencies:
	class TestGetFirstCustomInit:

		def test_should_return_none_when_no_custom_init(self):
			# Given
			class TestClass:
				pass

			# When
			result = get_first_custom_init(TestClass)

			# Then
			assert result is None

		def test_should_return_init_method(self):
			# Given
			class TestClass:
				def __init__(self):
					self.a = 1

			# When
			result = get_first_custom_init(TestClass)

			# Then
			assert result == TestClass.__init__

		def test_should_return_parent_init_method(self):
			# Given
			class ParentTestClass:
				def __init__(self):
					self.a = 1

			class TestClass(ParentTestClass):
				pass

			# When
			result = get_first_custom_init(TestClass)

			# Then
			assert result == ParentTestClass.__init__

		def test_should_return_none_when_no_custom_init_in_parent(self):
			# Given
			class ParentTestClass:
				pass

			class TestClass(ParentTestClass):
				pass

			# When
			result = get_first_custom_init(TestClass)

			# Then
			assert result is None

		@pytest.mark.parametrize(
			'built_in_type',
			[
				str,
				int,
				float,
				bool,
				list,
				dict,
				set,
				tuple,
			]
		)
		def test_should_return_none_when_built_in_type(self, built_in_type):
			# When
			result = get_first_custom_init(built_in_type)

			# Then
			assert result is None

		def test_should_raise_attribute_error_when_it_can_not_be_type(self):
			with pytest.raises(AttributeError) as e:
				get_first_custom_init('sample')

			assert str(e.value) == "'str' object has no attribute '__mro__'"

		def test_should_return_init_with_default_arguments(self):
			class TestClass:
				def __init__(self, value=42):
					self.value = value

			result = get_first_custom_init(TestClass)
			assert result == TestClass.__init__

		def test_should_return_child_init_when_overridden(self):
			class ParentClass:
				def __init__(self):
					self.a = "parent"

			class ChildClass(ParentClass):
				def __init__(self):
					super().__init__()
					self.a = "child"

			result = get_first_custom_init(ChildClass)
			assert result == ChildClass.__init__

		def test_should_return_first_custom_init_in_mro_with_multiple_inheritance(self):
			class Grandparent:
				def __init__(self):
					self.a = "grandparent"

			class Parent1(Grandparent):
				def __init__(self):
					super().__init__()
					self.a = "parent1"

			class Parent2:
				def __init__(self):
					self.a = "parent2"

			class Child(Parent1, Parent2):
				pass

			result = get_first_custom_init(Child)
			assert result == Parent1.__init__

	class TestIsCustomClassStringAnnotation:

		def test_should_return_true_for_custom_class_string_type_annotation(self):
			# Given
			param = inspect.Parameter('b', inspect.Parameter.KEYWORD_ONLY, annotation='B')

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is True

		@pytest.mark.parametrize(
			'annotation',
			[
				str,
				int,
				float,
				bool,
				list,
				dict,
				set,
				tuple,
				Any,
				Optional[str],
				Union[str, int],
				List[str],
				Dict[str, int],
				Set[str],
				Tuple[str, int],
			]
		)
		def test_should_return_false_for_builtin_type_annotation(self, annotation):
			# Given
			param = inspect.Parameter('invalid', inspect.Parameter.KEYWORD_ONLY, annotation=annotation)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is False

		@pytest.mark.parametrize(
			'annotation',
			[
				'str',  # ビルトインタイプの文字列形式
				'int',
				'float',
				'bool',
				'list',
				'dict',
				'set',
				'tuple',
				'Any',
				'Optional[str]',
				'Union[str, int]',
				'List[str]',
				'Dict[str, int]',
				'Set[str]',
				'Tuple[str, int]',
				'Final[str]',
				'ClassVar[str]',
				'Protocol',
			]
		)
		def test_should_return_false_for_builtin_type_string_annotations(self, annotation):
			# Given
			param = inspect.Parameter('invalid', inspect.Parameter.KEYWORD_ONLY, annotation=annotation)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is False

		@pytest.mark.parametrize(
			'annotation',
			[
				'AnyCustomClass',
				'UnionCustomClass',
				'TypeVarCustomClass',
				'CallableCustomClass',
				'OptionalCustomClass',
				'LiteralCustomClass',
				'FinalCustomClass',
				'ClassVarCustomClass',
				'ProtocolCustomClass',
				'ListCustomClass',
				'DictCustomClass',
				'SetCustomClass',
				'TupleCustomClass',
			]
		)
		def test_should_return_true_when_custom_class_string_include_special_types(self, annotation):
			# Given
			param = inspect.Parameter('fine', inspect.Parameter.KEYWORD_ONLY, annotation=annotation)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is True

		def test_should_return_false_for_any_type_annotation(self):
			# Given
			param = inspect.Parameter('invalid', inspect.Parameter.KEYWORD_ONLY, annotation=Any)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is False

		def test_should_return_false_for_none_annotation(self):
			# Given
			param = inspect.Parameter('invalid', inspect.Parameter.KEYWORD_ONLY, annotation=None)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is False

		def test_should_return_false_for_direct_custom_class_annotation(self):
			# Given
			class CustomClass:
				pass

			param = inspect.Parameter('invalid', inspect.Parameter.KEYWORD_ONLY, annotation=CustomClass)

			# When
			result = is_custom_class_string_annotation(param)

			# Then
			assert result is False

	class TestResolveDependencyFromOverrides:

		@pytest.mark.parametrize(
			'original_class',
			[
				AWithStringAnnotation,
				AWithDirectTypeAnnotation
			]
		)
		def test_should_return_override_when_name_in_overrides(self, original_class):
			# Given
			overrides = {
				'b': 'override'
			}
			signature = inspect.signature(original_class.__init__)
			items = list(signature.parameters.items())
			name, param = items[1]

			# When
			result = resolve_dependency_from_overrides(original_class, name, param, overrides)

			# Then
			assert result == 'override'

		@pytest.mark.parametrize(
			'original_class',
			[
				AWithStringAnnotation,
				AWithDirectTypeAnnotation
			]
		)
		def test_should_return_override_when_type_in_overrides(self, original_class):
			# Given
			overrides = {
				B: 'override'
			}
			signature = inspect.signature(original_class.__init__)
			items = list(signature.parameters.items())
			name, param = items[1]

			# When
			result = resolve_dependency_from_overrides(original_class, name, param, overrides)

			# Then
			assert result == 'override'

		@pytest.mark.parametrize(
			'original_class',
			[
				AWithStringAnnotation,
				AWithDirectTypeAnnotation
			]
		)
		def test_should_return_override_when_name_in_overrides_and_type_in_overrides(self, original_class):
			# Given
			overrides = {
				'b': 'override',
				B: 'override2'
			}
			signature = inspect.signature(original_class.__init__)
			items = list(signature.parameters.items())
			name, param = items[1]

			# When
			result = resolve_dependency_from_overrides(original_class, name, param, overrides)

			# Then
			assert result == 'override'  # Ensures name takes priority

		@pytest.mark.parametrize(
			'original_class',
			[
				AWithStringAnnotation,
				AWithDirectTypeAnnotation
			]
		)
		def test_should_return_none_when_no_override(self, original_class):
			signature = inspect.signature(original_class.__init__)
			items = list(signature.parameters.items())
			name, param = items[1]

			# When
			result = resolve_dependency_from_overrides(original_class, name, param, {})

			# Then
			assert result is None

		@pytest.mark.parametrize(
			'original_class',
			[
				AWithStringAnnotation,
				AWithDirectTypeAnnotation
			]
		)
		def test_should_raise_error_for_unresolved_string_reference(self, original_class):
			# Given
			signature = inspect.signature(original_class.__init__)
			items = list(signature.parameters.items())
			name, param = items[1]

			# Corrupting the reference in annotation to an invalid class name
			param._annotation = "NonExistentClass"

			# When
			with pytest.raises(AttributeError) as e:
				resolve_dependency_from_overrides(original_class, name, param, {})

			# Then
			assert str(
				e.value) == "Class 'NonExistentClass' not found in module 'test_main'"

	class TestFindClassInModule:

		def test_should_return_found_class_which_defined_in_module(self):
			# When
			result = find_class_in_module(AWithStringAnnotation, 'B')

			# Then
			assert result == B

		def test_should_return_found_class_which_imported_in_module(self):
			# When
			result = find_class_in_module(AWithStringAnnotation, 'datetime')

			# Then
			assert result == datetime

		def test_should_raise_attribute_error_when_class_not_found(self):
			# When
			with pytest.raises(AttributeError) as e:
				find_class_in_module(AWithStringAnnotation, 'NonExistentClass')

			# Then
			assert str(
				e.value) == "Class 'NonExistentClass' not found in module 'test_main'"

		def test_should_raise_attribute_error_when_attribute_is_not_class(self):
			# When
			with pytest.raises(AttributeError) as e:
				find_class_in_module(AWithStringAnnotation, 'sample_const')

			# Then
			assert str(
				e.value) == "Found 'sample_const' in module 'test_main', but it is not a class."

	class TestIsBuiltinType:
		@pytest.mark.parametrize(
			'builtin_type',
			[
				str,
				int,
				float,
				bool,
				list,
				dict,
				set,
				tuple,
			]
		)
		def test_should_return_true_for_builtin_types(self, builtin_type):
			# When
			result = is_builtin_type(builtin_type)

			# Then
			assert result is True

		def test_should_return_false_for_custom_types(self):
			# When
			result = is_builtin_type(B)

			# Then
			assert result is False

		def test_should_return_false_for_special_types(self):
			# When
			result = is_builtin_type(Any)

			# Then
			assert result is False

	class TestIsCustomClass:

		def test_should_return_true_for_custom_class(self):
			# When
			result = is_custom_class(B)

			# Then
			assert result is True

		@pytest.mark.parametrize(
			'builtin_type',
			[
				str,
				int,
				float,
				bool,
				list,
				dict,
				set,
				tuple,
			]
		)
		def test_should_return_false_for_builtin_types(self, builtin_type):
			# When
			result = is_custom_class(builtin_type)

			# Then
			assert result is False

		@pytest.mark.parametrize(
			'special_type',
			[
				Any,
				Optional,
				Union,
				List,
				Dict,
				Set,
				Tuple,
			]
		)
		def test_should_return_false_for_special_types(self, special_type):
			# When
			result = is_custom_class(special_type)

			# Then
			assert result is False

	class TestResolveDependency:

		def test_should_return_none_when_param_name_is_self(self):
			params = inspect.signature(B.__init__).parameters
			name, param = list(params.items())[0]

			# When
			result = resolve_dependency(B, name, param, {})

			# Then
			assert result is None

		def test_should_return_override_value_when_resolve_dependency_from_overrides_return_value(self):
			with patch('simple_dependency_resolver.main.resolve_dependency_from_overrides') as mock_resolve:
				# Given
				mock_resolve.return_value = 'override'
				params = inspect.signature(B.__init__).parameters
				name, param = list(params.items())[1]

				# When
				result = resolve_dependency(B, name, param, {})

				# Then
				assert result == 'override'

		def test_should_call_find_class_in_module_when_is_custom_class_string_annotation_return_true(self):
			with patch('simple_dependency_resolver.main.resolve_dependency_from_overrides') as mock_resolve:
				# Given
				mock_resolve.return_value = None
				with patch('simple_dependency_resolver.main.find_class_in_module') as mock_find:
					# Given
					params = inspect.signature(AWithStringAnnotation.__init__).parameters
					name, param = list(params.items())[1]

					# When
					resolve_dependency(AWithStringAnnotation, name, param, {})

					# Then
					mock_find.assert_called_once_with(AWithStringAnnotation, 'B')

		def test_should_call_instantiate_with_dependencies_when_is_custom_class_return_true(self):
			with patch('simple_dependency_resolver.main.resolve_dependency_from_overrides') as mock_resolve:
				# Given
				mock_resolve.return_value = None
				with patch(
						'simple_dependency_resolver.main.is_custom_class_string_annotation') as mock_is_custom_string_class:
					mock_is_custom_string_class.return_value = False
					with patch(
							'simple_dependency_resolver.main.instantiate_with_dependencies') as mock_instantiate:
						# Given
						params = inspect.signature(AWithDirectTypeAnnotation.__init__).parameters
						name, param = list(params.items())[1]

						# When
						resolve_dependency(AWithDirectTypeAnnotation, name, param, {})

						# Then
						mock_instantiate.assert_called_once_with(B, {})

		def test_should_return_default_value_when_param_default_is_not_param_empty(self):
			with patch('simple_dependency_resolver.main.resolve_dependency_from_overrides') as mock_resolve:
				# Given
				mock_resolve.return_value = None
				with patch(
						'simple_dependency_resolver.main.is_custom_class_string_annotation') as mock_is_custom_string_class:
					mock_is_custom_string_class.return_value = False
					with patch(
							'simple_dependency_resolver.main.is_custom_class') as mock_is_custom_class:
						mock_is_custom_class.return_value = False
						params = inspect.signature(B.__init__).parameters
						name, param = list(params.items())[2]

						# When
						result = resolve_dependency(B, name, param, {})

						# Then
						assert result == 'default message'

		def test_should_return_none_when_default_value_is_not_set(self):
			with patch('simple_dependency_resolver.main.resolve_dependency_from_overrides') as mock_resolve:
				# Given
				mock_resolve.return_value = None
				with patch(
						'simple_dependency_resolver.main.is_custom_class_string_annotation') as mock_is_custom_string_class:
					mock_is_custom_string_class.return_value = False
					with patch(
							'simple_dependency_resolver.main.is_custom_class') as mock_is_custom_class:
						mock_is_custom_class.return_value = False
						params = inspect.signature(B.__init__).parameters
						name, param = list(params.items())[0]

						# When
						result = resolve_dependency(B, name, param, {})

						# Then
						assert result is None

	class TestInstantiateWithDependencies:

		def test_should_return_instance_when_no_overrides(self):
			# When
			result = instantiate_with_dependencies(B)

			# Then
			assert isinstance(result, B)

		def test_should_return_instance_when_overrides_and_override_type(self):
			# Given
			overrides = {
				C: 'override'
			}

			# When
			result = instantiate_with_dependencies(B, overrides)

			# Then
			assert isinstance(result, B)
			assert result.c == 'override'

		def test_should_return_instance_when_overrides_and_override_name(self):
			# Given
			overrides = {
				'c': 'override'
			}

			# When
			result = instantiate_with_dependencies(B, overrides)

			# Then
			assert isinstance(result, B)
			assert result.c == 'override'

		def test_should_return_instance_when_overrides_and_override_name_and_override_type(self):
			# Given
			overrides = {
				'c': 'override',
				C: 'override2'
			}

			# When
			result = instantiate_with_dependencies(B, overrides)

			# Then
			assert isinstance(result, B)
			assert result.c == 'override'

		def test_should_throw_error_when_class_has_required_arguments(self):
			# Given
			class E:
				def __init__(self, a: int):
					self.a = a

			# When
			with pytest.raises(TypeError) as e:
				instantiate_with_dependencies(E)

			# Then
			assert str(
				e.value) == "TestInstantiateWithDependencies.TestInstantiateWithDependencies.test_should_throw_error_when_class_has_required_arguments.<locals>.E.__init__() missing 1 required positional argument: 'a'"

		def test_should_return_instance_when_no_dependencies(self):
			# When
			result = instantiate_with_dependencies(C)

			# Then
			assert isinstance(result, C)

		def test_should_return_instance_when_some_arguments_are_overridden(self):
			# Given
			class F:
				def __init__(self, a: int, b: str = "default"):
					self.a = a
					self.b = b

			overrides = {
				"a": 42
			}

			# When
			result = instantiate_with_dependencies(F, overrides)

			# Then
			assert isinstance(result, F)
			assert result.a == 42
			assert result.b == "default"

		def test_should_resolve_dependencies_across_multiple_levels(self):
			# Given
			class Inner:
				def __init__(self, x: int):
					self.x = x

			class Outer:
				def __init__(self, inner: Inner):
					self.inner = inner

			overrides = {
				"x": 100
			}

			# When
			result = instantiate_with_dependencies(Outer, overrides)

			# Then
			assert isinstance(result, Outer)
			assert isinstance(result.inner, Inner)
			assert result.inner.x == 100

		def test_should_resolve_default_none_values(self):
			# Given
			class G:
				def __init__(self, a: Optional[int] = None):
					self.a = a

			# When
			result = instantiate_with_dependencies(G)

			# Then
			assert isinstance(result, G)
			assert result.a is None

		def test_should_not_raise_error_for_invalid_override_type(self):
			"""
			Limitation of instantiating with kwargs, we can't check the type of the value
			"""

			# Given
			class H:
				def __init__(self, a: int):
					self.a = a

			overrides = {
				"a": "invalid"  # 非整数型
			}

			# When
			res = instantiate_with_dependencies(H, overrides)

			# Then
			assert isinstance(res, H)

		def test_should_handle_multiple_string_annotations(self):
			# Given
			class I:
				def __init__(self, b: "B", c: "C"):
					self.b = b
					self.c = c

			overrides = {
				"B": B(c=C()),
				"C": C()
			}

			# When
			result = instantiate_with_dependencies(I, overrides)

			# Then
			assert isinstance(result, I)
			assert isinstance(result.b, B)
			assert isinstance(result.c, C)

		def test_should_raise_error_for_circular_dependencies(self):
			# When
			with pytest.raises(RecursionError) as e:
				instantiate_with_dependencies(J)

			# Then
			assert "maximum recursion depth exceeded" in str(e.value)

		def test_should_return_override_for_special_type_specified_by_param_name(self):
			# Given
			class L:
				def __init__(self, a: Any):
					self.a = a

			overrides = {
				"a": "special_value"
			}

			# When
			result = instantiate_with_dependencies(L, overrides)

			# Then
			assert isinstance(result, L)
			assert result.a == "special_value"
