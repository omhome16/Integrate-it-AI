import { useEffect, useMemo, useState } from 'react';
import { Download, FileDown, FileText } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { ReportInfo } from '../../types';

interface Props {
  report?: ReportInfo;
}

function splitTableRow(row: string) {
  return row
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim().replace(/\\\|/g, '|'));
}

function isSeparatorRow(row: string) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(row);
}

function MarkdownPreview({ markdown }: { markdown: string }) {
  const blocks = useMemo(() => {
    const lines = markdown.replace(/\r\n/g, '\n').split('\n');
    const output: Array<{ type: string; lines: string[] }> = [];
    let index = 0;

    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) {
        index += 1;
        continue;
      }

      if (line.startsWith('```')) {
        const code: string[] = [];
        index += 1;
        while (index < lines.length && !lines[index].startsWith('```')) {
          code.push(lines[index]);
          index += 1;
        }
        output.push({ type: 'code', lines: code });
        index += 1;
        continue;
      }

      if (line.startsWith('|') && index + 1 < lines.length && isSeparatorRow(lines[index + 1])) {
        const table: string[] = [line];
        index += 2;
        while (index < lines.length && lines[index].startsWith('|')) {
          table.push(lines[index]);
          index += 1;
        }
        output.push({ type: 'table', lines: table });
        continue;
      }

      if (/^#{1,4}\s/.test(line)) {
        output.push({ type: 'heading', lines: [line] });
        index += 1;
        continue;
      }

      if (/^-\s+/.test(line)) {
        const items: string[] = [];
        while (index < lines.length && /^-\s+/.test(lines[index])) {
          items.push(lines[index].replace(/^-\s+/, ''));
          index += 1;
        }
        output.push({ type: 'list', lines: items });
        continue;
      }

      const paragraph: string[] = [line];
      index += 1;
      while (
        index < lines.length &&
        lines[index].trim() &&
        !/^#{1,4}\s/.test(lines[index]) &&
        !/^-\s+/.test(lines[index]) &&
        !lines[index].startsWith('|') &&
        !lines[index].startsWith('```')
      ) {
        paragraph.push(lines[index]);
        index += 1;
      }
      output.push({ type: 'paragraph', lines: paragraph });
    }

    return output;
  }, [markdown]);

  return (
    <div className="markdown-preview">
      {blocks.map((block, index) => {
        if (block.type === 'code') {
          return (
            <pre key={index}>
              <code>{block.lines.join('\n')}</code>
            </pre>
          );
        }

        if (block.type === 'table') {
          const [header, ...rows] = block.lines.map(splitTableRow);
          return (
            <div className="report-table-wrap" key={index}>
              <table>
                <thead>
                  <tr>{header.map((cell, cellIndex) => <th key={cellIndex}>{cell}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        if (block.type === 'heading') {
          const text = block.lines[0].replace(/^#{1,4}\s/, '');
          const level = block.lines[0].match(/^#+/)?.[0].length ?? 2;
          if (level === 1) return <h2 key={index}>{text}</h2>;
          if (level === 2) return <h3 key={index}>{text}</h3>;
          return <h4 key={index}>{text}</h4>;
        }

        if (block.type === 'list') {
          return (
            <ul key={index}>
              {block.lines.map((item, itemIndex) => (
                <li key={itemIndex}>{item}</li>
              ))}
            </ul>
          );
        }

        return <p key={index}>{block.lines.join(' ')}</p>;
      })}
    </div>
  );
}

export function ReportTab({ report }: Props) {
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!report) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(report.url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      })
      .then((text) => {
        if (!cancelled) setMarkdown(text);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [report]);

  if (!report) {
    return (
      <EmptyState
        icon={FileText}
        title="No Report Yet"
        description="Run the pipeline to generate a saved integration report."
      />
    );
  }

  return (
    <div className="tab-stack report-tab">
      <div className="report-actions">
        <div>
          <h3>{report.fileName}</h3>
          <p>{report.path}</p>
        </div>
        <div className="report-action-buttons">
          <a className="icon-text-button" href={report.url} download={report.fileName}>
            <Download size={15} />
            Markdown
          </a>
          <a className="icon-text-button" href={report.pdfUrl} download={report.fileName.replace(/\.md$/i, '.pdf')}>
            <FileDown size={15} />
            PDF
          </a>
        </div>
      </div>

      <section className="report-preview-panel">
        {loading && <p className="muted">Loading report...</p>}
        {error && <p className="muted">Unable to load report preview: {error}</p>}
        {!loading && !error && <MarkdownPreview markdown={markdown} />}
      </section>
    </div>
  );
}
