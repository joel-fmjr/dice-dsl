Árvore de derivação de `4d6 rr<3 kb3 ex` segundo `dice.lark` (usada por `dice_dsl.py`)

```mermaid
graph TD
    start --> expr["expr"]
    expr --> term["term"]
    term --> factor["factor"]
    factor --> roll["roll"]

    roll --> n4["4"]
    roll --> d["d"]
    roll --> n6["6"]
    roll --> mod1["modifier"]
    roll --> mod2["modifier"]
    roll --> mod3["modifier"]

    mod1 --> rr["rr"]
    mod1 --> comp["&lt;"]
    mod1 --> n3a["3"]

    mod2 --> kb["kb"]
    mod2 --> n3b["3"]

    mod3 --> ex["ex"]
```

Na gramática, `roll: NUMBER "d" NUMBER modifier*` é uma regra só, então os
modificadores são filhos diretos de `roll`, na ordem em que aparecem na string
(`rr`, `kb`, `ex`). A ordem de aplicação (`rr` → `min` → `kb`/`ks` → `ex`) é
definida em `run_single_roll`, não pela árvore.
