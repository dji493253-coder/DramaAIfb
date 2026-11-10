import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const browserExecutable = process.env.CHROME || '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const frames = process.argv.slice(2).map(Number);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});
const comp = await selectComposition({serveUrl, id: 'EP', browserExecutable, chromiumOptions: {gl: 'swangle'}});
for (const f of frames) {
  const t0 = Date.now();
  await renderStill({composition: comp, serveUrl, frame: f, output: `out/stills/f${String(f).padStart(5, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 85, browserExecutable, scale: 0.5, chromiumOptions: {gl: 'swangle'}});
  console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
}
