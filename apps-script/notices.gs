/**
 * Zaria notices: receives a notice from the Estate tab, adds it to the "Notices" tab (NOT approved),
 * and emails the committee a one-tap Approve / Reject link.
 * Setup: script.google.com > New project (separate from the receipt uploader) > paste this file > set COMMITTEE > Deploy > New deployment >
 * type "Web app", Execute as "Me", Who has access "Anyone" > copy the web app URL.
 */
const COMMITTEE = 'andy.chuma@gmail.com';   // comma-separated committee emails that receive notices
const TAB = 'Notices';
const SHEET_ID = '1E9q6ot6hEpbIsJujR72FJ24i1eZcH5SWNAk930pMRfY';

function doPost(e) {
  const p = e.parameter || {};
  const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB);
  const token = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
  const who = [p.name, p.phone, p.email].filter(String).join(' | ');
  const note = [p.guests ? 'Expected guests: ' + p.guests + '.' : '', p.details || ''].join(' ').trim();
  const title = p.kind || 'Notice';
  const when = p.date ? new Date(p.date + 'T00:00:00') : '';
  sh.appendRow([false, when, p.start || '', p.where || '', title, p.contact || '', note, who, token, 'Pending']);
  const url = ScriptApp.getService().getUrl();
  const link = function (a) { return url + '?a=' + a + '&t=' + token; };
  const body = 'New notice from the Estate tab\n\n' +
    'Type: ' + title + '\nDate: ' + (p.date || '') + '\nStart: ' + (p.start || '') + '\nWhere: ' + (p.where || '') +
    '\nPlot: ' + (p.contact || '') + '\nGuests: ' + (p.guests || '') + '\nDetails: ' + (p.details || '') +
    '\nFrom: ' + who + '\n\nAPPROVE (shows to residents): ' + link('approve') +
    '\n\nREJECT: ' + link('reject') + '\n\nIt appears in the app at the next update, within about 30 minutes of approval.';
  MailApp.sendEmail(COMMITTEE, 'Zaria notice to approve: ' + title + ' ' + (p.date || ''), body);
  return ContentService.createTextOutput('ok');
}

function doGet(e) {
  const a = (e.parameter || {}).a, t = (e.parameter || {}).t;
  const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB);
  const tokens = sh.getRange(1, 9, sh.getLastRow(), 1).getValues().map(function (r) { return String(r[0]); });
  const i = t ? tokens.indexOf(t) : -1;
  if (i < 1) return HtmlService.createHtmlOutput('<p>Link not found or already used.</p>');
  const row = i + 1;
  if (a === 'approve') { sh.getRange(row, 1).setValue(true); sh.getRange(row, 10).setValue('Approved'); }
  else if (a === 'reject') { sh.getRange(row, 1).setValue(false); sh.getRange(row, 10).setValue('Rejected'); }
  else return HtmlService.createHtmlOutput('<p>Unknown action.</p>');
  return HtmlService.createHtmlOutput('<p style="font:20px sans-serif">' + (a === 'approve' ?
    'Approved. It will show in the Zaria app within about 30 minutes.' : 'Rejected. It will not be shown.') + '</p>');
}
