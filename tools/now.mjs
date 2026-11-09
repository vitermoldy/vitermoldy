// Rewrites the "Last push" line in README.md from the GitHub API: the public repository pushed most
// recently, leaving out this profile repository and forks. Run by .github/workflows/now.yml; locally:
//   node tools/now.mjs
import { readFile, writeFile } from 'node:fs/promises';

const USER = 'vitermoldy';
const README = new URL('../README.md', import.meta.url);
const START = '<!-- now:start -->';
const END = '<!-- now:end -->';

const headers = { accept: 'application/vnd.github+json', 'user-agent': `${USER}-profile-readme` };
if (process.env.GITHUB_TOKEN) headers.authorization = `Bearer ${process.env.GITHUB_TOKEN}`;

const res = await fetch(`https://api.github.com/users/${USER}/repos?sort=pushed&per_page=20&type=owner`, { headers });
if (!res.ok) {
  console.error(`GitHub API answered ${res.status}; README left as it is.`);
  process.exit(1);
}
const repos = (await res.json()).filter((r) => !r.fork && !r.private && r.name.toLowerCase() !== USER);
if (!repos.length) {
  console.log('No public repository found; README left as it is.');
  process.exit(0);
}

const latest = repos[0];
const date = new Date(latest.pushed_at).toLocaleDateString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Asia/Jakarta',
});
const line = `Last push: [${latest.name}](${latest.html_url}), ${date}.`;

const text = await readFile(README, 'utf8');
const a = text.indexOf(START);
const b = text.indexOf(END);
if (a < 0 || b < a) {
  console.error('Markers not found in README.md.');
  process.exit(1);
}
const next = `${text.slice(0, a + START.length)}\n${line}\n${text.slice(b)}`;
if (next === text) {
  console.log(`Unchanged: ${line}`);
} else {
  await writeFile(README, next);
  console.log(`Updated: ${line}`);
}
