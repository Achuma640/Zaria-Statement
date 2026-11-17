# Receipt uploader setup (about 5 minutes, once)
1. In Google Drive signed in as the treasurer account, go to script.google.com > New project. Paste `ReceiptUploader.gs`.
2. Project Settings > Script properties > add `UPLOAD_CODE` = a code of your choice (share it only with treasurers).
3. Deploy > New deployment > Web app. Execute as: **Me**. Who has access: **Anyone**. Deploy and approve the permissions (Drive + Sheets).
4. Copy the Web app URL (ends in /exec) into `SCRIPT_URL` in `receipt-upload-w4k8/index.html`.
Files go to Drive folder "Zaria Village Receipts"; each upload adds a row to the Sheet tab "Receipt Files".
