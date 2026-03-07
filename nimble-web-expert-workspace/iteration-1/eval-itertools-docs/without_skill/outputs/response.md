# Python itertools — Main Groups

Here's a summary based on my training knowledge:

## Infinite Iterators
- `count(start, step)` — counts up from start
- `cycle(iterable)` — cycles through iterable forever
- `repeat(object, times)` — repeats object

## Finite Iterators
- `chain(*iterables)` — chains multiple iterables
- `islice(iterable, stop)` — slices an iterable
- `groupby(iterable, key)` — groups consecutive elements
- `filterfalse(predicate, iterable)`
- `dropwhile(predicate, iterable)`
- `takewhile(predicate, iterable)`
- `accumulate(iterable, func)`
- `compress(data, selectors)`
- `starmap(function, iterable)`
- `zip_longest(*iterables, fillvalue)`

## Combinatoric Iterators
- `product(*iterables, repeat)` — Cartesian product
- `permutations(iterable, r)` — all orderings
- `combinations(iterable, r)` — subsets without replacement
- `combinations_with_replacement(iterable, r)` — subsets with replacement

Note: This is from training data, not fetched live from docs.python.org.
