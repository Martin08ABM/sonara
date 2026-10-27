# ADR-001: Apache License 2.0

**Status: Accepted** — decision made by the project owner in SPEC-002.

## Context

Sonara needs an explicit open source license for its own code before distribution. The bootstrap deferred the choice.

## Decision

Distribute Sonara's own code under the unmodified Apache License 2.0. Use the SPDX identifier `Apache-2.0` in package metadata. Third-party components, model weights and datasets retain their own licenses.

## Reasons and alternatives

The owner selected Apache 2.0 for its permissive reuse terms, explicit patent grant and contribution terms. MIT is a shorter permissive alternative; GPLv3 is a copyleft alternative. Neither was selected.

## Consequences

Distributors and contributors must comply with the license's conditions, including applicable notice and attribution obligations. Review third-party licenses before inclusion or redistribution. No third-party code or assets are bundled by this decision; no attribution NOTICE is presently required. Future distribution may require additional notices.
