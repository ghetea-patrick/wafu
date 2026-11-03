from __future__      import annotations

from collections.abc import Callable, Iterator
from dataclasses     import dataclass
from inspect         import Parameter, signature
from typing          import Any

No = int | float | complex
Re = int | float

Operator = Callable[["wavefunc"], "wavefunc"]

_GATTR_QUAL: str = "__qualname__"
_GATTR_NAME: str = "__name__"
_GATTR_FUNC: str = "func"
_GATTR_CONJ: str = "conjugate"

_CONST_LAMD: str = "lambda"
_CONST_LARE: str = "<lambda>"


@dataclass
class errorstring:
    @staticmethod
    def middleman_operand(other: Any) -> TypeError:
        return TypeError(f"An operator can only be applied to a wavefunc, not {type(other).__name__}.")

    @staticmethod
    def middleman_result(operator: Callable[..., Any], result: Any) -> TypeError:
        name = _funcname(operator)
        return TypeError(f"Operator '{name}' returned {type(result).__name__}; it needs to return a wavefunc.")

    @staticmethod
    def entangled_pair_type(value: Any) -> TypeError:
        return TypeError(f"An entangled term needs a pair, not {type(value).__name__}; use (coefficient, eigenvalue).")

    @staticmethod
    def entangled_pair_size(value: Any) -> ValueError:
        return ValueError(f"An entangled term needs exactly two values, but this one has {len(value)}.")

    @staticmethod
    def wavefunc_pair_type(value: Any) -> TypeError:
        return TypeError(f"A wavefunc term needs a pair, not {type(value).__name__}; use (coefficient, eigenvalue).")

    @staticmethod
    def wavefunc_pair_size(value: Any) -> ValueError:
        return ValueError(f"A wavefunc term needs exactly two values, but this one has {len(value)}.")

    @staticmethod
    def coefficient_type(value: Any) -> TypeError:
        return TypeError(f"A coefficient needs to be a number or a callable, not {type(value).__name__}.")

    @staticmethod
    def eigenvalue_type(value: Any) -> TypeError:
        return TypeError(f"An eigenvalue needs to be a number or a callable, not {type(value).__name__}.")

    @staticmethod
    def inspect_callable(function: Callable[..., Any]) -> TypeError:
        name = _funcname(function)
        return TypeError(f"Can't inspect '{name}' to evaluate it from named values.")

    @staticmethod
    def missing_values(function: Callable[..., Any], missing: list[str]) -> TypeError:
        name = _funcname(function)
        names = ", ".join(f"'{parameter}'" for parameter in missing)
        return TypeError(f"Can't evaluate '{name}' yet; you're still missing values for {names}.")

    @staticmethod
    def evaluated_coefficient(coefficient: Any, value: Any) -> TypeError:
        name = _funcname(coefficient) if callable(coefficient) else "coefficient"
        return TypeError(f"Coefficient '{name}' needs to evaluate to a number, not {type(value).__name__}.")

    @staticmethod
    def evaluated_eigenvalue(eigenvalue: Any, value: Any) -> TypeError:
        name = _funcname(eigenvalue) if callable(eigenvalue) else "eigenvalue"
        return TypeError(f"Eigenvalue '{name}' needs to evaluate to a number, not {type(value).__name__}.")

    @staticmethod
    def incomplete_terms() -> ValueError:
        return ValueError("Finish every term with '@ eigenvalue' before evaluating this wavefunc.")

    @staticmethod
    def call_arguments() -> TypeError:
        return TypeError("Bind values by name, or use func(...) to inspect its parameter names.")

    @staticmethod
    def call_value(name: str, value: Any) -> TypeError:
        return TypeError(f"'{name}' needs to be a real number, not {type(value).__name__}.")

    @staticmethod
    def normalization_target(value: Any) -> TypeError:
        return TypeError(f"The normalization target needs to be a real number, not {type(value).__name__}.")

    @staticmethod
    def normalization_zero() -> ValueError:
        return ValueError("Can't normalize this wavefunc because its coefficient sum is zero.")

    @staticmethod
    def unfinished_term() -> ValueError:
        return ValueError("Finish the previous term with '@ eigenvalue' before adding another coefficient.")

    @staticmethod
    def missing_coefficient() -> ValueError:
        return ValueError("Add a coefficient with '*' before assigning an eigenvalue with '@'.")

    @staticmethod
    def existing_eigenvalue() -> ValueError:
        return ValueError("This term already has an eigenvalue. Add another coefficient with '*' before using '@' again.")

    @staticmethod
    def inner_product_operand(other: Any) -> TypeError:
        return TypeError(f"An inner product needs another wavefunc or a callable operator, not {type(other).__name__}.")

    @staticmethod
    def tensor_product_operand(other: Any) -> TypeError:
        return TypeError(f"A tensor product needs another wavefunc, not {type(other).__name__}.")


def _conjugat(value: Any) -> Any:
    conjugate = getattr(value, _GATTR_CONJ, None)
    if callable(conjugate):
        return conjugate()
    else:
        return value


def _funcname(function: Callable[..., Any]) -> str:
    partial = getattr(function, _GATTR_FUNC, None)
    if callable(partial):
        return _funcname(partial)

    nameone = getattr(function, _GATTR_QUAL, None)
    nametwo = getattr(function, _GATTR_NAME, None)
    if name := nameone or nametwo:
        return _CONST_LAMD if name == _CONST_LARE else name
    return type(function).__name__


def _wrapfunc(
        function: Callable[..., Any],
        wrapfunc: Callable[[Any], Any],
) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return wrapfunc(function(*args, **kwargs))

    funcname = _funcname(function)
    wrapper.__name__     = funcname
    wrapper.__qualname__ = funcname
    wrapper.__wrapped__  = function
    return wrapper


class _middleman:
    def __init__(
            self,
            function: wavefunc,
            operator: Operator,
    ) -> None:
        self.function = function
        self.operator = operator
        self.opername = _funcname(operator)

    def __or__(self, other: wavefunc) -> complex:
        if not isinstance(other, wavefunc):
            raise errorstring.middleman_operand(other)

        result = self.operator(other)
        if not isinstance(result, wavefunc):
            raise errorstring.middleman_result(self.operator, result)

        return self.function | result

    def __str__(self) -> str:
        return f"{self.opername}({self.function})"

    def __repr__(self) -> str:
        return str(self)


class entangled:
    def __init__(
            self,
            term: None | list[tuple[Any, Any]] = None,
    ) -> None:
        self.term = [] if term is None else list(term)

    def __getitem__(
            self,
            index: int | slice,
    ) -> tuple[Any, Any] | list[tuple[Any, Any]]:
        return self.term[index]

    def __setitem__(
            self,
            index: int,
            value: tuple[Any, Any],
    ) -> None:
        if not isinstance(value, tuple):
            raise errorstring.entangled_pair_type(value)
        if len(value) != 2:
            raise errorstring.entangled_pair_size(value)
        self.term[index] = value

    def __iter__(self) -> Iterator[tuple[Any, Any]]:
        return iter(self.term)

    def __len__(self) -> int:
        return len(self.term)

    def __str__(self) -> str:
        if not self.term:
            return "entangled()"
        return " * ".join(f"{coefficient} @ {eigenvalue}" for coefficient, eigenvalue in self.term)

    def __repr__(self) -> str:
        return str(self)


class wavefunc:
    def __init__(
            self,
            term: None | list[tuple[Any, Any]] = None,
            vals: None | dict[str, float]      = None,
            mode: None | tuple[bool, bool]     = None,
    ) -> None:
        self.term = [] if term is None else list(term)
        self.vals = {} if vals is None else dict(vals)
        self.mode = mode
        self.name = self._names()

    def __getitem__(
            self,
            index: int | slice,
    ) -> tuple[Any, Any] | list[tuple[Any, Any]]:
        return self.term[index]

    def __setitem__(
            self,
            index: int,
            value: tuple[Any, Any]
    ) -> None:
        if not isinstance(value, tuple):
            raise errorstring.wavefunc_pair_type(value)
        if len(value) != 2:
            raise errorstring.wavefunc_pair_size(value)

        coefficient, eigenvalue = value
        if isinstance(coefficient, bool) or (not callable(coefficient) and not isinstance(coefficient, No)):
            raise errorstring.coefficient_type(coefficient)

        if eigenvalue is not None and isinstance(eigenvalue, bool):
            raise errorstring.eigenvalue_type(eigenvalue)
        if eigenvalue is not None and not callable(eigenvalue) and not isinstance(eigenvalue, No):
            raise errorstring.eigenvalue_type(eigenvalue)

        self.term[index] = value
        self.name = self._names()

    def __iter__(self) -> Iterator[tuple[Any, Any]]:
        return iter(self.term)

    def __len__(self) -> int:
        return len(self.term)

    def __str__(self) -> str:
        if not self.term:
            return "wavefunc()"

        terms = []
        for coefficient, eigenvalue in self.term:
            try:
                coefficient_value = self._evals(coefficient)
            except Exception:
                coefficient_value = _funcname(coefficient) if callable(coefficient) else coefficient
            try:
                eigenvalue_value = self._evals(eigenvalue)
            except Exception:
                eigenvalue_value = _funcname(eigenvalue) if callable(eigenvalue) else eigenvalue
            terms.append(f"{coefficient_value} @ {eigenvalue_value}")

        return " * ".join(terms)

    def __repr__(self) -> str:
        return str(self)

    def _clone(
            self,
            term: None | list[tuple[Any, Any]] = None,
            vals: None | dict[str, float]      = None,
    ) -> wavefunc:
        termnew = self.term if term is None else list(term)
        valsnew = self.vals if vals is None else dict(vals)
        return wavefunc(termnew, valsnew, self.mode)

    def _names(self) -> tuple[str, ...]:
        found = set()
        names = []

        for coefficient, eigenvalue in self.term:
            for value in (coefficient, eigenvalue):
                if not callable(value):
                    continue

                try:
                    parameters = signature(value).parameters.values()
                except (TypeError, ValueError):
                    continue

                for parameter in parameters:
                    if parameter.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                        continue
                    if parameter.name in found:
                        continue
                    names.append(parameter.name)
                    found.add(parameter.name)

        return tuple(names)

    def _evals(self, value: Any) -> Any:
        if not callable(value):
            return value

        try:
            parameters = signature(value).parameters.values()
        except (TypeError, ValueError) as e:
            raise errorstring.inspect_callable(value) from e

        keyword : dict[str, Any] = {}
        posword : list[Any]      = []
        missing : list[str]      = []
        explicit: set[str]       = set()
        morekeys: bool           = False

        for parameter in parameters:
            if parameter.kind is Parameter.VAR_POSITIONAL:
                continue
            if parameter.kind is Parameter.VAR_KEYWORD:
                morekeys = True
                continue

            explicit.add(parameter.name)

            if parameter.name in self.vals:
                if parameter.kind is Parameter.POSITIONAL_ONLY:
                    posword.append(self.vals[parameter.name])
                else:
                    keyword[parameter.name] = self.vals[parameter.name]
                continue

            if parameter.default is not Parameter.empty:
                if parameter.kind is Parameter.POSITIONAL_ONLY:
                    posword.append(parameter.default)
                continue

            missing.append(parameter.name)

        if missing:
            raise errorstring.missing_values(value, missing)

        if morekeys:
            for parameter, argument in self.vals.items():
                if parameter not in explicit:
                    keyword.setdefault(parameter, argument)

        result = value(*posword, **keyword)
        if isinstance(result, bool):
            return result
        if isinstance(result, Re):
            return float(result)
        return result

    def _coeff(self, coefficient: Any) -> No:
        value = self._evals(coefficient)
        if isinstance(value, bool) or not isinstance(value, No):
            raise errorstring.evaluated_coefficient(coefficient, value)
        return value

    def _eigen(self, eigenvalue: Any) -> No:
        value = self._evals(eigenvalue)
        if isinstance(value, bool) or not isinstance(value, No):
            raise errorstring.evaluated_eigenvalue(eigenvalue, value)
        return value

    def _twins(self) -> None:
        if any(eigenvalue is None for _, eigenvalue in self.term):
            raise errorstring.incomplete_terms()

    def __call__(
            self,
            *args   : Any,
            **kwargs: Any
    ) -> wavefunc | tuple[str, ...]:
        if args:
            if len(args) == 1 and args[0] is ... and not kwargs:
                return self._names()
            raise errorstring.call_arguments()

        for name, value in kwargs.items():
            if isinstance(value, bool) or not isinstance(value, Re):
                raise errorstring.call_value(name, value)

        values = self.vals | {name: float(value) for name, value in kwargs.items()}
        return self._clone(self.term, values)

    def __mod__(self, other: Re) -> wavefunc:
        if isinstance(other, bool) or not isinstance(other, Re):
            raise errorstring.normalization_target(other)
        self._twins()

        total = sum((self._coeff(coefficient) for coefficient, _ in self.term), 0.0)
        if total == 0:
            raise errorstring.normalization_zero()

        scale = other / total
        terms = []
        for coefficient, eigenvalue in self.term:
            if callable(coefficient):
                normalized = _wrapfunc(coefficient, lambda value, scale=scale: value * scale)
            else:
                normalized = coefficient * scale
            terms.append((normalized, eigenvalue))

        return self._clone(terms)

    def __mul__(self, other: Any) -> wavefunc:
        if isinstance(other, bool) or (not callable(other) and not isinstance(other, No)):
            raise errorstring.coefficient_type(other)
        if self.term and self.term[-1][1] is None:
            raise errorstring.unfinished_term()

        self.term.append((other, None))
        iscallable = callable(other)
        self.mode  = (self.mode[0], iscallable) if self.mode is not None else (iscallable, False)
        self.name  = self._names()
        return self

    def __matmul__(self, other: Any) -> wavefunc:
        if not self.term:
            raise errorstring.missing_coefficient()
        if self.term[-1][1] is not None:
            raise errorstring.existing_eigenvalue()

        if not callable(other):
            if isinstance(other, bool) or not isinstance(other, No):
                raise errorstring.eigenvalue_type(other)

        coefficient   = self.term[-1][0]
        self.term[-1] = (coefficient, other)
        if self.mode is None:
            self.mode = (callable(coefficient), callable(other))
        self.name = self._names()
        return self

    def __invert__(self) -> wavefunc:
        def conjugate(value: Any) -> Any:
            if callable(value):
                return _wrapfunc(value, _conjugat)
            return _conjugat(value)

        terms = [(conjugate(coefficient), conjugate(eigenvalue)) for coefficient, eigenvalue in self.term]
        return self._clone(terms)

    def __or__(
            self,
            other: wavefunc | Operator,
    ) -> complex | _middleman:
        if isinstance(other, wavefunc):
            self._twins()
            other._twins()
            result = 0j

            for coeffone, eigenone in self.term:
                eigenvalue_one = self._eigen(eigenone)
                for coefftwo, eigentwo in other.term:
                    if eigenvalue_one == other._eigen(eigentwo):
                        valone = complex(_conjugat(self._coeff(coeffone)))
                        valtwo = complex(other._coeff(coefftwo))
                        result += valone * valtwo
            return result

        if callable(other):
            return _middleman(self, other)

        raise errorstring.inner_product_operand(other)

    def __and__(self, other: wavefunc) -> entangled:
        if not isinstance(other, wavefunc):
            raise errorstring.tensor_product_operand(other)
        self._twins()
        other._twins()

        terms = []
        for coeffone, eigenone in self.term:
            for coefftwo, eigentwo in other.term:
                coefficient = self._coeff(coeffone) * other._coeff(coefftwo)
                eigenvalue = (self._eigen(eigenone), other._eigen(eigentwo))
                terms.append((coefficient, eigenvalue))

        return entangled(terms)


ket = wavefunc
bra = wavefunc

unitmode: str = "standard"

h: Callable[[], float] = lambda: 1.0 if unitmode == "natural" else 1.05457181e-34
c: Callable[[], float] = lambda: 1.0 if unitmode == "natural" else 2.99792458e8


class d:
    @staticmethod
    def dx() -> ...:
        ...
    @staticmethod
    def dy() -> ...:
        ...
    @staticmethod
    def dz() -> ...:
        ...
    @staticmethod
    def dt() -> ...:
        ...
    @staticmethod
    def dr() -> ...:
        ...


class dd:
    @staticmethod
    def dxx() -> ...:
        ...

    @staticmethod
    def dyy() -> ...:
        ...

    @staticmethod
    def dzz() -> ...:
        ...

    @staticmethod
    def dtt() -> ...:
        ...

    @staticmethod
    def drr() -> ...:
        ...

    @staticmethod
    def dxy() -> ...:
        ...

    @staticmethod
    def dyx() -> ...:
        ...

    @staticmethod
    def dyz() -> ...:
        ...

    @staticmethod
    def dzx() -> ...:
        ...

    @staticmethod
    def dzy() -> ...:
        ...


class hat:
    @staticmethod
    def nabla(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def p(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def x(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def t(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def I(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def T(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def V(psi: wavefunc) -> wavefunc:
        ...

    @staticmethod
    def H(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Lx(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Ly(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Lz(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Sx(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Sy(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def Sz(psi: wavefunc) -> wavefunc:
        return psi

    @staticmethod
    def laplacian(psi: wavefunc) -> wavefunc:
        return psi
