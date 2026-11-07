/**
 * Ground Truth decks: put a part's frames on its frames slide in one run.
 *
 * The "Slide frames" GitHub workflow draws every Polka and Waltz part from the planner as JPEGs and
 * lists them in deck/frames.json on GitHub Pages. fillFrames() reads that list, finds the slide whose
 * header is the part's name ("5 · Theme 2: Turning Gears") and that has no table (the frames slide,
 * not its measure table), removes the old frames on it, and lays the new ones out as big as they fit:
 * a 10pt page margin, 8pt gaps, equal squares, each row centered, rows spread down the page.
 *
 * Old frames are pictures an earlier run placed, plus square pictures below the header band (frames
 * are square, so diagrams, photos and other non-square pictures are left alone). Text boxes are never
 * touched, so captions placed by hand stay where they are.
 *
 * Install: paste this file into an Apps Script project that can open the decks (the comparison
 * script already has the Slides scope and UrlFetchApp). Preview first; it changes nothing and logs
 * which slide it found, what it would remove and how it would lay the frames out:
 *   previewFrames('5 · Theme 2: Turning Gears');          // every deck for that dance
 *   fillFrames('5 · Theme 2: Turning Gears');
 *   fillFrames('9 · Triumphant grid crossing', FRAME_DECKS.polkaGT);  // one deck only
 */
const FRAMES_URL = 'https://ahannum.github.io/opening-2027/deck/frames.json';
const FRAME_DECKS = {
  polkaGT: '1Ezgd0IjRn6hVH9Cl82wFNgZOM_e7ImAyuUzWlN7bXyU',
  polkaWIP: '1aOSv2W6ahab-swyGb3a97YeJGdMW7UDpfr3QN6xrTLA',
  waltzWIP: '1nwlxmbur9z_Q-gdONiVpXWb5HAoBX6iU06l-yVQ-Y_M',
  waltzPublic: '1Mi6bg3E81TKhUepr0r_7uvpa856pUo3dvHjQBszMLmY',
};
const FRAMES_TAG = 'auto-frames';

function previewFrames(partName, deckId) {
  fillFrames(partName, deckId, { dryRun: true });
}

function fillFrames(partName, deckId, options) {
  const dryRun = Boolean(options && options.dryRun);
  const manifest = JSON.parse(UrlFetchApp.fetch(FRAMES_URL + '?t=' + Date.now()).getContentText());
  const story = manifest.stories.find(function (item) { return item.name === partName; });
  if (!story) throw new Error('No part named "' + partName + '" in frames.json. Parts: ' + manifest.stories.map(function (s) { return s.name; }).join(' | '));
  const blobs = story.frames.map(function (frame) { return UrlFetchApp.fetch(manifest.base + frame.src).getBlob(); });
  const decks = deckId ? [deckId] : story.section === 'Waltz'
    ? [FRAME_DECKS.waltzPublic, FRAME_DECKS.waltzWIP]
    : [FRAME_DECKS.polkaGT, FRAME_DECKS.polkaWIP];
  decks.forEach(function (id) {
    const deck = SlidesApp.openById(id);
    const slide = framesSlide_(deck, partName);
    if (!slide) {
      Logger.log('%s: no frames slide titled "%s"', deck.getName(), partName);
      return;
    }
    const slideNumber = deck.getSlides().indexOf(slide) + 1;
    Logger.log('%s, slide %s (%s):', deck.getName(), slideNumber, slide.getObjectId());
    placeFrames_(deck, slide, blobs, dryRun);
  });
}

// The slide carrying the part's name with no table on it.
function framesSlide_(deck, partName) {
  return deck.getSlides().find(function (slide) {
    const elements = slide.getPageElements();
    const hasTable = elements.some(function (el) { return el.getPageElementType() === SlidesApp.PageElementType.TABLE; });
    const named = elements.some(function (el) {
      return el.getPageElementType() === SlidesApp.PageElementType.SHAPE && el.asShape().getText().asString().indexOf(partName) >= 0;
    });
    return named && !hasTable;
  }) || null;
}

function isOldFrame_(image) {
  const w = image.getWidth(), h = image.getHeight();
  return image.getDescription() === FRAMES_TAG || (image.getTop() >= 60 && Math.abs(w - h) <= 0.03 * Math.max(w, h));
}

function placeFrames_(deck, slide, blobs, dryRun) {
  const box = function (el) { return Math.round(el.getWidth()) + 'x' + Math.round(el.getHeight()) + ' at ' + Math.round(el.getLeft()) + ',' + Math.round(el.getTop()); };
  slide.getImages().forEach(function (image) {
    const old = isOldFrame_(image);
    Logger.log('  %s picture %s', old ? (dryRun ? 'would remove' : 'removing') : 'keeping', box(image));
    if (old && !dryRun) image.remove();
  });
  const W = deck.getPageWidth(), H = deck.getPageHeight(), M = 10, G = 8;
  // Frames start under the header band and any text near the top (like the "Formation:" line).
  let top = 74;
  slide.getShapes().forEach(function (shape) {
    if (shape.getTop() < 200 && shape.getText().asString().trim()) top = Math.max(top, shape.getTop() + shape.getHeight() + 6);
  });
  const n = blobs.length;
  let best = { cols: 1, size: 0 };
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    const size = Math.min((W - 2 * M - (cols - 1) * G) / cols, (H - top - M - (rows - 1) * G) / rows);
    if (size > best.size) best = { cols: cols, size: size };
  }
  const cols = best.cols, size = Math.floor(best.size), rows = Math.ceil(n / cols);
  const rowGap = rows > 1 ? (H - top - M - rows * size) / (rows - 1) : 0;
  Logger.log('  %s %s frames: %s per row, %spt squares, from y=%s', dryRun ? 'would place' : 'placing', n, cols, size, Math.round(top));
  if (dryRun) return;
  blobs.forEach(function (blob, i) {
    const row = Math.floor(i / cols), inRow = Math.min(cols, n - row * cols), col = i % cols;
    const rowWidth = inRow * size + (inRow - 1) * G;
    const image = slide.insertImage(blob);
    image.setWidth(size).setHeight(size);
    image.setLeft((W - rowWidth) / 2 + col * (size + G));
    image.setTop(top + row * (size + rowGap));
    image.setDescription(FRAMES_TAG);
  });
}
