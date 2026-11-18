import React from 'react';
import {Composition} from 'remotion';
import {Reel, TOTAL} from './Reel';
import {Narrado, TOTAL_NARRADO} from './Narrado';
import {Curto, TOTAL_CURTO} from './Curto';
import {Tour, TOTAL_TOUR} from './Tour';
import {Capa} from './Capa';

export const Root: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={TOTAL} fps={30} width={1080} height={1920} />
    <Composition id="Narrado" component={Narrado} durationInFrames={TOTAL_NARRADO} fps={30} width={1080} height={1920} />
    <Composition id="Curto" component={Curto} durationInFrames={TOTAL_CURTO} fps={30} width={1080} height={1920} />
    <Composition id="Tour" component={Tour} durationInFrames={TOTAL_TOUR} fps={30} width={1080} height={1920} />
    <Composition id="Capa" component={Capa} durationInFrames={1} fps={30} width={1080} height={1920} defaultProps={{v: 'tour' as const}} />
  </>
);
