/**
 * schedule-parser.js
 *
 * Standalone, dependency-free JavaScript implementation of the schedule text parser.
 * Suitable for direct inclusion in a static website (e.g., GitHub Pages portfolio).
 *
 * Usage:
 *   <script src="schedule-parser.js"></script>
 *   const result = ScheduleParser.parseScheduleText(rawText);
 *   // result.events is an array of { title, date, startTime, endTime?, location?, category }
 *
 * The parser handles common PDF-extracted and syllabus-pasted formats:
 * - Block layouts with date headers
 * - Flattened table text
 * - Mixed 12-hour / 24-hour times
 * - Locations, categories inferred from keywords
 * - Basic deduplication and date normalization to YYYY-MM-DD
 *
 * This is a portable extraction of the core parsing logic. Keep this file in sync
 * with any refinements made to the primary implementation.
 */

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ScheduleParser = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function to12HourTime(time) {
    if (!time) return '';
    if (time.match(/AM|PM/i)) {
      return time.toUpperCase();
    }
    const match = time.match(/^(\d{1,2}):?(\d{2})?$/);
    if (!match) return time;
    let hours = parseInt(match[1], 10);
    const minutes = match[2] || '00';
    const period = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    if (hours === 0) hours = 12;
    return `${hours}:${minutes} ${period}`;
  }

  function normalizeDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') {
      return null;
    }
    const months = {
      january: 1, february: 2, march: 3, april: 4, may: 5, june: 6,
      july: 7, august: 8, september: 9, october: 10, november: 11, december: 12,
      jan: 1, feb: 2, mar: 3, apr: 4, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12
    };
    // Month DD, YYYY
    const monthMatch = dateStr.match(/(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})/i);
    if (monthMatch) {
      const month = months[monthMatch[1].toLowerCase()];
      const day = monthMatch[2].padStart(2, '0');
      const year = monthMatch[3];
      return `${year}-${String(month).padStart(2, '0')}-${day}`;
    }
    // MM/DD/YYYY or MM/DD/YY
    const slashMatch = dateStr.match(/(\d{1,2})\/(\d{1,2})\/(\d{2,4})/);
    if (slashMatch) {
      const month = slashMatch[1].padStart(2, '0');
      const day = slashMatch[2].padStart(2, '0');
      const year = slashMatch[3].length === 2 ? `20${slashMatch[3]}` : slashMatch[3];
      return `${year}-${month}-${day}`;
    }
    // YYYY-MM-DD
    const isoMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (isoMatch) {
      return dateStr;
    }
    return null;
  }

  function extractLocation(text) {
    const patterns = [
      /(?:room|rm\.?|building|bldg|hall|location|loc)\s*[:#]?\s*([A-Za-z0-9\s-]+)/i,
      /(?:room|rm\.?)\s*(\d+[A-Za-z]?)/i,
    ];
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }
    return undefined;
  }

  function detectCategory(text) {
    const categoryKeywords = {
      exam: ['exam', 'midterm', 'final', 'test', 'quiz', 'assessment'],
      class: ['lecture', 'class', 'lab', 'section', 'seminar', 'workshop'],
      meeting: ['meeting', 'conference', 'call', 'sync', 'standup'],
      appointment: ['appointment', 'consultation', 'office hours', 'tutorial'],
      deadline: ['deadline', 'due', 'submission', 'homework', 'assignment', 'project'],
      work: ['shift', 'work', 'job'],
    };
    const lower = text.toLowerCase();
    for (const [category, keywords] of Object.entries(categoryKeywords)) {
      if (keywords.some(kw => lower.includes(kw))) {
        return category;
      }
    }
    return 'personal';
  }

  function parseTime(text) {
    let startTime = '';
    let endTime = '';

    // Time range
    const rangeMatch = text.match(/(\d{1,2}:\d{2})\s*(AM|PM|am|pm)?\s*[–—-]\s*(\d{1,2}:\d{2})\s*(AM|PM|am|pm)?/i);
    if (rangeMatch) {
      startTime = rangeMatch[1];
      const startPeriod = rangeMatch[2];
      endTime = rangeMatch[3];
      const endPeriod = rangeMatch[4];
      const hour1 = parseInt(startTime.split(':')[0]);
      const hour2 = parseInt(endTime.split(':')[0]);
      if (startPeriod) {
        startTime = `${startTime} ${startPeriod.toUpperCase()}`;
      } else if (hour1 >= 7 && hour1 < 12) {
        startTime = `${startTime} AM`;
      } else {
        startTime = `${startTime} PM`;
      }
      if (endPeriod) {
        endTime = `${endTime} ${endPeriod.toUpperCase()}`;
      } else if (hour2 >= 1 && hour2 <= 12) {
        endTime = `${endTime} PM`;
      } else {
        endTime = `${endTime} PM`;
      }
      return { startTime: to12HourTime(startTime), endTime: to12HourTime(endTime) };
    }

    // Single time
    const singleMatch = text.match(/(\d{1,2}:\d{2})\s*(AM|PM|am|pm)?/i);
    if (singleMatch) {
      startTime = singleMatch[1];
      if (singleMatch[2]) {
        startTime = `${startTime} ${singleMatch[2].toUpperCase()}`;
      } else {
        const hour = parseInt(startTime.split(':')[0]);
        if (hour >= 7 && hour < 12) {
          startTime = `${startTime} AM`;
        } else {
          startTime = `${startTime} PM`;
        }
      }
      return { startTime: to12HourTime(startTime), endTime: '' };
    }
    return { startTime: '', endTime: '' };
  }

  /**
   * Main entry point. Parses raw schedule text into structured events.
   * @param {string} text - Raw schedule text.
   * @returns {{ events: Array<{title: string, date: string, startTime: string, endTime?: string, location?: string, category: string}> }}
   */
  function parseScheduleText(text) {
    const events = [];
    const seenEvents = new Set();

    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const fullText = lines.join(' ');

    const datePatterns = [
      /((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4})/gi,
      /((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s*\d{4})/gi,
      /(\d{1,2}\/\d{1,2}\/\d{2,4})/g,
      /(\d{4}-\d{2}-\d{2})/g,
    ];

    // Primary strategy: date-driven line scanning
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      let foundDate = null;

      for (const pattern of datePatterns) {
        pattern.lastIndex = 0;
        const match = pattern.exec(line);
        if (match && match[1]) {
          const normalized = normalizeDate(match[1]);
          if (normalized) {
            foundDate = normalized;
            break;
          }
        }
      }
      if (!foundDate) continue;

      const contextWindow = [lines[i - 1] || '', line, lines[i + 1] || ''].join(' ');
      const { startTime, endTime } = parseTime(contextWindow);

      let title = '';
      if (i > 0) {
        const prevLine = lines[i - 1];
        const prevHasDate = datePatterns.some(p => { p.lastIndex = 0; return p.test(prevLine); });
        if (!prevHasDate && prevLine.length > 2 && prevLine.length < 100) {
          title = prevLine;
        }
      }
      if (!title) {
        title = line
          .replace(/\d{4}-\d{2}-\d{2}/g, '')
          .replace(/(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}/gi, '')
          .replace(/(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s*\d{4}/gi, '')
          .replace(/\d{1,2}\/\d{1,2}\/\d{2,4}/g, '')
          .replace(/\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*[–—-]\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?/gi, '')
          .replace(/\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?/gi, '')
          .replace(/^[–—•\s]+|[–—•\s]+$/g, '')
          .replace(/\s+/g, ' ')
          .trim();
      }
      if (!title && i < lines.length - 1) {
        const nextLine = lines[i + 1];
        const nextHasDate = datePatterns.some(p => { p.lastIndex = 0; return p.test(nextLine); });
        if (!nextHasDate && nextLine.length > 2 && nextLine.length < 100) {
          title = nextLine;
        }
      }

      title = title
        .replace(/^(exam|test|quiz|midterm|final)\s*(\d+)?\s*[:–—-]\s*/i, '')
        .replace(/^\d+\.\s*/, '')
        .replace(/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*/i, '')
        .trim();

      if (!title || title.length < 2) continue;

      const location = extractLocation(contextWindow);
      const category = detectCategory(title + ' ' + contextWindow);

      const eventKey = `${title.toLowerCase()}|${foundDate}`;
      if (seenEvents.has(eventKey)) continue;
      seenEvents.add(eventKey);

      events.push({
        title: title,
        date: foundDate,
        startTime: startTime,
        endTime: endTime || undefined,
        location: location,
        category: category,
      });
    }

    // Secondary keyword-driven strategy for exams, deadlines, etc.
    const keywordPatterns = [
      { pattern: /(Midterm\s*(?:Exam\s*)?[\dIV]*)/gi, category: 'exam' },
      { pattern: /(Final\s*Exam)/gi, category: 'exam' },
      { pattern: /(Quiz\s*[\dIV]*)/gi, category: 'exam' },
      { pattern: /(Test\s*[\dIV]*)/gi, category: 'exam' },
      { pattern: /(Project\s*[\dIV]*)/gi, category: 'deadline' },
      { pattern: /(Homework\s*[\dIV]*)/gi, category: 'deadline' },
      { pattern: /(Assignment\s*[\dIV]*)/gi, category: 'deadline' },
      { pattern: /(Office\s*Hours)/gi, category: 'appointment' },
      { pattern: /(Lecture)/gi, category: 'class' },
      { pattern: /(Lab)/gi, category: 'class' },
    ];

    for (const { pattern, category } of keywordPatterns) {
      pattern.lastIndex = 0;
      let match;
      while ((match = pattern.exec(fullText)) !== null) {
        const matchStart = match.index;
        const matchEnd = matchStart + match[0].length;
        const contextStart = Math.max(0, matchStart - 200);
        const contextEnd = Math.min(fullText.length, matchEnd + 200);
        const context = fullText.slice(contextStart, contextEnd);

        let foundDate = null;
        for (const datePattern of datePatterns) {
          datePattern.lastIndex = 0;
          const dateMatch = datePattern.exec(context);
          if (dateMatch && dateMatch[1]) {
            const normalized = normalizeDate(dateMatch[1]);
            if (normalized) {
              foundDate = normalized;
              break;
            }
          }
        }
        if (!foundDate) continue;

        const { startTime, endTime } = parseTime(context);
        const title = match[0].trim();
        const eventKey = `${title.toLowerCase()}|${foundDate}`;
        if (seenEvents.has(eventKey)) continue;
        seenEvents.add(eventKey);

        events.push({
          title: title,
          date: foundDate,
          startTime: startTime,
          endTime: endTime || undefined,
          location: extractLocation(context),
          category: category,
        });
      }
    }

    events.sort((a, b) => a.date.localeCompare(b.date));
    return { events: events };
  }

  // Utility helpers for presentation (optional but convenient for website use)
  function groupByDate(items) {
    return items.reduce((acc, item) => {
      const date = item.date;
      if (!acc[date]) acc[date] = [];
      acc[date].push(item);
      return acc;
    }, {});
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  function formatTime(timeStr) {
    if (!timeStr) return '';
    if (timeStr.match(/AM|PM/i)) {
      return timeStr.toUpperCase();
    }
    const parts = timeStr.split(':').map(Number);
    const hours = parts[0];
    const minutes = parts[1] || 0;
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  }

  function getCategoryColor(category) {
    const colors = {
      exam: '#dc2626',
      class: '#6366f1',
      meeting: '#8b5cf6',
      appointment: '#ec4899',
      deadline: '#f59e0b',
      work: '#f59e0b',
      personal: '#10b981',
      imported: '#64748b',
    };
    return colors[category] || colors.personal;
  }

  return {
    parseScheduleText: parseScheduleText,
    groupByDate: groupByDate,
    formatDate: formatDate,
    formatTime: formatTime,
    getCategoryColor: getCategoryColor,
    // Internal helpers exposed for advanced use or testing
    _normalizeDate: normalizeDate,
    _parseTime: parseTime,
    _detectCategory: detectCategory,
  };
}));
