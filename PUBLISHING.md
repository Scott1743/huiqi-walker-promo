# Publishing the promotional website

Website: <https://scott1743.github.io/huiqi-walker-promo/>. This independent repository publishes its `main` branch root through GitHub Pages. A local file update is not an online deployment.

## Content and versioning

The current page presents **1.1.0 development content**, with one main trailer and one gameplay guide. `release_status` stays `pre_release`; publishing media does not release the game. `VERSION`, `version.json`, and the HTML version metadata must agree. Editing within a game version increments `media_revision` and the asset cache key.

Two current video files are `assets/videos/main.en.mp4` and `assets/videos/gameplay.en.mp4`. Each has English narration, burned English + Chinese subtitles, a poster, and English / Chinese / bilingual SRT and VTT files. Additional caption tracks must not be `default`, because the picture already contains subtitles.

Old media may remain in the repository for historical compatibility. It must not appear as a third current film or current download option. Existing historical tags remain immutable. Any new tag must be unique, for example `promo-game-1.1.0-r1`; no release link should be advertised before it exists.

## Verify and deploy

1. Synchronize `index.html`, `site.js`, `styles.css`, `VERSION`, `version.json`, the two films, their posters and captions, `README.md`, `MEDIA.md`, `press/`, and `CHANGELOG.md`.
2. Run `python3 scripts/check_site.py`. While media is still being produced, `--allow-missing-media` checks page structure but returns an explicitly incomplete result; it is **not** a release check.
3. Serve the directory locally with a server supporting byte ranges. Check the English default and Chinese switch, desktop/mobile layout, image filtering and keyboard navigation, both videos' play/seek/audio, and all optional caption tracks. Language changes must preserve media elements and playback position.
4. Keep every tracked file below 100 MiB. Use H.264 / yuv420p + AAC and MP4 faststart for browser playback; retain large masters outside this repository.
5. Review the independent repository diff and asset list, then commit and push normally to `main`. Do not commit the unrelated game workspace or rewrite existing history.
6. Verify the latest Pages build is `built` at the new commit. Fetch the public `version.json` and both video files; compare their sizes and SHA-256 hashes with the local delivery. Confirm public-page playback before reporting the update live.

The old version numbers `v1.0.0`, `v1.0.1`, `v1.1.0`, and `v1.1.3` were historical marketing revisions, not game release versions. See [historical numbering](history/marketing-revisions-before-1.0.0.md).
