# Stable card references implementation plan

> Execute this focused plan in the existing isolated `codex/*` worktree. Keep
> source review before the final model regression.

**Goal:** References to the consumed execution card remain retrievable when its
title/state changes and the project advances to the next slice.

**Architecture:** Planning emits an actual stable heading for an embedded card.
Human title and current/closed state live in body fields. Implementation cites
the retained card using a Markdown link relative to the citing document.

**Spec:** The user's ongoing duplicate-record/stale-reference optimization and
the five unresolved card pointers recorded in [the previous results](EVIDENCE-HELPER-RESULTS.md).

**Stack:** Existing Markdown artifacts and reference verifier. No new runtime
dependency, file, verification command or history database.

## Constraints and review focus

- Control commit is `4f79ffe`; preserve `main`, release versions and tags.
- Existing project locations and stable file/heading identities take precedence.
- Preserve frozen cards and whole-file hash references byte for byte.
- A card version's heading identifies that version; changed execution content
  needs a new revision while the previous version remains retrievable. Later
  state for byte-frozen cards stays in an existing unfrozen record.
- Title/state changes must not silently turn a historical card into current
  authorization. Existing contract hashes, approvals and stage boundaries stay.
- Nested receipts use their own document-relative URLs. An inline-code logical
  identifier is not a mechanically verified navigation link.

## Task 1 — Fix the producer contract

Files are Plan `SKILL.md`, Plan `references/artifact-templates.md`, Implement
`SKILL.md`, and the affected forward evaluation cases.

- [x] Preserve the observed failing historical cases and start five fresh control
  two-slice developments with the original prompt and ordinary scoped tools.
- [x] Align the card template's actual heading with its stable-ID example. State
  closure/title changes separately and keep superseded versions retrievable.
- [x] Specify real document-relative card links at the implementation receipt.
- [x] Review this exact source delta before freezing the candidate.

## Task 2 — Verify behavior and cost

- [ ] Run five fresh candidate developments on identical frozen initial inputs.
  All five should retain the actual consumed cards and resolvable citations both
  when first saved and after S02. Score ID text and real links separately.
- [ ] Check product behavior, original RED/GREEN/regression, delivery examples,
  duplication, permissions, writes and whole-flow native usage independently.
  Do not infer total savings from shorter headings or fewer documents.
- [ ] Give the first three projects per arm to two fresh read-only recipients
  each, under the same control runtime. Preserve their natural artifacts.
- [ ] Check custom layouts and existing frozen/self-contained records in focused
  compatibility runs. New conventions must not authorize rewriting frozen inputs.
- [ ] Complete the exact-candidate standard regression with registered DeepSeek
  Flash and all required local checks. Keep scores and manual interpretation
  separate, preserve failed trials, and do not accept a new baseline.
- [ ] Keep, revise or drop the method according to observed card retrieval and
  obligations. Report actual costs and any unresolved regressions before the
  final development commit.

## Deferred from this batch

Five previous producers authored 17 manual verification-summary calls. An optional
compact verifier output may address that observed demand later. This batch does
not add that API or broaden verification to ambiguous bare card pointers.
