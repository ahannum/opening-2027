# Opening 2027

Interactive formation planner for Stanford Viennese Ball Opening Committee

## Use

Open `index.html` in a browser.

## Features

- Follow a four-step planning workflow: choose who moves (always pinned at the top), choose a formation, fine-tune, and capture a shot. Controls are grouped into Formation, Storyboard, and More tabs.
- Switch arrow keys between Circle and Straight, and straight step size between Short, ½ Tape, and Full Tape, from the pinned bar (or press M / H). The same bar switches Snap to dots / Free (F) and Couples Together / Split (P).
- Quick arrow-key presses in different directions queue up and run in order instead of cancelling each other.
- Drag and arrange 16 couple tokens.
- Show joined couples as either lead/follow halves or a single partner token.
- Split joined couples into separate lead and follow tokens, then join them again.
- Select and move every lead or every follow independently; any preset can apply to just that group.
- Select every odd-numbered or even-numbered couple at once, including both partners when split.
- Move selected or all tokens clockwise/counterclockwise around the line of dance.
- Step selected or all tokens between the outer tape, ¼ ring, ½ ring, ¾ ring, inner tape, and center ring. The pinned In/Out switch (or Q) chooses ¼ Ring steps or bigger ½ Ring steps that skip the ¼ and ¾ rings.
- Face joined lead/follow symbols inward or outward along either a circle or the nearest edge of a square.
- Save custom formations and play custom paths with constrained movement.
- Capture formation screenshots into a reorderable stop-motion storyboard, reopen and edit existing shots, and step through them.
- Save the complete editable storyboard as one project file and reopen it later from Downloads. Supported browsers also keep that project file and individual PNGs in a chosen folder.
- Each shot keeps its own title and subheading. Click a shot and edit its text; the change saves to that shot (and its picture) automatically.
- Control the GIF: size (360, 480, 720, or 1080 px), time per frame, a per-shot hold time, extra time on the last frame, and loop forever or play once. Playback in the planner uses the same timing, and the settings save with the storyboard.
- Save a storyboard (project file, PNG frames, and GIF) straight to Google Drive and open it again from Drive in any browser — no Drive for desktop needed.
- Copy current positions as JSON.
- Pick a saved configuration (Formation tab → Saved configurations), such as the Unfurling Pyramid: 5 frames, one four-count measure each. Configurations live in `STORY_PRESETS` in `index.html`.
- Copy any frame to paste into Google Slides, or save every frame as a numbered PNG. Frames render at 2160 px, and storyboards saved with smaller frames are redrawn at that size when opened. GIFs go up to 2160 px.
- Present a story in `present.html`: pick a saved configuration, press Present in the planner's Storyboard tab, or open a saved storyboard file, then step with the arrow keys, Space, a clicker, or the buttons. F goes fullscreen. Keep `present.html` next to `index.html`; it uses the planner to draw the configurations.

## GitHub Pages

This is a static app. GitHub Pages can serve it directly from the repository root.

## Google Drive setup (one time)

Drive saving signs people in with Google from the browser, so the planner needs its own Google Cloud OAuth client. Until `GOOGLE_DRIVE_CONFIG.clientId` is filled in, the Drive buttons explain that Drive isn't connected yet.

1. Go to <https://console.cloud.google.com/>, create a project (e.g. "Opening 2027 Planner"), and note its **project number** on the project dashboard.
2. **APIs & Services → Library**: enable **Google Drive API** and **Google Picker API**.
3. **APIs & Services → OAuth consent screen**: choose **External**, fill in the app name and your email, and add the scope `.../auth/drive.file`. While the app is in **Testing**, add each committee member's Google account under **Test users** (up to 100). Testing-mode sign-ins expire after 7 days, so people may need to sign in again weekly; publish the app to avoid that.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**: type **Web application**. Under **Authorized JavaScript origins**, add `https://ahannum.github.io` (and `http://localhost:8000` if you test locally with `python3 -m http.server`). Copy the **client ID**.
5. **Credentials → Create credentials → API key**. Restrict it to **HTTP referrers** `https://ahannum.github.io/*` and to the **Google Picker API**. Copy the key.
6. In `index.html`, fill in `GOOGLE_DRIVE_CONFIG`:

   ```js
   const GOOGLE_DRIVE_CONFIG = {
     clientId: "1234567890-abc123.apps.googleusercontent.com",
     apiKey: "AIza...",
     appId: "1234567890", // the project number
   };
   ```

7. Commit and push. Drive saving only works from the GitHub Pages site (or another allowed origin), not from opening `index.html` as a local file.

The client ID and a referrer-restricted API key are meant to be public, so it's fine for them to be in the repo.

How it works:

- **Save to Drive** creates `Opening 2027 Storyboards / <story name>` in the signed-in person's Drive. Inside it saves `storyboard.json`, one PNG per shot, and the GIF. Saving again replaces those files.
- **Open from Drive** lists storyboards that person saved from the planner. **Browse Drive…** opens Google's file picker, so people can open a `storyboard.json` a teammate shared with them.
- The planner uses the `drive.file` permission, so it can only see files it created or that someone picks. It can't read the rest of anyone's Drive.
- If your Stanford Google account blocks unapproved apps, use a personal Gmail account instead.
