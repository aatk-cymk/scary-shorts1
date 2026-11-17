"""Synthesize an original eerie ambient track: low drones, dissonant pad, sparse music-box notes."""
import numpy as np, wave, sys

SR = 44100


def tone(f, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    return t, np.sin(2 * np.pi * f * t)


def make(dur, out, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    root = rng.choice([55.0, 58.27, 61.74])  # A1, Bb1, B1
    mix = np.zeros(n)
    # drone: root + detuned + fifth, slow tremolo
    for f, a in [(root, 0.35), (root * 1.006, 0.3), (root * 1.5, 0.12), (root * 2.01, 0.08)]:
        mix += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6))
    mix *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t)
    # dissonant high pad (minor second) swelling in and out
    pad = sum(np.sin(2 * np.pi * f * t) for f in (root * 8, root * 8 * 1.0595, root * 8 * 1.414))
    mix += 0.05 * pad * (0.5 - 0.5 * np.cos(2 * np.pi * t / 16))
    # music box: sparse notes from a creepy (harmonic minor + tritone) set
    scale = np.array([0, 1, 4, 6, 7, 8, 11, 12, 13])
    tnext = 1.5
    while tnext < dur - 2:
        f = root * 16 * 2 ** (rng.choice(scale) / 12)
        ln = 2.5
        i0 = int(tnext * SR); i1 = min(n, i0 + int(ln * SR))
        tt = np.arange(i1 - i0) / SR
        env = np.exp(-tt * 2.2)
        note = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * env
        mix[i0:i1] += 0.12 * note
        tnext += rng.choice([0.5, 0.75, 1.0, 1.5, 2.5])
    # low rumble
    noise = rng.standard_normal(n)
    k = 2000
    rumble = np.convolve(noise, np.ones(k) / k, mode="same") * 6
    mix += 0.25 * rumble
    # fade in/out
    fade = np.minimum(1, np.minimum(t / 2.0, (dur - t) / 2.0))
    mix *= np.clip(fade, 0, 1)
    mix /= np.max(np.abs(mix)) + 1e-9
    data = (mix * 0.8 * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


if __name__ == "__main__":
    make(float(sys.argv[1]), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
