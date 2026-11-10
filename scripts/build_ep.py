#!/usr/bin/env python3
"""Bangun timeline (data/ep01.json) dan mix audio (public/audio/ep01_mix.wav) dari data/ep01_edit.json."""
import json, subprocess, re, os, sys
import numpy as np
from scipy.io import wavfile
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SR = 48000
edit = json.load(open('data/ep01_edit.json'))
FPS = edit['fps']
shots = edit['shots']
rng = np.random.default_rng(7)

# ---------- timeline (dalam frame) ----------
cur = 0
for s in shots:
    s['from'] = cur
    s['dur'] = max(1, round((s['out'] - s['in']) * FPS))
    cur += s['dur']
video_end = cur
end_start = video_end
total = video_end + edit['endHoldFrames'] + edit['endCardFrames']
for i, s in enumerate(shots):
    nxt = shots[i + 1] if i + 1 < len(shots) else None
    s['fadeOut'] = 4 if (nxt and nxt['trans'] == 'dip') else 0
    if i == len(shots) - 1: s['fadeOut'] = 0
out = {'fps': FPS, 'width': 1080, 'height': 1920, 'total': total, 'videoEnd': video_end,
       'endHold': edit['endHoldFrames'], 'endCard': edit['endCardFrames'], 'shots': shots}
json.dump(out, open('data/ep01.json', 'w'), indent=1)
T = total / FPS
N = int(T * SR) + SR
t_axis = np.arange(N) / SR
print(f'shots={len(shots)} video={video_end/FPS:.1f}s total={T:.1f}s')

# ---------- dialog ----------
def load_audio(clip):
    p = f'public/clips/{clip}.mp4'
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-'])
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)

def lufs(clip):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f'public/clips/{clip}.mp4', '-af', 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    m = re.findall(r'\n\s+I:\s+(-?\d+\.\d+) LUFS', r)
    return float(m[-1]) if m else -22.0

clips = {}
for c in sorted({s['clip'] for s in shots}):
    a = load_audio(c)
    g = min(7.0, max(-6.0, -20.0 - lufs(c)))  # samakan ke sekitar -20 LUFS
    clips[c] = (a, 10 ** (g / 20))

dlg = np.zeros((N, 2), dtype=np.float32)
for i, s in enumerate(shots):
    a, g = clips[s['clip']]
    g *= 10 ** (s.get('dialogGain', 0) / 20)
    n = int(round(s['dur'] / FPS * SR))
    i0 = int(round(s['in'] * SR))
    seg = a[i0:i0 + n].copy()
    if len(seg) < n: seg = np.vstack([seg, np.zeros((n - len(seg), 2), dtype=np.float32)])
    seg *= g
    f = int(0.012 * SR)
    prev = shots[i - 1] if i else None
    nxt = shots[i + 1] if i + 1 < len(shots) else None
    contiguous_prev = prev and prev['clip'] == s['clip'] and abs(prev['out'] - s['in']) < 0.02
    contiguous_next = nxt and nxt['clip'] == s['clip'] and abs(nxt['in'] - s['out']) < 0.02
    if not contiguous_prev: seg[:f] *= np.linspace(0, 1, f)[:, None]
    if not contiguous_next: seg[-f:] *= np.linspace(1, 0, f)[:, None]
    st = int(round(s['from'] / FPS * SR))
    dlg[st:st + n] += seg

# envelope dialog untuk ducking
mono = np.abs(dlg).mean(axis=1)
win = int(0.03 * SR)
env = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode='same'))
env = np.convolve(env, np.ones(int(0.18 * SR)) / int(0.18 * SR), mode='same')
env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)

# ---------- helper sintesis ----------
def tt(d): return np.arange(int(d * SR)) / SR
def add(buf, x, t0, gain=1.0):
    i = int(t0 * SR)
    if i < 0 or i >= len(buf): return
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * gain
def lp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return signal.sosfilt(signal.butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)

def thud(strength=1.0):
    t = tt(0.55)
    f = 38 + 70 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    x += lp(rng.standard_normal(len(t)), 220) * np.exp(-t * 30) * 0.5
    return x * strength

def boom():
    t = tt(2.2)
    f = 30 + 45 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    x += lp(rng.standard_normal(len(t)), 350) * np.exp(-t * 7) * 0.8
    return x

def whoosh(d=0.5, up=True):
    t = tt(d)
    x = bp(rng.standard_normal(len(t)), 500, 5500)
    e = np.sin(np.pi * t / d) ** 2
    if not up: e = e[::-1]
    return x * e * 0.5

def riser(d):
    t = tt(d)
    e = (t / d) ** 2.2
    f = 180 + 700 * (t / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    n = hp(rng.standard_normal(len(t)), 1200) * 0.5
    return (s + n) * e

def heartbeat(d, bpm=66, strength=0.7):
    x = np.zeros(int(d * SR) + SR)
    per = 60 / bpm
    k = 0
    while k * per < d:
        add(x, thud(strength), k * per)
        add(x, thud(strength * 0.55), k * per + 0.27)
        k += 1
    return x[:int(d * SR)]

def reverb(x, d=2.0, wet=0.35):
    t = tt(d)
    ir = rng.standard_normal(len(t)) * np.exp(-t * 2.8)
    ir = lp(ir, 3500)
    y = signal.fftconvolve(x, ir)[:len(x)]
    y *= np.abs(x).max() / (np.abs(y).max() + 1e-9)
    return x * (1 - wet) + y * wet

# ---------- musik ----------
tens = np.zeros(N)
for s in shots:
    a = int(s['from'] / FPS * SR); b = a + int(s['dur'] / FPS * SR)
    tens[a:b] = s['tension']
tens[int(video_end / FPS * SR):] = 0.35
tens = lp(tens, 0.4, 1)
tens = np.clip(tens, 0, 1)

chord = [55.0, 82.41, 110.0, 130.81]
pad = np.zeros(N)
for k, f in enumerate(chord):
    for det in (0.997, 1.003):
        ph = rng.uniform(0, 6.28)
        lfo = 1 + 0.004 * np.sin(2 * np.pi * (0.07 + 0.03 * k) * t_axis + ph)
        pad += np.sin(2 * np.pi * np.cumsum(f * det * lfo) / SR + ph) / 8
pad = lp(pad, 700)
sub = np.sin(2 * np.pi * 36.7 * t_axis) * 0.5
dis = (np.sin(2 * np.pi * 880 * t_axis) + np.sin(2 * np.pi * 932 * t_axis)) * 0.5
dis = lp(dis, 2500) * (tens ** 3)
air = lp(rng.standard_normal(N), 1800) * 0.03
music = (pad * (0.35 + 0.9 * tens) + sub * (0.15 + 0.35 * tens) + dis * 0.05 + air * (0.4 + tens)) * 0.22
# fade in/out
music *= np.clip(t_axis / 1.0, 0, 1)
music *= np.clip((T + 0.5 - t_axis) / 2.0, 0, 1)
music *= (1 - 0.65 * env)   # ducking saat bicara

# ---------- sfx ----------
sfx = np.zeros(N)
for s in shots:
    t0 = s['from'] / FPS
    d = s['dur'] / FPS
    if s.get('riser'): add(sfx, riser(d), t0, 0.55)
    if s.get('heartbeat'): add(sfx, heartbeat(d), t0, 0.55)
    if s.get('boom'): add(sfx, boom(), t0 - 0.02, 0.75)
    for th in s.get('thud', []): add(sfx, thud(1.0), t0 + th, 0.8)
    if s['trans'] == 'flash': add(sfx, whoosh(0.45), t0 - 0.35, 0.6); add(sfx, thud(0.8), t0, 0.6)
    elif s['trans'] == 'dip':  add(sfx, whoosh(0.5, up=False), t0 - 0.05, 0.35)
# sting akhir: hening singkat lalu dentuman + ekor
t_end = video_end / FPS
add(sfx, reverb(boom() * 1.0, 2.6, 0.5), t_end + 0.15, 0.9)
# kartu penutup: akor lembut
card = np.zeros(N)
t0 = t_end + edit['endHoldFrames'] / FPS
for f in (110.0, 164.81, 220.0, 329.63):
    seg = np.sin(2 * np.pi * f * tt(T - t0 + 1)) * 0.05
    seg *= np.clip(tt(T - t0 + 1) / 1.2, 0, 1) * np.clip((T - t0 + 0.6 - tt(T - t0 + 1)) / 1.5, 0, 1)
    add(card, seg, t0)

# reverb ringan pada bus sfx
sfx = reverb(sfx, 1.6, 0.2)

# ---------- mix ----------
mix = np.zeros((N, 2), dtype=np.float32)
mix += dlg * 0.9
bed = (music + card).astype(np.float32)
mix[:, 0] += bed + sfx.astype(np.float32) * 0.9
mix[:, 1] += np.roll(bed, 37) + sfx.astype(np.float32) * 0.9   # sedikit lebar stereo
mix = mix[:int(T * SR)]
pk = np.abs(mix).max()
mix = mix / max(1.0, pk * 1.05)
tmp = '/tmp/ep01_raw.wav'
wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
os.makedirs('public/audio', exist_ok=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=9', '-ar', str(SR), '-ac', '2',
                'public/audio/ep01_mix.wav'], check=True)
print('audio selesai')
