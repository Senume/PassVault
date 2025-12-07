# Threat model (concise)

Primary assumptions
- The application runs on a single-user Linux machine.
- Vault files are stored in the user's home directory and are only accessible to that user (file perms 0600).
- No network access is required for vault operations; backups are encrypted blobs.

Adversaries
- Local attacker with user-level access should not be able to decrypt vault without master password.
- Physical access to the machine: if attacker can read memory or cold-boot attack, secrets may be at risk.
- Remote attackers are out of scope for the offline-only initial design.

Protections
- Argon2id for KDF to slow brute-force.
- AEAD (AES-GCM) for encryption to provide confidentiality and authenticity.
- File permission hardening and atomic writes.
- Optional ephemeral caching in Secret Service is out-of-scope unless enabled by the user.

Notes
- Consider moving crypto-critical parts to Rust for extra memory-safety in later versions.
