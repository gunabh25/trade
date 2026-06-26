/** Lightweight markdown → HTML for journal preview (no external deps). */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function renderMarkdown(source: string): string {
  const lines = source.split('\n');
  const html: string[] = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      html.push('</ul>');
      inList = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith('### ')) {
      closeList();
      html.push(`<h3>${inlineFormat(escapeHtml(line.slice(4)))}</h3>`);
    } else if (line.startsWith('## ')) {
      closeList();
      html.push(`<h2>${inlineFormat(escapeHtml(line.slice(3)))}</h2>`);
    } else if (line.startsWith('# ')) {
      closeList();
      html.push(`<h1>${inlineFormat(escapeHtml(line.slice(2)))}</h1>`);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) {
        html.push('<ul>');
        inList = true;
      }
      html.push(`<li>${inlineFormat(escapeHtml(line.slice(2)))}</li>`);
    } else if (line === '') {
      closeList();
      html.push('<br />');
    } else {
      closeList();
      html.push(`<p>${inlineFormat(escapeHtml(line))}</p>`);
    }
  }
  closeList();
  return html.join('');
}

function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(
      /\[(.+?)\]\((.+?)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
    );
}
