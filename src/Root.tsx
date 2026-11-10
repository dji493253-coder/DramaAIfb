import React from 'react';
import {Composition} from 'remotion';
import '@fontsource/cinzel/600.css';
import '@fontsource/cinzel/700.css';
import '@fontsource/cormorant-garamond/500.css';
import '@fontsource/cormorant-garamond/600-italic.css';
import {Episode} from './Episode';
import data from '../data/ep01.json';

export const Root: React.FC = () => (
  <Composition
    id="EP"
    component={Episode}
    width={data.width}
    height={data.height}
    fps={data.fps}
    durationInFrames={data.total}
  />
);
