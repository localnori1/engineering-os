# UI implementation

1. Confirm the user outcome, information hierarchy, primary/secondary actions,
   permissions, state transitions, and acceptance criteria.
2. Inspect the rendered existing flow plus canonical tokens, primitives, and
   similar interactions. Reuse or compose them before adding a variant.
3. Choose the smallest coherent surface: existing page, inline interaction,
   modal, drawer, popover, or new route. Do not create a screen by habit.
4. Implement relevant loading, empty, error, partial, disabled, success,
   destructive, interruption, cancellation, and recovery states.
5. Preserve semantics, labels, focus order/visibility/trapping/return, keyboard
   behavior, announcements, contrast, reduced motion, zoom/reflow, localization,
   touch targets, and supported viewport behavior.
6. For web UI, use the browser's built-in features (native elements, CSS, and
   platform APIs) before custom scripts or a new library, within the project's
   browser support target (default: widely supported features only). Verify
   support against current references such as MDN or the browser-compat data,
   not memory. A feature newer than the target needs a graceful fallback; one
   supported by a single browser or still experimental needs the owner's
   approval. When touching old code, replace a legacy workaround only if the
   change is in scope; otherwise note it as debt.
7. Keep business rules and authorization at their authoritative boundaries;
   client visibility is not permission enforcement.
8. Test deterministic interaction behavior and critical integrations. Inspect
   the rendered result at representative viewports and interaction states.
9. Compare the finished result with adjacent product surfaces for drift. Request
   human judgment for consequential aesthetics or product behavior.

Use an available UI-polish capability such as Impeccable when useful. Its output
is review evidence, not authority, and its absence never lowers the baseline.

Frontend code is public. Keep secrets, privileged keys, and authorization
decisions out of the client, and render only data the user may see; see the
[security baseline](../../engineering-review/references/security-baseline.md).
