# PS5 payload catalog

Personal source for [PS5 Payload Manager](https://github.com/itsPLK/ps5-payload-manager)
(Settings → Manage Sources → Add Source):

```
https://raw.githubusercontent.com/Ture919/ps5-payload-catalog/main/payloads.json
```

`payloads.json` is rebuilt every 6 hours by a GitHub Action from the latest GitHub releases
listed in `sources.json` (version, download URL and SHA-256 from the release asset).
Files are downloaded from the original GitHub releases; nothing is re-hosted here.

To add a payload, add an entry to `sources.json` (`repo`, `asset` regex, `prerelease`).
