const types = {
  software: /software|\bswe\b|\bsde\b/i,
  ml: /machine learning|\bml\b|\bai\b|artificial intelligence/i,
  data: /data|analytics/i,
  security: /security|cyber/i,
  embedded: /embedded|firmware/i,
  infrastructure: /infrastructure|\bsre\b|site reliability|platform|devops/i,
};

function timestamp(job) {
  return Date.parse(job.date) || 0;
}

function matches(job, filters, now = Date.now()) {
  const primary = ['new_grad_2027', 'general_early_career'].includes(job.section);
  if (!primary && !filters.secondary) return false;
  if (!`${job.company || ''} ${job.title || ''}`.toLowerCase().includes(filters.search.toLowerCase().trim())) return false;
  if (filters.location && !(job.locations || []).includes(filters.location)) return false;
  const matchedTypes = Object.keys(types).filter(type => types[type].test(job.title || ''));
  if (filters.type && matchedTypes.length && !matchedTypes.includes(filters.type)) return false;
  if (filters.week && (!job.date || timestamp(job) < now - 7 * 86400000 || timestamp(job) > now)) return false;
  return true;
}

const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
};

function card(job) {
  const secondary = !['new_grad_2027', 'general_early_career'].includes(job.section);
  const article = element('article', null, `job${secondary ? ' secondary' : ''}`);
  const content = element('div');
  if (job.company) content.append(element('p', job.company, 'company'));
  if (job.title) content.append(element('h2', job.title));
  if (secondary) content.append(element('span', 'Low confidence', 'badge'));
  if (job.status === 'closed') content.append(element('span', 'Closed', 'badge'));
  if (job.full_time_unverified) content.append(element('span', '⚠️ Full-time unverified', 'badge'));
  if (job.manual_check) content.append(element('span', '📝 Manual check', 'badge'));
  const locations = job.locations || [];
  if (locations.length >= 3) {
    const details = element('details', null, 'meta');
    details.append(element('summary', `${locations.length} locations`));
    for (const location of locations) details.append(element('div', location));
    content.append(details);
  } else if (locations.length) content.append(element('p', locations.join(' · '), 'meta'));
  if (job.date) content.append(element('p', `${job.date_kind}: ${job.date.slice(0, 10)}`, 'meta'));
  if (job.notes) content.append(element('p', job.notes, 'notes'));
  for (const [key, label] of [['deadline', 'Deadline'], ['sponsorship', 'Sponsorship'], ['citizenship', 'Citizenship'], ['degree_level', 'Degree']]) {
    if (job[key]) content.append(element('p', `${label}: ${job[key]}`, 'meta'));
  }
  article.append(content);
  if (job.apply_url) {
    try {
      const url = new URL(job.apply_url);
      if (['https:', 'http:'].includes(url.protocol)) {
        const link = element('a', job.status === 'closed' ? 'View posting' : 'Apply', 'apply');
        link.href = url.href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        article.append(link);
      }
    } catch {}
  }
  return article;
}

async function start() {
  const count = document.querySelector('#count');
  const list = document.querySelector('#list');
  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error('Data unavailable');
    const data = await response.json();
    const jobs = data.jobs.slice().sort((a, b) => timestamp(b) - timestamp(a));
    const location = document.querySelector('#location');
    for (const value of [...new Set(jobs.flatMap(job => job.locations || []))].sort()) {
      const option = element('option', value);
      option.value = value;
      location.append(option);
    }
    const update = () => {
      const filters = {
        search: document.querySelector('#search').value,
        location: location.value,
        type: document.querySelector('#type').value,
        week: document.querySelector('#week').checked,
        secondary: document.querySelector('#secondary').checked,
      };
      const visible = jobs.filter(job => matches(job, filters));
      count.textContent = `${visible.length} ${visible.length === 1 ? 'role' : 'roles'}`;
      list.replaceChildren(...visible.map(card));
      if (!visible.length) list.append(element('p', 'No roles match these filters.'));
    };
    document.querySelector('#filters').addEventListener('submit', event => event.preventDefault());
    document.querySelector('#filters').addEventListener('input', update);
    update();
  } catch {
    count.textContent = 'Listings could not load. Generate site/data.json and serve this folder over HTTP.';
  }
}

if (typeof document !== 'undefined') start();
if (typeof module !== 'undefined') module.exports = { matches, timestamp };
