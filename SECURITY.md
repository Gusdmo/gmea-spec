# Security Policy

Treat .gmea files as untrusted SQLite-contained archives unless they are from a trusted source and pass validation.

Readers should open read-only where possible, avoid executing archive-provided SQL, disable extension loading, validate known tables directly, and enforce size/row-count limits where appropriate.
