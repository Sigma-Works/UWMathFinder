#!/usr/bin/env node
/**
 * syllabus-reminder.js — print the quarterly "confirm the syllabus" issue.
 *
 * Used by .github/workflows/syllabus-reminder.yml. Output format:
 *   line 1      → issue title
 *   lines 2..n  → issue body (Markdown)
 * Run it locally to preview: `node scripts/syllabus-reminder.js`
 */
const path = require('node:path');
const { currentTerm } = require('../assets/js/syllabus.js');
const syllabus = require(path.join(__dirname, '..', 'syllabus.json'));

const repo = process.env.REPO_URL || 'https://github.com/Sigma-Works/UWMathFinder';
// the workflow runs ~2 weeks before a quarter, so look ahead to the quarter that's starting
const term = currentTerm(new Date(Date.now() + 14 * 24 * 60 * 60 * 1000));

const rows = Object.entries(syllabus.courses).map(([course, conf]) =>
  `- [ ] **${course}** (last confirmed: ${conf.verified || 'never'})`);

console.log(`Confirm syllabi for ${term}
**${term}** is about to start. For each course below, check the course page or syllabus, then edit [\`syllabus.json\`](${repo}/blob/main/syllabus.json):

1. **Nothing changed:** set \`"verified": "${term}"\`.
2. **A topic was dropped or added:** add an entry to \`changes\` and set \`verified\`. See [docs/syllabus-changes.md](${repo}/blob/main/docs/syllabus-changes.md) for examples.

Until a course is confirmed, the practice-exam generator shows students a "last confirmed" warning for it.

${rows.join('\n')}

Close this issue once every box is ticked.`);
