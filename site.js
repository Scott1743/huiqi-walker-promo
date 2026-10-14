'use strict';

const shotButtons = Array.from(document.querySelectorAll('.shot'));
const dialog = document.querySelector('.lightbox');
const fullImage = document.querySelector('#full-image');
const fullTitle = document.querySelector('#full-title');
const fullImageLink = document.querySelector('#full-image-link');
let currentButton = null;
let opener = null;
let language = 'en';

function updateGalleryStatus() {
  const count = shotButtons.filter(shot => !shot.hidden).length;
  const all = document.querySelector('.filter[aria-pressed="true"]')?.dataset.filter === 'all';
  document.querySelector('#gallery-status').textContent = language === 'en'
    ? `Showing ${all ? 'all ' : ''}${count} screenshots`
    : `${all ? '显示全部' : '显示'} ${count} 张截图`;
}

function updateLightbox() {
  if (!currentButton) return;
  const img = currentButton.querySelector('img');
  const visible = shotButtons.filter(shot => !shot.hidden);
  fullImage.alt = img.alt;
  fullTitle.textContent = `${visible.indexOf(currentButton) + 1} / ${visible.length} · ${img.alt}`;
}

function setLanguage(next) {
  language = next === 'zh-CN' ? 'zh-CN' : 'en';
  const attribute = language === 'en' ? 'data-en' : 'data-zh';
  document.documentElement.lang = language;
  document.querySelectorAll('[data-en][data-zh]').forEach(element => {
    element.textContent = element.getAttribute(attribute);
  });
  for (const target of ['alt', 'aria-label']) {
    document.querySelectorAll(`[${attribute}-${target}]`).forEach(element => {
      element.setAttribute(target, element.getAttribute(`${attribute}-${target}`));
    });
  }
  document.querySelectorAll('[data-language]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.language === language));
  });
  document.title = language === 'en' ? '灰契行者 · Main Trailer & Gameplay' : '灰契行者 · 主宣发与核心玩法';
  const labels = language === 'en'
    ? ['Main navigation', 'Filter screenshots', 'Full-size gameplay screenshot', 'Previous screenshot', 'Next screenshot']
    : ['主导航', '筛选截图', '实机截图原图', '上一张截图', '下一张截图'];
  ['.topbar nav', '.filters', '.lightbox', '#previous', '#next'].forEach((selector, index) => {
    document.querySelector(selector).setAttribute('aria-label', labels[index]);
  });
  updateGalleryStatus();
  updateLightbox();
  try { localStorage.setItem('huiqi-promo-language', language); } catch (_) { /* Storage is optional. */ }
}

document.querySelectorAll('[data-language]').forEach(button => {
  button.addEventListener('click', () => setLanguage(button.dataset.language));
});
try {
  const saved = localStorage.getItem('huiqi-promo-language');
  if (saved === 'zh-CN') setLanguage(saved);
} catch (_) { /* English remains the default. */ }

function showShot(button) {
  const img = button.querySelector('img');
  currentButton = button;
  fullImage.src = img.getAttribute('src');
  fullImageLink.href = img.getAttribute('src');
  updateLightbox();
  if (!dialog.open) {
    opener = button;
    dialog.showModal();
  }
}

function moveShot(direction) {
  const visible = shotButtons.filter(shot => !shot.hidden);
  const index = visible.indexOf(currentButton);
  showShot(visible[(index + direction + visible.length) % visible.length]);
}

shotButtons.forEach(button => button.addEventListener('click', () => showShot(button)));
document.querySelector('.lightbox-close').addEventListener('click', () => dialog.close());
document.querySelector('#previous').addEventListener('click', () => moveShot(-1));
document.querySelector('#next').addEventListener('click', () => moveShot(1));
dialog.addEventListener('close', () => opener?.focus());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const rect = dialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
});
dialog.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    moveShot(event.key === 'ArrowLeft' ? -1 : 1);
    event.preventDefault();
  }
});

document.querySelectorAll('.filter').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(filter => filter.setAttribute('aria-pressed', String(filter === button)));
    shotButtons.forEach(shot => { shot.hidden = button.dataset.filter !== 'all' && shot.dataset.feature !== button.dataset.filter; });
    updateGalleryStatus();
  });
});

document.querySelectorAll('video').forEach(video => {
  video.addEventListener('play', () => {
    document.querySelectorAll('video').forEach(other => { if (other !== video) other.pause(); });
  });
  video.addEventListener('loadedmetadata', () => {
    if (!Number.isFinite(video.duration)) return;
    const slug = video.closest('article').id.replace('video-', '');
    const seconds = Math.round(video.duration);
    document.querySelector(`[data-duration-for="${slug}"]`).textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  });
});
