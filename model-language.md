# Declared model language

A model is a JSON object with `dimension`, `min_entropy`, optional `prior`, and a finite `root` node. Vectors and matrix rows are nonnegative integer bit masks: bit `j` is latent coordinate `j`. The language deliberately omits affine offsets because a public offset can be added to each candidate without changing a Hamming-distance test.

Node forms are:

```json
{"type":"stop"}
```

```json
{"type":"epoch","rows":[1,2],"radius":0,"guesses":1,"next":{...}}
```

```json
{"type":"observe","rows":[1],"eta":"1/4","children":[{...},{...}]}
```

An epoch fixes one response map, one Hamming radius, and a bounded number of adaptive guesses. It reveals only accept/reject and reaches `next` only after every guess is rejected. An observation applies independent BSC errors with the declared exact rational crossover to its listed rows. Child index is the little-endian output mask in row order. Unknown keys, malformed probabilities, inconsistent child counts, out-of-range rows, and unsupported sizes are errors; they never fall back to another channel.

The checker permits `dimension <= 256`, at most 256 syntax nodes, depth at most 32, at most four observation rows, at most 256 epoch rows, and at most 64 guesses. The exact posterior oracle is intentionally narrower: `dimension <= 6`, at most four response rows, and at most four guesses. The refined certificate has explicit state and transition guards.

`min_entropy = k` invokes only the one-time factor `2^(dimension-k)` proved in the artifact. An explicit prior is accepted only when its entries are exact nonnegative rationals summing to one and every point mass is at most `2^-k`. The certificate does not infer entropy, independence, physical reliability, or model conformance from data.
