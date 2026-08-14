# Ponytail Setup Guide

> Load this only when setting up ponytail interop for the first time.

**Optional Enhancement**: [ponytail](https://github.com/DietrichGebert/ponytail) is an
AI-agent minimalism framework that climbs a decision ladder (YAGNI → reuse → stdlib →
platform → dependency → one-liner → minimum-that-works) before writing code.

> **Prerequisite:** This addon assumes ponytail is installed and active in this session. If
> `/ponytail` is not a recognized command, stop and install it first — see below.
> Without ponytail loaded, the precedence rules in `ponytail-workflow.md` govern nothing.

## Installing Ponytail

Install and configuration instructions live upstream and change independently of PDCA — see
[github.com/DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) for current
steps. Do not follow stale copy-pasted instructions from elsewhere; use the upstream README.

## Liveness Check

Confirm ponytail is actually loaded in this session before relying on the precedence rules:

```
/ponytail
```

If that is not a recognized command, ponytail is not active — install it first, or proceed
without this addon.

## Mode

Ponytail owns its own mode state; PDCA never sets or reads it on ponytail's behalf. Set mode
directly:

```
/ponytail lite|full|ultra|off
```

Mode can also default via `PONYTAIL_DEFAULT_MODE` or `~/.config/ponytail/config.json` — see
ponytail's own documentation. See `ponytail-workflow.md` for guidance on which mode to pick
per PDCA phase.

---

## License & Attribution

**License:** ponytail is MIT licensed, © DietrichGebert. This addon references ponytail's
behavior; it does not vendor or redistribute ponytail's code or install instructions.

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-agentic-coding-framework)
