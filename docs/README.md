# Documents

This directory contains documents and generated assets used by Razavi Bench.

The two IEEE Solid-State Circuits Magazine articles in `papers/` are included with permission from Prof. Behzad Razavi. They are the source material for the benchmark questions and figures referenced by this repository.

These documents and derived benchmark materials are provided for public viewing,
citation, non-commercial research reference, and local evaluation from this
repository only. They may not be redistributed, rehosted, repackaged, or
incorporated into third-party benchmark or dataset releases without prior
written permission. See `../LICENSE` for details.

See `references.bib` for citation metadata.

## Website data

Current Direct QA data is published under `data/direct_qa/`:

- `index.json` contains the ranked model summaries and links to detail files.
- `models/<model_key>.json` contains three rollouts for one model, including the
  question, raw answer, both judge results, active score, and token usage.

`input_tokens` includes cached and cache-creation input tokens when the provider
reports them. `cached_input_tokens` is the cache-read subset. A `null` token value
with `complete: false` means that the historical provider response did not expose
that field; consumers must not interpret it as zero.
