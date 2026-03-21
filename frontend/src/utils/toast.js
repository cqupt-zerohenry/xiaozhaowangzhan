/**
 * Lightweight toast notification system.
 * Usage: toast.success('Saved!'), toast.error('Failed'), toast.info('Hint')
 */

let container = null;

function ensureContainer() {
  if (container) return container;
  container = document.createElement('div');
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

function show(message, type = 'info', duration = 3000) {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  ensureContainer().appendChild(el);
  setTimeout(() => {
    el.remove();
    if (container && container.children.length === 0) {
      container.remove();
      container = null;
    }
  }, duration);
}

export default {
  success: (msg) => show(msg, 'success'),
  error: (msg) => show(msg, 'error'),
  info: (msg) => show(msg, 'info'),
  warn: (msg) => show(msg, 'warn'),
};
