# Public export validation

Prepared on 20 October 2026 from the latest supplied 17-module account export, `LinkedIn Simple Chat - Text and Image.blueprint (2).json`.

## Changes in the public copy

- Unbound Make connection and webhook IDs; replaced the concrete spreadsheet ID with an explicit setup placeholder.
- Removed cached restore/account labels and stale setup-validation metadata.
- Corrected the LinkedIn upload from `13.data` to the real Telegram `13.fileOutput` buffer and mapped `13.fileName`. The owner supplied a real Download a File output showing those fields.
- Changed the image-data guard to Basic Exists on `fileOutput`.
- Kept reply filters aligned at chat 3500, draft 1200, image 1200; removed an older conflicting 900-character topic-reply instruction.
- Preserved module IDs, research-before-editor order, publishing route, existing state guards, selected models, and sequential settings. The original source file was not modified.

## Checks

`export-validation.json` records the source/output SHA-256 hashes and 14 local assertions: module identity, route order, unbound connections, corrected file mapping/filter, JSON parser source, sequential processing, obvious-token and email scans, removal of the known source resource identifiers, and unchanged source bytes.

These are static checks. They do not establish native Make import compatibility, model access, successful search calls, factual accuracy, OAuth permissions, or successful LinkedIn publication. No external messages or posts were sent while preparing this copy. Users must configure their own accounts and complete an end-to-end check.

The weekly companion scenario was not included in the supplied current export and has not been reconstructed here. No weekly deployment or execution claim is made by these checks.
