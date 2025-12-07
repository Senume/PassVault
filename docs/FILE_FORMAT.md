# Vault file format (v1)

We use a simple JSON-based envelope for ease of prototyping. All binary blobs are base64-encoded.

Schema (JSON):

{
  "version": 1,
  "kdf": {"time": <int>, "memory": <int>, "parallelism": <int>},
  "salt": "<base64>",
  "nonce": "<base64>",
  "ciphertext": "<base64>"
}

- `salt`: 16 random bytes used for Argon2id.
- `nonce`: 12 bytes (for AES-GCM) used for encryption.
- `ciphertext`: the AEAD output (ciphertext + tag as produced by the underlying library).

Rationale: JSON envelope is simple and easy to inspect (for debugging) while keeping secrets encrypted. On export/import the whole file can be copied safely.
