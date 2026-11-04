# Wafu

**Terms for wavefunctions. Hats for operators. Functions for the values you want to fill in later.**

Wafu is a small Python DSL for building wavefunctions as coefficient–eigenvalue terms, evaluating overlaps, composing tensor products, and expressing operator matrix elements. The notation keeps the mathematical structure visible without asking you to build a separate expression language just to describe a calculation.

[What it does](#what-it-does) · [Get started](#get-started) · [A quick example](#a-quick-example) · [How it fits together](#how-it-fits-together) · [Evaluate a wavefunction](#evaluate-a-wavefunction) · [Work with operators](#work-with-operators) · [Reference](#reference) · [Canonical style](#canonical-style) · [Implementation targets](#implementation-targets) · [Examples](#examples) · [Good to know](#good-to-know) · [Design notes](#design-notes)

## What it does

- Builds wavefunctions from pairs of **coefficients** and **eigenvalues**.
- Provides `ket()` and `bra()` constructors, with `*` and `@` for writing terms.
- Supports numeric values and callable functions as coefficients or eigenvalues.
- Binds function arguments by name and can report the parameter names a wavefunction needs.
- Conjugates wavefunctions with `~` and scales their coefficient sum with `%`.
- Evaluates inner products with `|`, matching terms by eigenvalue.
- Applies callable operators with the chained form `bra | operator | ket`.
- Builds pairwise tensor products with `&`, returning an `entangled` collection.
- Provides a `hat` namespace for the intended built-in operator vocabulary, plus `d` and `dd` namespaces for derivative targets.
- Exposes `h()` and `c()` constants in standard or natural-unit mode.

## Get started

Put `wafu.py` somewhere on your Python import path, then import the objects you need:

```python
from wafu import ket, bra, wavefunc, hat
```

Wafu uses the Python standard library and requires Python 3.10 or newer. A wavefunction is assembled one term at a time. Each term has this shape:

```python
state = ket() * 0.5 @ 2.0
```

The general pattern is `state * coefficient @ eigenvalue`. The `*` starts a term by supplying its coefficient. The `@` finishes that term by supplying its eigenvalue. Continue the same pattern to add more terms.

## A quick example

This example builds a three-term wavefunction, takes its complex conjugate, and inspects the resulting terms:

```python
from wafu import ket, wavefunc

psi: wavefunc = (
    ket()
    * 0.1 @ (3 - 4j)
    * 0.2 @ (3 + 2j)
    * 0.3 @ (1 + 3j)
)

psi = ~psi

assert psi[0] == (0.1, 3 + 4j)
assert psi[1][0] == 0.2
assert psi[2][1] == 1 - 3j

for coefficient, eigenvalue in psi:
    print(coefficient, eigenvalue)
```

The expression reads from left to right: add a coefficient, attach its eigenvalue, then begin the next term. Applying `~` conjugates both values in every term. The original wavefunction is left untouched; the conjugated wavefunction is returned as a new one.

## How it fits together

### Wavefunctions and terms

A `wavefunc` is an ordered collection of `(coefficient, eigenvalue)` pairs. `ket` and `bra` are convenient names for constructing one:

```python
from wafu import ket, bra

psi = (
    ket()
    * 0.4 @ (2 + 1j)
    * 0.2 @ (3 - 1j)
    * 0.3 @ (4 + 2j)
)
phi = (
    bra()
    * 0.7 @ (2 - 1j)
    * 0.1 @ (5 + 1j)
    * 0.2 @ (4 - 2j)
)
```

Each coefficient and eigenvalue may be an integer, a float, a complex number, or a callable that evaluates to a number. A term is complete once both values have been supplied.

> [!IMPORTANT]
> **`ket()` and `bra()` are constructor aliases in the current implementation.** They both create the same `wavefunc` type. `bra()` does not conjugate a state automatically; use `~psi` when you want the conjugated wavefunction.

A wavefunction can contain as many terms as the calculation needs. The order is preserved, so indexing and iteration follow the order in which the terms were added.

### Conjugation

Use `~` to conjugate the coefficient and eigenvalue of every term:

```python
bra_psi = ~psi
```

Numeric complex values are conjugated directly. Callable values are wrapped so that their returned values are conjugated when evaluated.

### Inspect and edit terms

A wavefunction supports the usual small-container operations:

```python
first = psi[0]       # one (coefficient, eigenvalue) pair
last = psi[-1]
window = psi[1:3]    # a list of pairs
count = len(psi)

for coefficient, eigenvalue in psi:
    print(coefficient, eigenvalue)
```

Replace a term by assigning a two-item tuple:

```python
psi[2] = (0.0, psi[2][1])
```

The coefficient and eigenvalue are validated when a term is assigned. The coefficient must be numeric or callable. The eigenvalue may also be `None` while a term is being assembled, or numeric/callable once complete.

> [!TIP]
> Use indexing when you need to inspect or adjust one term. Iteration is usually the cleanest way to process the whole wavefunction without relying on particular term positions.

## Evaluate a wavefunction

### Use ordinary values

Numbers can be supplied directly:

```python
psi = ket() * 0.1 @ (3 - 4j) * 0.2 @ (1 + 2j)
```

Coefficients and eigenvalues accept `int`, `float`, and `complex` values. Booleans are deliberately not treated as numbers here.

### Use functions as coefficients or eigenvalues

A callable can stand in for either value. Wafu inspects its parameter names and evaluates it when the wavefunction needs a numeric value:

```python
def coefficient(r, t):
    return r + 1j * t


def eigenvalue(x, y):
    return x * y

func: wavefunc = ket() * coefficient @ eigenvalue * 0.5 @ 2.0
```

The first term has a callable coefficient and callable eigenvalue. The second term is already numeric. This lets one expression keep both fixed and parameter-dependent terms together.

### Discover the required argument names

Call a wavefunction with `...` to inspect the parameter names collected from its callable terms:

```python
func(...)
# ('r', 't', 'x', 'y')
```

Names are reported once, in the order they are first encountered across the terms. The ellipsis form is for inspection; it does not evaluate the functions.

### Bind values by name

Supply arguments as keyword values:

```python
evaluated = func(r=1.0, t=2.0, x=3.0, y=4.0)
```

This returns a new wavefunction with those values bound. The stored expression remains available in `func`, so you can evaluate another copy with a different set of values:

```python
first_run = func(r=1.0, t=2.0, x=3.0, y=4.0)
second_run = func(r=2.0, t=1.0, x=5.0, y=6.0)
```

Bound arguments must be real numbers (`int` or `float`). The callable coefficient or eigenvalue must evaluate to a number (`int`, `float`, or `complex`). Functions with required parameters cannot be evaluated until all of their required names have values.

> [!CAUTION]
> **Argument binding is keyword-only.** Positional values such as `func(1, 2)` are not accepted. Use the parameter names: `func(r=1, t=2)`. The only supported positional call is `func(...)`, which inspects the names.

### Scale the coefficient sum

Use `% target` to scale all coefficients so their sum equals the supplied real target:

```python
normalized = psi % 1
```

The operation returns a new wavefunction and preserves the eigenvalues. It requires complete terms and evaluates callable coefficients using any values already bound to the wavefunction.

> [!NOTE]
> This operation normalizes the **sum of the coefficients**. It does not calculate an L2 norm or a sum of squared magnitudes. If the coefficient sum is zero, normalization is undefined and Wafu raises a `ValueError`.

## Work with operators

### Inner products

Use `|` between two wavefunctions to calculate their inner product:

```python
value = psi | phi
```

Wafu compares the evaluated eigenvalues of every term pair. Only pairs with equal eigenvalues contribute. Each contribution is the complex conjugate of the left coefficient multiplied by the right coefficient, and the contributions are added together. The result is a `complex` value.

This also supports the explicitly conjugated forms:

```python
value = psi | ~phi
value = ~psi | phi
value = ~psi | ~phi
```

The conjugation is performed by `~`; the inner-product operation conjugates the coefficient on its left-hand side as part of its calculation.

### Apply an operator

A callable operator is written between two wavefunctions:

```python
def operator(state: wavefunc) -> wavefunc:
    return state

matrix_element = psi | operator | phi
```

The operator receives the right-hand wavefunction (`phi`) and must return a `wavefunc`. Wafu then evaluates the inner product between the left-hand wavefunction (`psi`) and that result.

The callable can be a named function, a lambda, or another callable object:

```python
identity = lambda state: state
value = psi | identity | phi
```

> [!IMPORTANT]
> **A custom operator must return a `wavefunc`.** Returning a number, `None`, or another object is not an operator result Wafu can use in this expression.

Custom operators are already supported by the framework. They are the working route for operator behavior while the built-in operator targets are being implemented.

### Tensor products and entangled terms

Use `&` to form the tensor product of two wavefunctions:

```python
joint = psi & phi
```

Wafu combines every term on the left with every term on the right. Each resulting term contains the product of the two coefficients and a pair of eigenvalues:

```python
for coefficient, eigenvalues in joint:
    print(coefficient, eigenvalues)
```

The result is an `entangled` object. It supports indexing, slicing, iteration, `len()`, and string formatting, much like a compact collection of paired terms.

> [!NOTE]
> A tensor product returns `entangled`, not `wavefunc`. It represents paired terms; it is not interchangeable with a single wavefunction in an inner product or operator expression.

## Reference

### The expression operators

| Syntax | Meaning |
|---|---|
| `ket()` | Create an empty wavefunction. |
| `bra()` | Create an empty wavefunction; currently an alias of `ket()`. |
| `wavefunc * coefficient` | Start a new term with a coefficient. |
| `wavefunc @ eigenvalue` | Complete the most recently started term. |
| `~psi` | Return a conjugated wavefunction. |
| `psi % target` | Scale coefficients so their sum equals `target`. |
| `psi \| phi` | Calculate the inner product. |
| `psi \| operator \| phi` | Apply a callable operator to `phi`, then take the inner product with `psi`. |
| `psi & phi` | Build an `entangled` tensor product. |
| `func(...)` | Inspect callable parameter names. |
| `func(name=value, ...)` | Return a copy with real-valued arguments bound by name. |

### `wavefunc` and `entangled`

| Operation | Behavior |
|---|---|
| `len(state)` | Number of terms. |
| `state[index]` | One term as a `(coefficient, eigenvalue)` tuple. |
| `state[start:stop]` | A list containing the selected terms. |
| `state[index] = (coefficient, eigenvalue)` | Replace one term. |
| `for coefficient, eigenvalue in state` | Iterate over terms in insertion order. |

`wavefunc` validates the two values in an assigned term. `entangled` requires an assigned term to be a tuple containing exactly two values.

### Constants and units

The module provides two callable constants:

| Name | Standard mode | Natural mode |
|---|---:|---:|
| `h()` | `1.05457181e-34` | `1.0` |
| `c()` | `2.99792458e8` | `1.0` |

The default `unitmode` is `"standard"`. Set the module variable to `"natural"` to make both callables return `1.0`:

```python
import wafu

wafu.unitmode = "natural"
print(wafu.h(), wafu.c())
```

These are scalar values exposed by the module; changing `unitmode` does not perform automatic unit conversion elsewhere in an expression.

## Canonical style

The syntax allows a fair amount of freedom. A few conventions make a wavefunction easier to read and check.

### Keep one term on each line

Write each coefficient–eigenvalue pair on its own line, with the coefficient first:

```python
psi = (
    ket()
    * 0.1 @ (3 - 4j)
    * 0.2 @ (3 + 2j)
    * 0.3 @ (1 + 3j)
)
```

This makes it easier to compare terms and spot a missing eigenvalue.

### Finish a term before starting the next one

The intended rhythm is `* coefficient @ eigenvalue`. Do not add another coefficient while the previous term is still waiting for its eigenvalue.

### Name callable parts for their role

Prefer `coefficient`, `potential`, `energy`, or `eigenvalue` over anonymous one-letter names when a function is doing real work. The parameter names are also the names users must supply when binding values.

### Keep operator expressions readable

Use a named function for an operator once it contains more than a trivial expression:

```python
def transform(state: wavefunc) -> wavefunc:
    return state

result = psi | transform | phi
```

The chained expression is the calculation. The function is where the custom behavior belongs.

## Implementation targets

Wafu already has the interface for custom operators: a callable accepts a `wavefunc` and returns a `wavefunc`, and the expression `left | operator | right` uses it. The built-in namespaces describe the operator vocabulary intended for the project, but the current functions are not all implemented yet.

### Built-in operator targets

The `hat` namespace currently contains:

| Target | Intended role | Current state in `wafu.py` |
|---|---|---|
| `hat.nabla` | Nabla / gradient operator | Identity placeholder; returns its input unchanged. |
| `hat.p` | Momentum operator | Identity placeholder; returns its input unchanged. |
| `hat.x` | Position operator | Identity placeholder; returns its input unchanged. |
| `hat.t` | Time operator | Identity placeholder; returns its input unchanged. |
| `hat.I` | Identity operator | Returns its input unchanged. |
| `hat.T` | `T` operator | Identity placeholder; returns its input unchanged. |
| `hat.V` | Potential operator | Not implemented; currently returns `None`. |
| `hat.H` | Hamiltonian operator | Identity placeholder; returns its input unchanged. |
| `hat.Lx`, `hat.Ly`, `hat.Lz` | Angular-momentum components | Identity placeholders; return their input unchanged. |
| `hat.Sx`, `hat.Sy`, `hat.Sz` | Spin components | Identity placeholders; return their input unchanged. |
| `hat.laplacian` | Laplacian operator | Identity placeholder; returns its input unchanged. |

Use the namespace form in code, for example:

```python
chi = ket() * 0.6 @ (2 + 1j)

alpha = psi | hat.H | phi
beta = phi | hat.p | chi
gamma = psi | hat.T | chi
```

In the current source these names live under `hat`; bare module-level names such as `H`, `p`, and `T` are not defined.

> [!CAUTION]
> **The built-in names are not yet a promise of working physics.** Apart from acting as placeholders, the current methods do not implement the corresponding mathematical operators. In particular, `hat.H` currently behaves like the identity, and `hat.V` returns `None`. Do not use these placeholders as computed physical results.

### Derivative targets

The `d` and `dd` namespaces reserve names for first- and second-order derivatives:

| Namespace | Available targets |
|---|---|
| `d` | `dx`, `dy`, `dz`, `dt`, `dr` |
| `dd` | `dxx`, `dyy`, `dzz`, `dtt`, `drr`, `dxy`, `dyx`, `dyz`, `dzx`, `dzy` |

These methods are currently empty stubs. Their intended mathematical behavior and return values still need to be implemented. They are listed as the target surface, not as available derivative calculations.

### Bring your own operator

You do not need to wait for the built-in operators to implement a custom one. The callable interface is already available:

```python
from wafu import ket, wavefunc


def phase(state: wavefunc) -> wavefunc:
    result = ket()
    for coefficient, eigenvalue in state:
        result = result * (1j * coefficient) @ eigenvalue
    return result


psi = ket() * 1.0 @ 2.0
phi = ket() * 0.5 @ 2.0
value = psi | phase | phi
```

This example applies a phase factor to each numeric coefficient. It is deliberately small: custom operators can be as specific as the calculation requires, provided they return a valid `wavefunc`.

## Examples

### Compare two wavefunctions

```python
from wafu import ket

psi = ket() * 0.4 @ 1.0 * 0.6 @ 2.0
phi = ket() * 0.2 @ 1.0 * 0.8 @ 3.0

same = psi | phi
```

Only the terms with matching eigenvalues contribute to the result.

### Bind a parameterized wavefunction

```python
from wafu import ket, wavefunc


def amplitude(a, b):
    return a + 1j * b


def energy(momentum):
    return momentum ** 2

state: wavefunc = ket() * amplitude @ energy

print(state(...))
# ('a', 'b', 'momentum')

resolved = state(a=0.5, b=0.25, momentum=3.0)
```

The function signatures tell Wafu which names to request. The values are supplied when the expression is evaluated.

### Form an entangled pair

```python
from wafu import ket

left = ket() * 0.5 @ 1 * 0.5 @ 2
right = ket() * 0.2 @ 3 * 0.8 @ 4

pair = left & right
print(len(pair))  # 4 pairwise combinations
```

Every left term is paired with every right term, so the resulting collection contains the Cartesian product of the two term lists.

## Good to know

> [!NOTE]
> A term is not complete until it has both a coefficient and an eigenvalue. Operations that evaluate a wavefunction, such as inner products, tensor products, and coefficient-sum normalization, require complete terms.

- `ket` and `bra` currently refer to the same constructor; conjugation is explicit with `~`.
- Coefficients and eigenvalues may be numbers or callables. Evaluated results must be numeric.
- Values passed to `func(name=value)` must be real numbers; complex values are allowed as callable results and as direct coefficients/eigenvalues.
- Callable arguments are bound by keyword, not position.
- `func(...)` reports parameter names; it does not evaluate the wavefunction.
- `%` scales the coefficient sum, not the sum of squared magnitudes.
- `|` matches terms by equality of their evaluated eigenvalues.
- `&` returns an `entangled` collection, not a `wavefunc`.
- A custom operator must accept one wavefunction and return one wavefunction.
- `hat` methods, `d`, and `dd` include unfinished implementation targets. Check their status before using them in a calculation.
- `h()` and `c()` read the module-level `unitmode` each time they are called.

## Design notes

Wafu keeps the expression close to the mathematical objects it is meant to describe. A wavefunction is a list of coefficient–eigenvalue terms. `*` and `@` make those terms readable in sequence. `~`, `%`, `|`, and `&` express the common transformations and combinations without hiding them behind a collection of helper calls.

Callable coefficients and eigenvalues keep parameterized expressions in the same form as fixed ones. The operator interface is intentionally open: built-in hats can grow into the project's standard operators, while custom callables can already provide application-specific behavior.

The aim is a compact notation that shows the calculation at the point where you write it. Keep the terms visible, keep the operators explicit, and leave the implementation details where they belong.
