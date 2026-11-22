import {Config} from '@remotion/cli/config';

// Used by `remotion studio` and the `remotion` CLI. `npm run render` (tools/render.mjs) passes the same values.
// PNG frames: JPEG at the default quality smears thin borders and fine textures.
Config.setVideoImageFormat('png');
Config.setCodec('h264');
Config.setCrf(16);
Config.setPixelFormat('yuv420p');
Config.setColorSpace('bt709');
Config.setOverwriteOutput(true);
