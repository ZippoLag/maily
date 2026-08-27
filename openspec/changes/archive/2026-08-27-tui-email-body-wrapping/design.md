## Context

See proposal.md — Why. `_add_email_node` currently adds the body as a Tree node label after flattening newlines and truncating to 1000 chars. Textual's `Tree` is single-line per node (flat `_tree_lines`, no wrapping), so the body can never wrap inside the tree. The fix renders the body in a separate wrap-enabled widget.

## Goals / Non-Goals

- **Goals**: Wrap expanded email bodies to the available terminal width; preserve paragraph structure; reflow on resize; scroll long bodies. Keep tree navigation untouched.
- **Non-Goals**: No changes to scan, classification, config, or CLI output. No hard-wrapping of stored bodies (soft-wrap for display only). No Gmail mutations.

## Decisions

- **Render the body in a `Static` reading pane below the tree**: Textual `Static` widgets wrap long text to their width by default and re-render on resize, giving free reflow. The tree stays the navigation surface. Layout: a `Vertical` container holding the `CategoryTree` and the pane, or a pane mounted below the tree with a fixed/`fr` height split. Alternative considered — pre-wrapping the body into multiple dimmed tree child rows — was rejected: every wrapped line becomes a focusable tree row (keyboard navigation noise) and it cannot reflow dynamically on resize.
- **Preserve stored newlines instead of flattening**: `body.replace('\n', ' ')` is removed. Paragraph breaks render as blank lines; long lines wrap at the pane width. A small pure helper (e.g., `pane_text_for_email(item, width)`) composes sender/subject/body text so the wrapping contract is unit-testable without launching the app.
- **Drop the 1000-char truncation**: it was a display hack for the single-line tree row; the scrolling pane removes the need. Long bodies scroll instead of being cut off.
- **Keyboard/scroll**: pane scrolls via standard Textual scrolling (arrow keys / PageUp / PageDown) while the tree keeps cursor navigation. Textual's `Static` participates in focus/scroll natively.
- **Alternative considered — `Markdown` widget**: renders wrapped text but reinterprets raw email bodies as Markdown, which can mangle plain text (links, emphasis, code spans). `Static` with plain text is predictable and sufficient.

## Risks / Trade-offs

- [Pane consumes vertical space, shrinking the tree] → mitigated by a height split with the pane sized proportionally (e.g., `fr(1)`/`fr(2)`); collapse or dismiss not required by scope.
- [Very long single-line bodies] → Textual wraps long words at the width; acceptable worst case is an over-wide word clipped or wrapped mid-word, matching standard terminal behavior.
- [Resize during active scroll] → reflow keeps scroll offset anchored at the top of the visible region; acceptable for v1.
