# PACTUM

**Pactum · 契印**

> English | [简体中文](README.zh-CN.md)

An unofficial desktop companion for **Hunt: Showdown 1896**.

Pactum is a community-built, Windows-first application for map awareness,
points of interest, reference information, and focused utilities that support
the hunt without modifying the game. The project is being rebuilt from the
ground up with Tauri.

The name reflects the contracts, pacts, marks, and consequences at the heart
of every hunt. **Pactum** is the product name; **PACTUM** is its visual wordmark;
**契印** is its Chinese name.

## Project Status

Pactum is currently at the beginning of its Tauri rewrite. The active branches
have intentionally been reduced to a clean foundation, and production
application code has not been added yet.

The earlier Tauri proof of concept established that the Windows overlay approach
is technically viable. The production implementation will now be designed as
Pactum rather than carried forward as a renamed prototype.

## Direction

Pactum is intended to grow as a coherent companion rather than a collection of
unrelated tools. Its initial direction includes:

- Windows overlay and map-related assistance
- Official and custom point-of-interest workflows
- Hunt reference information presented alongside practical utilities
- Local-first settings and user data
- A modular foundation for carefully selected future features

The implementation will be based on Tauri, with Rust handling native desktop
responsibilities and a focused web frontend providing the interface.

## Principles

- **Windows first:** runtime behavior is designed and validated on Windows.
- **Non-invasive:** Pactum must not modify game files, inject into the game
  process, or read or alter game memory.
- **Local first:** settings and personal data should remain under the user's
  control.
- **Purposeful scope:** new features should strengthen the companion experience
  instead of turning the application into an unfocused toolbox.
- **Community built:** the project is unofficial and developed independently of
  Crytek.

## Branches

| Branch | Purpose |
| --- | --- |
| `dev` | Primary development branch for the new Tauri application |
| `main` | Stable integration branch, updated from `dev` |
| `legacy` | Archived PySide6 implementation preserved at commit `93b9035` |

## Disclaimer

Pactum is an unofficial community project and is not affiliated with, endorsed
by, or sponsored by Crytek. Hunt: Showdown 1896 and related names and assets are
the property of their respective owners.

Use Pactum at your own risk and always comply with the game's applicable terms
and policies.

## Heritage and Credits

Pactum is the clean successor to the HuntOverlay project maintained in this
repository. Its archived implementation was originally derived from
[HuntOverlay-by-sKhaled](https://github.com/uzpj/HuntOverlay-by-sKhaled).

- Original overlay implementation: sKhaled
- Community POI data: Kamille and the Hunt community
