"""Build one scary Short (v2: fast hook, word-by-word captions).
usage: python3 tools/make.py stories/NNN.json videos/short-NNN.mp4
story.json: {"title", "description", "seed", "hook": {"text","scene"}, "lines": [{"text","scene"}, ...]}
Scenes: house, phone, grave, door, knock, figure, window, road, forest, mirror
The hook is spoken first, over the scariest scene, with no title card.
"""
import subprocess, os, json, sys, shutil
from PIL import Image, ImageDraw, ImageFont
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from tts import synth
from scenes import draw
from music import make as make_music

W, H = 1080, 1920
story = json.load(open(sys.argv[1]))
out = os.path.abspath(sys.argv[2])
seed = int(story.get("seed", 1))
B = os.path.join(here, "..", "build")
shutil.rmtree(B, ignore_errors=True)
os.makedirs(B)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True)


def dur_of(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def chunks(text, n=3):
    w = text.split()
    return [" ".join(w[i:i + n]) for i in range(0, len(w), n)]


def caption_png(text, path, red=False):
    """Transparent 1080x1920 overlay with one big caption chunk, centred low."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    size = 104
    f = ImageFont.truetype(FONT, size)
    text = text.upper()
    while d.textlength(text, font=f) > W - 140 and size > 56:
        size -= 6; f = ImageFont.truetype(FONT, size)
    y = 1460
    d.text((W / 2, y), text, font=f, anchor="mm", fill=(230, 30, 35) if red else (255, 255, 255),
           stroke_width=10, stroke_fill=(0, 0, 0))
    img.save(path)


items = [story["hook"]] + story["lines"]
parts = []
for i, it in enumerate(items):
    raw, a = f"{B}/a{i}.wav", f"{B}/b{i}.wav"
    synth(it["text"], raw)
    run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
         "asetrate=22050*0.9,aresample=44100,aecho=0.8:0.7:60:0.25,lowpass=f=5000,apad=pad_dur=0.35",
         "-ar", "44100", "-ac", "1", a])
    dur = dur_of(a)
    speech = max(dur - 0.35, 0.5)
    frames = int(round(dur * 30))
    bg = f"{B}/bg{i}.png"
    draw(it["scene"], seed * 100 + i).save(bg)
    # caption chunks timed by character share of the spoken part
    cs = chunks(it["text"])
    total_chars = sum(len(c) for c in cs)
    inputs, filters, t = [], [], 0.0
    prev = "[v0]"
    for k, c in enumerate(cs):
        cp = f"{B}/c{i}_{k}.png"
        caption_png(c, cp, red=(i == 0))
        span = speech * len(c) / total_chars
        end = dur if k == len(cs) - 1 else t + span
        inputs += ["-i", cp]
        nxt = f"[v{k+1}]"
        filters.append(f"{prev}[{k+2}:v]overlay=0:0:enable='between(t,{t:.3f},{end:.3f})'{nxt}")
        prev = nxt
        t += span
    z = "min(1+0.0015*on,1.2)" if i % 2 == 0 else "max(1.2-0.0015*on,1)"
    base = (f"[0:v]scale=1296:2304,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
            f"noise=alls=6:allf=t[v0]")
    fc = ";".join([base] + filters) + f";{prev}format=yuv420p[vout]"
    tmp = f"{B}/s{i}.tmp.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", bg, "-i", a] + inputs +
        ["-filter_complex", fc, "-map", "[vout]", "-map", "1:a", "-frames:v", str(frames),
         "-c:v", "libx264", "-crf", "26", "-maxrate", "3M", "-bufsize", "6M", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", tmp])
    os.replace(tmp, f"{B}/s{i}.mp4")
    parts.append(f"s{i}.mp4")

with open(f"{B}/list.txt", "w") as fh:
    fh.writelines(f"file '{p}'\n" for p in parts)
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/joined.mp4"])
total = dur_of(f"{B}/joined.mp4")
make_music(total + 0.5, f"{B}/music.wav", seed)
run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/joined.mp4", "-i", f"{B}/music.wav",
     "-filter_complex",
     "[1]aecho=0.8:0.85:400|900:0.35|0.25,volume=0.32[m];[0:a][m]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]",
     "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out + ".tmp.mp4"])
os.replace(out + ".tmp.mp4", out)
print(out, round(total, 1), "sec", os.path.getsize(out) // 1024, "KB")
