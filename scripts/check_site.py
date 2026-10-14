#!/usr/bin/env python3
"""Check the two-film site; missing-media mode is preparation, never release QA."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.video_cards, self.videos = [], [], []
        self.ids, self.meta = set(), {}
        self.language, self.current_video = None, None
        self.language_buttons = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'html':
            self.language = attrs.get('lang')
        if tag == 'video':
            self.current_video = {'source': None, 'tracks': [], 'preload': attrs.get('preload')}
            self.videos.append(self.current_video)
        if tag == 'source' and self.current_video is not None:
            self.current_video['source'] = urlsplit(attrs.get('src', '')).path
        if tag == 'track' and self.current_video is not None:
            self.current_video['tracks'].append(attrs)
        if tag == 'article' and 'video-card' in attrs.get('class', '').split():
            self.video_cards.append((attrs.get('id'), 'featured' in attrs['class'].split()))
        if tag == 'button' and 'data-language' in attrs:
            self.language_buttons.append((attrs['data-language'], attrs.get('aria-pressed')))
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('src', 'href', 'poster'):
            if attrs.get(name):
                self.links.append(attrs[name])
        if tag == 'meta' and attrs.get('name'):
            self.meta[attrs['name']] = attrs.get('content')

    def handle_endtag(self, tag):
        if tag == 'video':
            self.current_video = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-missing-media', action='store_true', help='Prepare the page before media delivery; output remains INCOMPLETE if assets are missing.')
    args = parser.parse_args()
    errors, pending = [], set()
    release = json.loads((ROOT / 'version.json').read_text())
    version = (ROOT / 'VERSION').read_text().strip()
    page = Page()
    html = (ROOT / 'index.html').read_text()
    page.feed(html)
    records = release.get('videos', [])
    if [record.get('id') for record in records] != ['main', 'gameplay']:
        errors.append('version.json must describe main and gameplay, in that order')
    expected_media = set()
    for record in records:
        expected_media.update([record['path'], record['poster']])
        if set(record.get('subtitles', {})) != {'en', 'zh-CN', 'bilingual'}:
            errors.append(f"Missing caption languages for {record['id']}")
        for language, formats in record.get('subtitles', {}).items():
            if set(formats) != {'srt', 'vtt'}:
                errors.append(f"Expected SRT and VTT for {record['id']}/{language}")
            expected_media.update(formats.values())
    if page.video_cards != [('video-main', True), ('video-gameplay', False)] or len(page.videos) != 2:
        errors.append('Show exactly one featured main trailer followed by one gameplay guide')
    for slug, video in zip(['main', 'gameplay'], page.videos):
        if video['source'] != f'assets/videos/{slug}.en.mp4':
            errors.append(f'Wrong current video source: {slug}')
        if video['preload'] != 'none':
            errors.append(f'Keep large video preload disabled: {slug}')
        tracks = video['tracks']
        actual = {urlsplit(track.get('src', '')).path for track in tracks}
        expected = {f'assets/subtitles/{slug}.{language}.vtt' for language in ['en', 'zh-CN', 'bilingual']}
        if actual != expected or len(tracks) != 3:
            errors.append(f'Expected English, Chinese and bilingual VTT tracks: {slug}')
        if any('default' in track for track in tracks):
            errors.append(f'Burned bilingual subtitles must not have a default extra caption track: {slug}')
    if page.language != 'en' or page.language_buttons != [('en', 'true'), ('zh-CN', 'false')]:
        errors.append('Static default must be English, with an English / Chinese switch')
    if version != release.get('site_version') or version != release.get('game_version'):
        errors.append('VERSION, site_version and game_version must agree')
    if release.get('release_status') != 'pre_release':
        errors.append('A media update must preserve pre_release game status')
    if not isinstance(release.get('media_revision'), int) or release['media_revision'] < 1:
        errors.append('media_revision must be a positive integer')
    for name, value in [('site-version', version), ('game-version', release['game_version'])]:
        if page.meta.get(name) != value:
            errors.append(f'index.html {name} does not match version.json')
    expected_scope = {'collectible_cards': 96, 'chapters': 3, 'equipment_types': 28, 'equipment_bases': 16, 'core_equipment': 12, 'endless_mode': True, 'animated_card_backs': 10, 'classic_card_backs': 1}
    for key, value in expected_scope.items():
        if release.get('scope', {}).get(key) != value:
            errors.append(f'Wrong current development scope: {key}')
    if '[ENGLISH GAME TITLE]' in html or 'Wishlist on Steam' in html:
        errors.append('Do not publish an unconfirmed English title or Steam CTA')
    if any(re.search(r'assets/videos/(narrative|combat|builds)\.', link) for link in page.links):
        errors.append('Legacy three-film assets must not be linked as current videos')

    references = [(ROOT / 'index.html', ref) for ref in page.links]
    for source in list(ROOT.glob('*.css')) + [ROOT / 'index.html']:
        references.extend((source, ref) for ref in re.findall(r"url\(['\"]?([^'\")]+)", source.read_text()))
    for source in list(ROOT.glob('*.md')) + list((ROOT / 'press').glob('*.md')) + list((ROOT / 'history').glob('*.md')):
        references.extend((source, ref) for ref in re.findall(r'\]\(([^)]+)\)', source.read_text()))
    references.extend((ROOT / 'version.json', ref) for ref in expected_media)
    for source, ref in references:
        link = urlsplit(ref)
        if link.scheme or link.netloc:
            continue
        if not link.path:
            if source.name == 'index.html' and link.fragment and link.fragment not in page.ids:
                errors.append(f'Missing page anchor: {ref}')
            continue
        if link.path.startswith('/'):
            errors.append(f'Project Pages requires relative resource paths: {ref}')
            continue
        destination = (source.parent / unquote(link.path)).resolve()
        if not destination.is_relative_to(ROOT):
            errors.append(f'Reference leaves the site: {ref}')
            continue
        if not destination.exists():
            relative = str(destination.relative_to(ROOT))
            if args.allow_missing_media and relative in expected_media:
                pending.add(relative)
            else:
                errors.append(f'Missing local reference in {source.name}: {ref}')
    for path in sorted(expected_media):
        asset = ROOT / path
        if asset.is_file() and asset.stat().st_size == 0:
            errors.append(f'Empty current media asset: {path}')
        if asset.is_file() and asset.suffix == '.vtt' and not asset.read_text().lstrip('\ufeff').startswith('WEBVTT'):
            errors.append(f'Invalid VTT header: {path}')
        if asset.is_file() and asset.suffix == '.srt' and '-->' not in asset.read_text():
            errors.append(f'No subtitle cues: {path}')
    files = [path for path in ROOT.rglob('*') if path.is_file() and '.git' not in path.parts]
    for path in files:
        if path.stat().st_size >= 100 * 1024 * 1024:
            errors.append(f'GitHub file size limit: {path.relative_to(ROOT)}')
    if errors:
        raise SystemExit('\n'.join(sorted(set(errors))))
    total = sum(path.stat().st_size for path in files)
    status = 'INCOMPLETE — page checks passed; media still missing' if pending else 'OK'
    print(f"{status}: game/marketing v{version}, media r{release['media_revision']}; two films; {len(references)} references; {len(files)} files, {total / 1024 / 1024:.1f} MiB")
    if pending:
        print(json.dumps({'publish_ready': False, 'missing_media': sorted(pending)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
