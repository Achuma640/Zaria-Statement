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
  if (p['form-name'] === 'subscribe') {
    const ss = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Subscribers');
    const em = String(p.email || '').trim();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) return ContentService.createTextOutput('bad');
    const em2 = String(p.email2 || '').trim();
    const ok2 = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em2);
    ss.appendRow([new Date(), String(p.plot || ''), p.name || '', em, p.phone || '', 'Agreed to estate emails', ok2 ? em2 : '']);
    return ContentService.createTextOutput('ok');
  }
  if (p['form-name'] === 'vote') {
    const vs = SpreadsheetApp.openById(SHEET_ID).getSheetByName('WorkerVotes');
    if (p.id && p.plot) vs.appendRow([new Date(), String(p.id), String(p.plot), String(p.dir) === '-1' ? -1 : 1]);
    return ContentService.createTextOutput('ok');
  }
  if (p['form-name'] === 'worker') {
    const ws = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Workers');
    if (!p.wname || !p.trade) return ContentService.createTextOutput('bad');
    const tk = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
    const nm = ws.getRange(1, 3, ws.getMaxRows(), 1).getValues();
    let wr = 2; while (wr <= nm.length && String(nm[wr - 1][0]).trim() !== '') wr++;
    if (wr > ws.getMaxRows()) ws.insertRowsAfter(ws.getMaxRows(), 20);
    ws.getRange(wr, 4).setNumberFormat('@');
    let ph = String(p.wphone || '').replace(/[^0-9]/g, '');
    if (ph.indexOf('254') === 0 && ph.length === 12) ph = '0' + ph.slice(3); else if (ph.length === 9) ph = '0' + ph;
    ws.getRange(wr, 1, 1, 9).setValues([[false, p.trade, p.wname, ph, p.note || '', p.plot || '', tk, 'Pending', p.name || '']]);
    const wl = function (a) { return ScriptApp.getService().getUrl() + '?a=' + a + '&t=' + tk; };
    try { MailApp.sendEmail(COMMITTEE, 'Zaria worker to approve: ' + p.wname + ' (' + p.trade + ')',
      'New worker recommendation\n\nTrade: ' + p.trade + '\nName: ' + p.wname + '\nPhone: ' + (p.wphone || '') + '\nNote: ' + (p.note || '') +
      '\nRecommended by plot ' + (p.plot || '') + ' ' + (p.name || '') + '\n\nAPPROVE (shows to residents): ' + wl('approve') + '\n\nREJECT: ' + wl('reject')); }
    catch (err) { ws.getRange(wr, 10).setValue('Email failed: ' + err); }
    return ContentService.createTextOutput('ok');
  }
  const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB);
  const token = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
  const who = [p.name, p.phone, p.email].filter(String).join(' | ');
  const note = [p.guests ? 'Expected guests: ' + p.guests + '.' : '', p.details || ''].join(' ').trim();
  const title = p.kind || 'Notice';
  const when = p.date ? new Date(p.date + 'T00:00:00') : '';
  // first free row, judged by the Title column (the Approved column holds ready-made tick boxes)
  const titles = sh.getRange(1, 5, sh.getMaxRows(), 1).getValues();
  let r = 2; while (r <= titles.length && String(titles[r - 1][0]).trim() !== '') r++;
  if (r > sh.getMaxRows()) sh.insertRowsAfter(sh.getMaxRows(), 20);
  sh.getRange(r, 1, 1, 10).setValues([[false, when, p.start || '', p.where || '', title, p.contact || '', note, who, token, 'Pending']]);
  const url = ScriptApp.getService().getUrl();
  const link = function (a) { return url + '?a=' + a + '&t=' + token; };
  const body = 'New notice from the Estate tab\n\n' +
    'Type: ' + title + '\nDate: ' + (p.date || '') + '\nStart: ' + (p.start || '') + '\nWhere: ' + (p.where || '') +
    '\nPlot: ' + (p.contact || '') + '\nGuests: ' + (p.guests || '') + '\nDetails: ' + (p.details || '') +
    '\nFrom: ' + who + '\n\nAPPROVE (shows to residents): ' + link('approve') +
    '\n\nREJECT: ' + link('reject') + '\n\nIt appears in the app at the next update, within about 30 minutes of approval.';
  try { MailApp.sendEmail(COMMITTEE, 'Zaria notice to approve: ' + title + ' ' + (p.date || ''), body); } catch (err) { sh.getRange(r, 11).setValue('Email failed: ' + err); }
  return ContentService.createTextOutput('ok');
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function codeOk_(c) { const k = PropertiesService.getScriptProperties().getProperty('APPROVE_CODE'); return !!k && String(c || '') === k; }

function doGet(e) {
  const a = (e.parameter || {}).a, t = (e.parameter || {}).t;
  const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB);
  // Committee approval page: list pending notices / approve or reject one. Needs the APPROVE_CODE script property.
  if (a === 'list' || a === 'set') {
    if (!codeOk_((e.parameter || {}).code)) return json_({ ok: false, error: 'code' });
    if (a === 'list') {
      const v = sh.getRange(1, 1, sh.getLastRow(), 10).getDisplayValues(), out = [];
      for (let i = 1; i < v.length; i++) if (v[i][4]) out.push({ row: i + 1, approved: v[i][0] === 'TRUE', date: v[i][1], time: v[i][2], where: v[i][3], title: v[i][4], plot: v[i][5], note: v[i][6], by: v[i][7], status: v[i][9] });
      return json_({ ok: true, rows: out.reverse() });
    }
    const row = parseInt(e.parameter.r, 10), act = e.parameter.v;
    if (!(row >= 2) || String(sh.getRange(row, 5).getValue()).trim() === '') return json_({ ok: false, error: 'row' });
    sh.getRange(row, 1).setValue(act === 'approve'); sh.getRange(row, 10).setValue(act === 'approve' ? 'Approved' : 'Rejected');
    return json_({ ok: true });
  }
  const wsh = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Workers');
  if (t && wsh && wsh.getLastRow() > 1) {
    const wt = wsh.getRange(1, 7, wsh.getLastRow(), 1).getValues().map(function (r) { return String(r[0]); }), wi = wt.indexOf(t);
    if (wi >= 1) {
      if (a === 'approve') { wsh.getRange(wi + 1, 1).setValue(true); wsh.getRange(wi + 1, 8).setValue('Approved'); }
      else if (a === 'reject') { wsh.getRange(wi + 1, 1).setValue(false); wsh.getRange(wi + 1, 8).setValue('Rejected'); }
      else return HtmlService.createHtmlOutput('<p>Unknown action.</p>');
      return HtmlService.createHtmlOutput('<p style="font:20px sans-serif">' + (a === 'approve' ? 'Approved. It will be listed in the Zaria app within about 30 minutes.' : 'Rejected. It will not be listed.') + '</p>');
    }
  }
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

/** Run this once from the editor (select "authorize" in the toolbar, then Run) so Google asks for permission to send email. */
function authorize() {
  MailApp.sendEmail(COMMITTEE, 'Zaria notices script authorised', 'The notice approval emails will now be sent.');
  SpreadsheetApp.openById(SHEET_ID).getSheetByName(TAB).getRange(1, 1).getValue();
}
