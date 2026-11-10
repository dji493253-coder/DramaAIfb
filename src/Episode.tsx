import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise2D} from '@remotion/noise';
import data from '../data/ep01.json';

type Shot = (typeof data.shots)[number] & {punches?: {at: number; to: number}[]; shake?: number};

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background: 'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 48%, rgba(0,0,0,0.30) 78%, rgba(0,0,0,0.62) 100%)',
      pointerEvents: 'none',
    }}
  />
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const x = Math.floor(random(`gx${frame}`) * 400);
  const y = Math.floor(random(`gy${frame}`) * 400);
  return (
    <AbsoluteFill style={{mixBlendMode: 'overlay', opacity: 0.16, overflow: 'hidden', pointerEvents: 'none'}}>
      <Img src={staticFile('grain.png')} style={{width: 1700, height: 2500, objectFit: 'cover', transform: `translate(${-x}px, ${-y}px)`}} />
    </AbsoluteFill>
  );
};

const ShotView: React.FC<{s: Shot; last: boolean}> = ({s, last}) => {
  const frame = useCurrentFrame();
  const fps = data.fps;
  const p = interpolate(frame, [0, s.dur], [0, 1], {extrapolateRight: 'clamp'});
  let scale = s.zoom[0] + (s.zoom[1] - s.zoom[0]) * Easing.inOut(Easing.sin)(p);
  (s.punches || []).forEach((pu) => {
    const f0 = Math.round(pu.at * fps);
    const k = interpolate(frame, [f0, f0 + 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
    scale *= 1 + (pu.to - 1) * k;
  });
  if (s.trans === 'flash') {
    scale *= 1 + 0.05 * interpolate(frame, [0, 6], [1, 0], {extrapolateRight: 'clamp'});
  }
  const amp = s.shake || 0;
  const dx = amp ? noise2D('sx', frame * 0.4, 0) * amp * 4 : 0;
  const dy = amp ? noise2D('sy', frame * 0.4, 9) * amp * 4 : 0;

  let black = 0;
  if (s.trans === 'dip') black = interpolate(frame, [0, 6], [1, 0], {extrapolateRight: 'clamp'});
  const fo = last ? 8 : s.fadeOut;
  if (fo) black = Math.max(black, interpolate(frame, [s.dur - fo, s.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const white = s.trans === 'flash' ? interpolate(frame, [0, 7], [0.95, 0], {extrapolateRight: 'clamp'}) : 0;

  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <AbsoluteFill style={{filter: 'contrast(1.07) saturate(1.04) brightness(0.97)'}}>
        <OffthreadVideo
          src={staticFile(`prep/${s.clip}.mp4`)}
          startFrom={Math.round(s.in * fps)}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: `${s.focal[0] * 100}% ${s.focal[1] * 100}%`,
            transform: `translate(${dx}px, ${dy}px) scale(${scale})`,
          }}
        />
      </AbsoluteFill>
      {white > 0 && <AbsoluteFill style={{background: '#fff', opacity: white}} />}
      {black > 0 && <AbsoluteFill style={{background: '#000', opacity: black}} />}
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const a = (from: number, to: number) => interpolate(frame, [from, to], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const out = interpolate(frame, [data.endCard - 10, data.endCard], [1, 0], {extrapolateLeft: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#050403', alignItems: 'center', justifyContent: 'center', opacity: out}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, rgba(160,120,60,0.16), rgba(0,0,0,0) 62%)'}} />
      <div style={{textAlign: 'center', transform: 'translateY(-40px)'}}>
        <div style={{fontFamily: 'Cinzel', fontWeight: 600, fontSize: 34, letterSpacing: 12, color: '#c9a86a', opacity: a(4, 20)}}>STORY BEHIND LIFE</div>
        <div style={{width: 380 * a(10, 34), height: 2, background: '#c9a86a', margin: '34px auto', opacity: 0.7}} />
        <div style={{fontFamily: 'Cinzel', fontWeight: 700, fontSize: 84, letterSpacing: 4, color: '#f0e2c4', opacity: a(14, 36), transform: `translateY(${(1 - a(14, 36)) * 18}px)`}}>RAHASIA</div>
        <div style={{fontFamily: 'Cinzel', fontWeight: 700, fontSize: 84, letterSpacing: 4, color: '#f0e2c4', opacity: a(20, 42), transform: `translateY(${(1 - a(20, 42)) * 18}px)`}}>20 TAHUN</div>
        <div style={{fontFamily: 'Cormorant Garamond', fontStyle: 'italic', fontWeight: 600, fontSize: 44, color: '#d7c3a0', marginTop: 60, opacity: a(40, 58)}}>Episode 2 segera hadir</div>
      </div>
    </AbsoluteFill>
  );
};

export const Episode: React.FC = () => {
  const shots = data.shots as Shot[];
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {shots.map((s, i) => (
        <Sequence key={s.id} from={s.from} durationInFrames={s.dur} layout="none">
          <ShotView s={s} last={i === shots.length - 1} />
        </Sequence>
      ))}
      <Sequence from={data.videoEnd} durationInFrames={data.endHold} layout="none">
        <AbsoluteFill style={{background: '#000'}} />
      </Sequence>
      <Sequence from={data.videoEnd + data.endHold} durationInFrames={data.endCard} layout="none">
        <EndCard />
      </Sequence>
      <Sequence from={0} durationInFrames={data.videoEnd} layout="none">
        <Vignette />
        <Grain />
      </Sequence>
      <Audio src={staticFile('audio/ep01_mix.wav')} />
    </AbsoluteFill>
  );
};
