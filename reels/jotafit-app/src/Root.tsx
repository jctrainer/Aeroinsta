import React from 'react';
import {Composition} from 'remotion';
import {Reel, TOTAL} from './Reel';
import {Narrado, TOTAL_NARRADO} from './Narrado';

export const Root: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={TOTAL} fps={30} width={1080} height={1920} />
    <Composition id="Narrado" component={Narrado} durationInFrames={TOTAL_NARRADO} fps={30} width={1080} height={1920} />
  </>
);
