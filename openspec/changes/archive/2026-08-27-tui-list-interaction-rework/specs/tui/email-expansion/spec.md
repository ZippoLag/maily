## REMOVED Requirements

### Requirement: Expand/collapse emails
**Reason**: The expansion feature was useless for triage — expanding an email with Enter/Space surfaced nothing more than the reading pane, and the triangles added visual noise. The interaction model now uses Enter and Space to mark emails instead, and the reading pane already renders the selected email's body.
**Migration**: Remove the expansion triangles, the expand/collapse toggle action, and the Enter/Space expand bindings. Enter and Space now mark the highlighted email. The reading pane remains the single surface for reading a selected email's content.