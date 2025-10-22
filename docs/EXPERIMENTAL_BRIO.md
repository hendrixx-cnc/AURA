# Experimental "Brio" Compressor

This module lives in `aura_compression.experimental.brio` and is *not*
referenced by the production compressor or streaming pipeline. It exists so we
can iterate on a Brotli-inspired stack without affecting shipping code.

Key stages:

1. **Static dictionary** – curated phrases common in AI conversations are
   replaced with compact tokens. Metadata annotates which dictionary entries
   fired so downstream AI can react without inflating the payload.
2. **LZ77 back-references** – a 32 KiB rolling window searches for matches of
   length ≥ 4. Tokens encode `(distance, length)` pairs while literals represent
   unmatched bytes.
3. **rANS entropy coding** – serialised tokens are passed through an order‑0
   rANS coder (scale 1 ≪ 12). Frequency tables are stored per payload to keep
   decoding stateless and deterministic.

## File layout

- `constants.py` – format/version constants.
- `dictionary.py` – dictionary entries and lookup helpers.
- `lz77.py` – naïve sliding-window matcher used for literal runs.
- `tokens.py` – token dataclasses shared by encoder/decoder.
- `encoder.py` – orchestrates dictionary matching, match detection and rANS.
- `decoder.py` – reverses the process and returns UTF‑8 text.
- `rans.py` – minimal rANS implementation (normalisation, encode, decode).

## Integration plan

- Keep prototypes behind `aura_compression.experimental`. No production import
  should reference these classes until we intentionally wire them up.
- Benchmark against the current Brotli stack using captured audit logs.
- Once ratios/latency are competitive, add a feature flag in the production
  compressor to experiment with opt‑in use.
- Ensure any future schema changes bump the version byte in the container so
  we can distinguish incompatible payloads.

## Risks and mitigations

- **Compression regressions** – dictionary/LZ tokens are only emitted when
  beneficial; otherwise literals preserve the original bytes. The metadata
  channel is tiny (five bytes per event) and optional for receivers.
- **Decoding errors** – container includes magic/version and per-payload
  frequency tables, avoiding cross-run state. Metadata is bundled alongside
  tokens so audit logs can always rebuild the original text.
- **Performance** – the current matcher is naïve; swap it for a hashed search
  or move the hot loops into Rust once the prototype’s ratios look promising.
