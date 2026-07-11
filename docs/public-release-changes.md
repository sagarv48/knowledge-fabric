# Public Release Changes

## Files modified

- `README.md`
- `docs/README.md`
- `docs/AIPromptForImplementation.md`
- `docs/docs-setup.md`
- `docs/repo-boundaries.md`
- `docs/prompts/Cleanup_Private_Content_Relocation.md`
- `docs/prompts/MASTER_Setup_All_Phases.md`

## Files added

- `CONTRIBUTING.md`
- `docs/public-review-report.md`
- `docs/content-classification.md`
- `docs/security-review.md`
- `docs/open-source-checklist.md`
- `docs/public-release-changes.md`
- `docs/prompts/Cleanup_Open_Source_Readiness.md`
- `docs/prompts/MASTER_Setup_All_Phases_Generic.md`
- `private/enterprise-examples/README.md`

## Files removed

- None

## Files moved

- Enterprise-specific prompt content was relocated out of public-facing prompt files and replaced with relocation notices.

## References replaced

- Product-specific names replaced with vendor-neutral terms such as:
  - "runtime MCP adapter"
  - "product-specific integration"
  - "enterprise integration adapters"
  - "knowledge organization framework"
  - "intent orchestration layer"

## Private material isolated

- Enterprise-only examples are represented by placeholders in `private/enterprise-examples/`.
- Public prompt files now either contain generic guidance or explicit relocation notices.

## Outstanding risks

1. `private/enterprise-examples/` is still in this repository as a placeholder location; if strict public-only publishing is required, move this directory to a separate private repository before release.
