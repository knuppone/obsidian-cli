# obsidian-cli

Command-line tool for Obsidian vault operations. Works **headless** against vault files on disk (default), or via the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin when Obsidian is running.

## Install

```bash
cd /path/to/obsidian_cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `OBSIDIAN_VAULT` | (auto-detect) | Vault root path |
| `OBSIDIAN_API_KEY` | — | REST API key (required for `--backend rest`) |
| `OBSIDIAN_HOST` | `127.0.0.1` | REST host |
| `OBSIDIAN_PORT` | `27124` | REST port |
| `OBSIDIAN_PROTOCOL` | `https` | `http` or `https` |
| `OBSIDIAN_VERIFY_SSL` | `false` | Verify TLS (use `false` for self-signed) |

```bash
export OBSIDIAN_VAULT=~/path/to/vault
export OBSIDIAN_API_KEY=your-key-from-plugin-settings
export OBSIDIAN_VERIFY_SSL=false
```

## Capability matrix

| Feature | `--backend fs` | `--backend rest` |
|---------|----------------|------------------|
| List / read / write / delete files (text + binary) | Yes | Yes |
| Append, patch (heading / block / frontmatter) | Yes | Yes |
| Simple text search | Yes | Yes |
| Tag search | Yes | Yes |
| JsonLogic search | No | Yes |
| Active file read/write | No | Yes |
| Periodic notes | No | Yes |
| Command palette list/run | No | Yes |

## Command reference

Global options: `--vault`, `--backend fs|rest`, `--api-key`, `--human`

### Diagnostics

```bash
obsidian-cli doctor
obsidian-cli list-root
obsidian-cli list-dir notes
```

### File operations (`file`)

```bash
# Read (JSON: path, encoding, content, size)
obsidian-cli file read notes/meeting.md
obsidian-cli file read notes/meeting.md --metadata

# Write / create (replaces entire file)
obsidian-cli file write notes/new.md --content "# Title\n"
echo "body" | obsidian-cli file write notes/new.md

# Binary write
base64 < image.png | obsidian-cli file write assets/image.png --base64 --content-type image/png

# Append, patch, delete
obsidian-cli file append inbox.md --content "- [ ] Task\n"
obsidian-cli file patch notes/foo.md \
  --operation append --target-type heading --target "Section::Sub" \
  --content "More text\n"
obsidian-cli file delete notes/old.md --confirm
```

Legacy aliases: `read`, `append`, `patch`, `delete`, `search` (same behavior).

### Search (`search`)

```bash
obsidian-cli search text "meeting notes"
obsidian-cli search tag work --dir notes
obsidian-cli search json query.json
obsidian-cli search json --tag work --dir notes
echo '{"glob":["*.md",{"var":"path"}]}' | obsidian-cli search json
```

### Active file (`active`) — REST only

Requires Obsidian with a note open.

```bash
obsidian-cli --backend rest active read
obsidian-cli --backend rest active write --content "# Updated\n"
obsidian-cli --backend rest active append --content "Line\n"
obsidian-cli --backend rest active patch \
  --operation append --target-type heading --target "Tasks" --content "- [ ] Item\n"
obsidian-cli --backend rest active delete
```

### Periodic notes (`periodic`) — REST only

```bash
obsidian-cli --backend rest periodic get daily
obsidian-cli --backend rest periodic recent daily --limit 5 --include-content
obsidian-cli --backend rest periodic append daily --content "- [ ] Log entry\n"
obsidian-cli --backend rest periodic write daily --content "# Daily\n"
obsidian-cli --backend rest periodic delete daily
```

Periods: `daily`, `weekly`, `monthly`, `quarterly`, `yearly`.

### Commands (`command`) — REST only

```bash
obsidian-cli --backend rest command list
obsidian-cli --backend rest command list --filter "daily"
obsidian-cli --backend rest command run "periodic-notes:open-daily-note"
```

## Troubleshooting REST auth (40101)

1. Run `obsidian-cli --backend rest doctor`
2. Re-copy API key from Obsidian → Settings → Local REST API
3. Or `unset OBSIDIAN_API_KEY` to use the key from `.obsidian/plugins/obsidian-local-rest-api/data.json`
4. Ensure `OBSIDIAN_API_KEY` is exported in the same shell that runs the CLI

## Tests

```bash
pytest
```

## License

MIT
