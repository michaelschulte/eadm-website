# Adding a newsletter

New newsletter issues reach the EADM website through a **pull request**
on GitHub: you upload the PDF, Michael reviews it, and once the pull
request is merged the site rebuilds and publishes itself within a few
minutes. Everything below is done in the browser on github.com; you do
not need to install anything.

## 1. Name the PDF

Name the file after the month of the issue:

```
EADM-Newsletter-YEAR-MONTH.pdf
```

for example `EADM-Newsletter-2026-11.pdf` for the November 2026 issue.
Use the two-digit month and no spaces.

## 2. Upload it

1. Go to <https://github.com/michaelschulte/eadm-website> and sign in.
2. Open the `files` folder, then the folder for the year and month
   (e.g. `files/2026/11/`).
   If that folder does not exist yet, upload the file from inside
   `files/` and type the folder path in front of the file name.
3. Choose **Add file → Upload files** and drag in the PDF.

## 3. Open the pull request

1. When saving ("Commit changes"), describe the change in a sentence,
   e.g. *Add the November 2026 newsletter*, and choose **Create a new
   branch for this commit and start a pull request**. Without write
   access to the repository, GitHub first creates a copy (a "fork") for
   you; this is expected.
2. Click **Create pull request**. Michael reviews and merges it;
   the website updates a few minutes later.

You do not need to edit the newsletter archive or write an announcement
for the News page; both are taken care of separately.

Not sure about something? Open the pull request anyway and describe
what you would like to add; Michael will help finish it.
