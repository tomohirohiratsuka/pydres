import builtins

SPECIAL_TYPES = {
	"Any",
	"Union",
	"TypeVar",
	"Callable",
	"Optional",
	"Literal",
	"Final",
	"ClassVar",
	"Protocol",
	"List",
	"Dict",
	"Set",
	"Tuple"
}

BUILTIN_TYPES = {type_.__name__ for type_ in vars(builtins).values() if isinstance(type_, type)}