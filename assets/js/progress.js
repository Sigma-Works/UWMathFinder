/**
 * progress.js — remembers which questions a student has done or wants to review.
 *
 * Saved in the browser (localStorage), so there's no account: progress stays on
 * this device and browser only. Every read/write is wrapped in try/catch because
 * storage can be blocked (private windows, strict settings); the site then works
 * normally, it just doesn't remember.
 *
 * Exposed as the global `Progress`:
 *   Progress.get('q0012')            → 'done' | 'review' | null
 *   Progress.set('q0012', 'review')  → store a state (null clears it)
 *   Progress.toggle('q0012', 'done') → set it, or clear it if it was already that
 *   Progress.counts(ids)             → { done, review } among the given ids
 */
(function (root) {
  'use strict';

  const KEY = 'uwmf.progress.v1';      // bump the version if the stored shape ever changes
  const STATES = new Set(['done', 'review']);
  let cache = null;                    // { questionId: 'done' | 'review' }

  /** Load the saved map once; fall back to empty if storage is missing or corrupt. */
  function load() {
    if (cache) return cache;
    try {
      const parsed = JSON.parse(root.localStorage.getItem(KEY) || '{}');
      cache = parsed && typeof parsed === 'object' ? parsed : {};
    } catch (e) {
      cache = {};
    }
    return cache;
  }

  /** Write the map back; ignore failures (the in-memory copy still works this visit). */
  function save() {
    try { root.localStorage.setItem(KEY, JSON.stringify(cache)); } catch (e) { /* storage blocked */ }
  }

  function get(id) {
    return load()[id] || null;
  }

  function set(id, state) {
    load();
    if (STATES.has(state)) cache[id] = state;
    else delete cache[id];
    save();
  }

  function toggle(id, state) {
    set(id, get(id) === state ? null : state);
    return get(id);
  }

  function counts(ids) {
    const map = load();
    let done = 0, review = 0;
    for (const id of ids) {
      if (map[id] === 'done') done++;
      else if (map[id] === 'review') review++;
    }
    return { done, review };
  }

  root.Progress = { get, set, toggle, counts };
})(typeof window !== 'undefined' ? window : globalThis);
