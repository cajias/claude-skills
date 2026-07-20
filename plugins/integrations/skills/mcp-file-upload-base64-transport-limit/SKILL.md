---
name: mcp-file-upload-base64-transport-limit
description: |
  Why you cannot upload a real file (>~15 KB) through content-MCP tools that
  take base64 inline — Google Drive `create_file`, similar Notion/media MCPs —
  and what to do instead. Use when: (1) `create_file` (or any MCP upload) fails
  with "Request contains an invalid argument" on a .pptx/.pdf/.png/.zip; (2) an
  upload subagent loops for many minutes / hours retrying the same file;
  (3) you Read a base64 file to feed a tool and it truncates (e.g. "returned
  only the first 22,377 of 124,988 characters", 25K-token cap, one unbreakable
  line); (4) you're about to push a binary to Drive/Notion via an MCP and the
  file is more than ~11 KB; (5) you need to embed a deck/file in Notion (Notion
  MCP is URL/text-only — no binary upload). Also records that Office files
  (.pptx/.docx/.xlsx) DO auto-convert to native Google editor types on
  create_file by default.
author: Claude Code
version: 1.0.0
date: 2026-06-30
---

# MCP file-upload base64 transport limit

## Problem

Content-oriented MCP upload tools (e.g. Google Drive `create_file`) accept file bytes
only as **base64 passed inline in the tool call** — there is no "upload from path"
input. That base64 must therefore pass through the *model's context*, and it hits two
independent hard limits that make uploading anything but tiny files impossible:

1. **Reading it back truncates.** If a subagent writes base64 to a file and Reads it to
   put in the call, the Read tool truncates large content (observed: only 22,377 of
   124,988 chars returned — a ~25K-token cap, made worse because base64 is one giant
   unbreakable line).
2. **Emitting it inline corrupts.** When the model generates the base64 directly into
   the tool arguments, long strings corrupt/truncate. Empirically: a 28 KB pptx
   (~37K base64 chars) failed with `Request contains an invalid argument`; a ~10 KB
   pptx (~13.7K chars) succeeded.

Net: `create_file`-style base64 upload is reliable only for files under **~11 KB**
(~15K base64 chars). Real artifacts (decks, PDFs, images) are 50–150 KB+ and will
fail — often after an agent burns minutes-to-hours retrying.

## Context / Trigger Conditions

- MCP upload fails with **"Request contains an invalid argument"** on a binary file.
- An upload subagent runs for a very long time (saw ~2.4 h / 200K tokens) retrying.
- Read returns "first N of M characters" on a `.b64` file you meant to feed to a tool.
- About to move a >~11 KB binary to Drive/Notion through an MCP.
- Need a deck/image *in Notion*: the Notion MCP (`notion-create-pages` /
  `notion-update-page`) is Notion-Markdown + **URL-referenced media only — no binary
  upload**.

## Solution

**Never route file bytes through the model.** Use a disk-based transport the model only
*invokes* (it never holds the bytes):

- **Google Drive (recommended): `rclone`.** One-time `rclone config` (type `drive`,
  scope full, browser OAuth). Then upload straight from disk, converting to a native
  Google editor type on the way in:

  ```
  rclone copy "deck.pptx" gdrive: \
    --drive-root-folder-id <FOLDER_ID> \
    --drive-import-formats pptx
  ```

  Target a specific folder by id with `--drive-root-folder-id`. Add `--drive-team-drive <id>`
  if the folder lives in a Shared Drive.
- **Share / get an embeddable URL** (Drive MCP has no set-permission tool):
  `rclone link gdrive:<path>` sets anyone-with-link AND returns the URL.
- **Into Notion:** put the file somewhere with a public URL (e.g. the Google Slides from
  above, or a static host), then embed the URL via `notion-update-page` — do not try to
  upload the binary.
- Keep the MCP `create_file` path only for genuinely tiny payloads (<~11 KB) or text
  (`textContent`).

## Verification

- `rclone` upload returns the new object; confirm conversion via Drive MCP
  `get_file_metadata` → `mimeType == application/vnd.google-apps.presentation` (or
  `.document` / `.spreadsheet`).
- `rclone link` returns a `https://…` URL that renders when embedded.

## Example

93 KB workshop deck (`Measuring the AI-First Organization.pptx`, ~125K base64 chars):
MCP `create_file` could not move it (Read truncated at 22K chars; inline emission
corrupted). `rclone copy … --drive-import-formats pptx` uploaded it from disk in one
shot and Drive converted it to a native Google Slides file; `rclone link` produced the
anyone-with-link URL embedded on the matching Notion page.

## Notes

- **Office auto-converts on create_file.** Despite the `create_file` schema listing only
  `text/plain`→Doc and `text/csv`→Sheet as default conversions, that list is
  non-exhaustive: uploading a `.pptx` with `contentMimeType=application/vnd.openxmlformats-officedocument.presentationml.presentation`
  yields a **native Google Slides** file by default. Set `disableConversionToGoogleType:true`
  only if you want to keep it as a raw Office file. (So the conversion was never the
  problem — only the transport was.)
- The Google Drive MCP set has **no delete/trash tool and no set-permission tool** —
  uploads are create-only (no upsert; re-runs duplicate), cleanup and sharing are manual
  or via rclone. Use `search_files` by title before uploading to avoid duplicates.
- This is the same class of limit as any "binary through an LLM context" attempt — it
  applies to subagents too, so do NOT fan out base64 uploads across subagents expecting
  it to help; they hit the identical wall. Subagents are still correct for the *build*
  step (local file generation), just not for the *transport*.

## The clean fix: Google Drive for desktop local mount

If the user runs **Google Drive for desktop**, the simplest transport needs no rclone,
no OAuth, no base64 — just a filesystem copy into the synced mount.

- **Mount location (macOS):** `~/Library/CloudStorage/GoogleDrive-<email>/My Drive/`.
  Copying a file into any synced folder there uploads it on the next sync. Proven:
  `cp deck.pptx "…/My Drive/ai-sdlc/presentations/"` appeared in Drive within seconds,
  byte-identical.
- **In-place updates keep the SAME `fileId`.** Re-copying an edited file over the same
  path *updates the existing Drive file in place* — same `fileId`, new
  `modifiedTime`/`size` — NOT a delete+recreate. This sidesteps the Drive MCP's lack of
  a delete/trash tool AND lack of upsert. Confirmed by checking `createdTime` and
  `fileId` unchanged after an overwrite. (Contrast the MCP `create_file` path, which
  duplicates on re-run.)
- **Sharing can come free.** If the destination folder is already link-shared
  ("anyone with link → reader"), files dropped in **inherit** it — immediately
  embeddable by URL. The Drive MCP has NO permission-setting tool (only
  `get_file_permissions`, read-only), so a **pre-shared folder is the easy path**;
  otherwise sharing needs the web UI / browser.
- **Conversion caveat.** A desktop-sync copy of a `.pptx` lands as a **`.pptx` (Office
  file), NOT native Google Slides**. Drive-for-desktop never runs the "convert to Google
  editor format" step — only web-UI upload with the convert setting, or an API import
  with `mimeType=application/vnd.google-apps.presentation`, does. The Drive MCP
  `copy_file` tool CANNOT convert either (it has no `mimeType` param). To get native
  Slides you need a browser step (Open with Google Slides → Save as Google Slides) or
  `rclone --drive-import-formats`.
- **Notion embed.** A `.pptx` in Drive that's link-shared embeds inside Notion via an
  `<embed src="https://drive.google.com/file/d/<ID>/preview">` block (Notion
  enhanced-markdown embed). Verified it renders the actual slides inline (after a brief
  load spinner). Notion has no bookmark block in its enhanced-markdown spec and no binary
  upload — URL/embed only.
