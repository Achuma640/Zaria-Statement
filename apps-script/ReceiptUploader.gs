/**
 * Zaria Village: receipt uploader (Google Apps Script web app).
 * Runs as the treasurer's Google account, so files land in HER/HIS Drive and rows in the Sheet.
 * Setup: see apps-script/README.md. Set Script properties: UPLOAD_CODE (shared code for treasurers).
 */
var SHEET_ID  = '1E9q6ot6hEpbIsJujR72FJ24i1eZcH5SWNAk930pMRfY';
var FOLDER_ID = '1i4PLoXfTX_S-Dsp-kzpbd0-m1KqLIHKL';   // Drive folder "Zaria Village Receipts"
var TAGS = ['Bush clearing & grounds','Pool & club house','Security & guard houses','Caretaker & salaries',
            'Legal, registration & admin','Utilities & repairs','Road construction & works','AGM & events',
            'Refund / transfer to resident','Other'];

function out_(o){ return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function codeOk_(c){ var k = PropertiesService.getScriptProperties().getProperty('UPLOAD_CODE'); return !!k && String(c||'') === k; }
function num_(v){ return typeof v === 'number' ? v : parseFloat(String(v||'0').replace(/,/g,'')) || 0; }

function doGet(e){
  var p = (e && e.parameter) || {};
  if (!codeOk_(p.code)) return out_({ok:false, error:'bad code'});
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var rf = ss.getSheetByName('Receipt Files').getDataRange().getValues();
  if (p.file) {   // send one saved receipt back as base64 so the report can show it with no Google sign-in
    var okId = false;
    for (var k = 1; k < rf.length; k++) if (String(rf[k][8]) === String(p.file)) { okId = true; break; }
    if (!okId) return out_({ok:false, error:'receipt not found'});
    try { var bl = DriveApp.getFileById(p.file).getBlob();
      return out_({ok:true, mime:bl.getContentType(), data:Utilities.base64Encode(bl.getBytes())});
    } catch (er) { return out_({ok:false, error:'file missing from Drive'}); }
  }
  var tx = ss.getSheetByName('Transactions').getDataRange().getDisplayValues();
  var have = {};
  for (var i = 1; i < rf.length; i++) { var r = String(rf[i][1]); have[r] = (have[r]||0) + 1; }
  var pays = [];
  for (var j = tx.length - 1; j >= 1 && pays.length < 150; j--) {
    var t = tx[j];
    if (t[2] === 'Payment') pays.push({date:t[0], ref:t[1], amount:num_(t[3]), payee:t[5], note:t[6], cat:t[9], files:have[t[1]]||0});
  }
  return out_({ok:true, payments:pays, tags:TAGS});
}

function doPost(e){
  var lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    var b = JSON.parse(e.postData.contents);
    if (!codeOk_(b.code)) return out_({ok:false, error:'bad code'});
    var ss = SpreadsheetApp.openById(SHEET_ID);
    var tx = ss.getSheetByName('Transactions').getDataRange().getDisplayValues(), row = null;
    for (var i = 1; i < tx.length; i++) if (tx[i][1] === b.ref && tx[i][2] === 'Payment') { row = tx[i]; break; }
    if (!row) return out_({ok:false, error:'payment ref not found'});
    var ext = b.mime === 'application/pdf' ? 'pdf' : 'jpg';
    var tag = String(b.tag||'Other').replace(/[\\\/:*?"<>|]/g,' ').slice(0,60);
    var base = b.ref + ' - ' + tag, name = base + '.' + ext, n = 2, folder = DriveApp.getFolderById(FOLDER_ID);
    while (folder.getFilesByName(name).hasNext()) name = base + ' (' + (n++) + ').' + ext;
    var blob = Utilities.newBlob(Utilities.base64Decode(b.data), b.mime, name);
    var f = folder.createFile(blob);
    f.setDescription('Payment ' + b.ref + ' | ' + row[0] + ' | KES ' + row[3] + ' | ' + row[5] + ' | tag: ' + tag + ' | ' + (b.note||''));
    ss.getSheetByName('Receipt Files').appendRow([new Date(), b.ref, tag, (b.note||'') || row[5], num_(row[3]), name, f.getUrl(), String(b.by||'').slice(0,40), f.getId()]);
    return out_({ok:true, name:name, link:f.getUrl()});
  } catch (err) { return out_({ok:false, error:String(err)}); }
  finally { lock.releaseLock(); }
}
