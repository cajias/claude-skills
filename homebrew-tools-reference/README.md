# Homebrew Tools Reference Files

This directory contains reference files for the
[cajias/homebrew-tools](https://github.com/cajias/homebrew-tools) repository.

## Files

- **`claude-skills.rb`** - Homebrew formula for installing claude-skills (contains placeholder
  values that will be updated by the automated workflow)
- **`.github/workflows/update-claude-skills.yml`** - GitHub Actions workflow to automatically
  update the formula with actual release information

## Setup Instructions

These files need to be added to the
[cajias/homebrew-tools](https://github.com/cajias/homebrew-tools) repository:

### 1. Add the Formula

Copy `claude-skills.rb` to the root of the homebrew-tools repository:

```bash
cp claude-skills.rb /path/to/homebrew-tools/
```

### 2. Add the Workflow

Copy the workflow file to the homebrew-tools repository:

```bash
cp .github/workflows/update-claude-skills.yml /path/to/homebrew-tools/.github/workflows/
```

### 3. Configure TAP_REPO_TOKEN

The workflow requires a `TAP_REPO_TOKEN` secret in the claude-skills repository:

1. Create a GitHub Personal Access Token with `repo` permissions
2. Add it as a secret named `TAP_REPO_TOKEN` in the claude-skills repository settings

### 4. Initial Formula Update

After adding the files, trigger the first formula update either:

- Wait for the next release in claude-skills repository, or
- Manually trigger the workflow in homebrew-tools using the "Run workflow" button with an
  existing release tag

This will replace the placeholder values in `claude-skills.rb` with actual release information.

## How It Works

1. When a new release is created in the claude-skills repository, the
   `release-please.yml` workflow runs
2. The workflow dispatches a `claude-skills-release` event to the homebrew-tools repository
3. The `update-claude-skills.yml` workflow in homebrew-tools receives the event
4. The workflow downloads the release tarball, calculates the SHA256 hash
5. The workflow updates `claude-skills.rb` with the new version, URL, and SHA256
6. Changes are automatically committed and pushed to homebrew-tools

## Installation (After Setup)

Once the files are added to homebrew-tools, users can install claude-skills via:

```bash
brew tap cajias/tools
brew install claude-skills
```

## Reference Implementation

This implementation is based on the existing `dotfiles.rb` formula and
`update-dotfiles.yml` workflow in the homebrew-tools repository.
