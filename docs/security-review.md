# Security Review

## Findings

1. License URLs present in `LICENSE`.
2. No email addresses found in repository content.
3. No credential assignments found (`password`, `secret`, `token`, `apiKey`, `clientSecret` patterns).
4. No internal collaboration links (SharePoint, Teams, internal GitHub URLs) found.
5. No internal hostnames or customer identifiers found after remediation.

## Disposition

1. **License URLs**: acceptable and required for OSS license text.
2. **No email addresses**: no action needed.
3. **No credentials/secrets**: no action needed.
4. **No internal collaboration links**: no action needed.
5. **No internal hostnames/identifiers**: no action needed.

## Remediation

- Rewrote product-specific and enterprise-specific wording in public docs.
- Replaced enterprise prompt content in `docs/prompts/` with relocation notices.
- Added generic prompt alternatives for public use.
- Added private placeholder directory `private/enterprise-examples/` to indicate separation boundary.
