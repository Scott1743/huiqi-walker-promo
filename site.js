'use strict';

const shotButtons = Array.from(document.querySelectorAll('.shot'));
const dialog = document.querySelector('.lightbox');
const fullImage = document.querySelector('#full-image');
const fullTitle = document.querySelector('#full-title');
const fullImageLink = document.querySelector('#full-image-link');
let currentButton = null;
let opener = null;

function showShot(button) {
  const img = button.querySelector('img');
  currentButton = button;
  fullImage.src = img.getAttribute('src');
  fullImage.alt = img.alt;
  fullImageLink.href = img.getAttribute('src');
  const visible = shotButtons.filter(shot => !shot.hidden);
  fullTitle.textContent = `${visible.indexOf(button) + 1} / ${visible.length} · ${img.alt}`;
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

shotButtons.forEach(button => {
  button.addEventListener('click', () => showShot(button));
});
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
    const count = shotButtons.filter(shot => !shot.hidden).length;
    document.querySelector('#gallery-status').textContent = button.dataset.filter === 'all' ? `显示全部 ${count} 张截图` : `显示${button.dataset.filter}截图，共 ${count} 张`;
  });
});

document.querySelectorAll('video').forEach(video => {
  video.addEventListener('play', () => {
    document.querySelectorAll('video').forEach(other => { if (other !== video) other.pause(); });
  });
});
