# Publish to GitHub

The local release repository has already been initialized and committed.

1. Create a new public GitHub repository named `thesis-steganalysis`.
2. Copy the repository HTTPS URL, then run:

```powershell
cd D:\thesis\release\thesis-steganalysis
git remote add origin https://github.com/<your-username>/thesis-steganalysis.git
git push -u origin main
```

After the push succeeds, replace `<你的用户名>` in `GitHub开源平台提交说明.docx` with the real GitHub username if the college requires the final URL inside the document.
