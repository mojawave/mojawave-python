# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0]

- `sms.send` sends an `Idempotency-Key` (yours via `idempotency_key`, or generated), so the SDK's automatic retries never send or charge a message twice.
- `sender` is optional: when omitted `from` is left out and your account's default sender is used.
- `status` may be `queued` (queue-first sending) or `scheduled`.
- New `client.reseller` for reseller partners: `customers`, `create_customer`, `set_prices`, `transfer`, `usage`, `commissions`.
- **Requires the MojaWave backend that accepts a missing `from` (deploy the backend first).**


## [1.0.1] - 2026-09-02

### Fixed
- `verify_signature`/`construct_event` compared the raw `X-MojaWave-Signature` header
  directly against the computed hex digest, never stripping the header's `sha256=`
  prefix — every legitimate signature failed verification. Fixed and added a
  regression test that signs with the real prefixed header format.

## [1.0.0] - Initial release
