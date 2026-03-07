# Python `itertools` — Main Function Groups

Fetched live from docs.python.org/3/library/itertools.html via Nimble.

---

## General Iterators

| Function | What it does |
|---|---|
| `accumulate(p [,func])` | Running totals: `[1,2,3,4,5] → 1 3 6 10 15` |
| `batched(p, n)` | Fixed-size chunks: `'ABCDEFG', 3 → ABC DEF G` |
| `chain(p, q, …)` | Concatenate iterables |
| `compress(data, selectors)` | Filter by boolean mask |
| `dropwhile(pred, p)` | Skip leading elements while predicate is true |
| `filterfalse(pred, p)` | Elements where predicate is False |
| `groupby(p [,key])` | Consecutive groups sharing the same key |
| `islice(p, stop)` | Iterator slice |
| `pairwise(p)` | Overlapping pairs: `'ABCDE' → AB BC CD DE` |
| `takewhile(pred, p)` | Take while predicate is true |
| `zip_longest(p, q, …)` | Zip with fill for unequal-length iterables |

## Infinite Iterators

| Function | What it does |
|---|---|
| `count(start [,step])` | `10 → 10 11 12 13 …` |
| `cycle(p)` | Loops indefinitely |
| `repeat(elem [,n])` | Repeat element n times (or forever) |

## Combinatoric Iterators

| Function | What it does |
|---|---|
| `product(p, q, …)` | Cartesian product |
| `permutations(p [,r])` | All r-length orderings |
| `combinations(p, r)` | r-length subsets, no repeats |
| `combinations_with_replacement(p, r)` | With repetition allowed |
