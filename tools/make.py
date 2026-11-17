"""Build one scary Short.  usage: python3 make.py story.json out.mp4
story.json: {"title", "description", "seed", "hook": {"text","scene"}, "lines": [{"text","scene"}, ...]}
Scenes: house, phone, grave, door, knock, figure, window
"""
import subprocess, os, json, sys, textwrap, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tts import synth
from scenes import draw
from music import make as make_music

W, H = 1080, 1920
here = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(sys.argv[1]))
out = os.path.abspath(sys.argv[2])
seed = int(story.get("seed", 1))
B = os.path.join(here, "build")
shutil.rmtree(B, ignore_errors=True)
os.makedirs(B)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True)


def dur_of(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def frame(text, scene, i, title=False):
    img = draw(scene, seed * 100 + i)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 92 if title else 66
    f = ImageFont.truetype(FONT, size)
    lines = textwrap.wrap(text, 15 if title else 22)
    lh = size * 1.28
    top = (520 if title else 1560) - lh * len(lines) / 2
    bd = ImageDraw.Draw(band)
    bd.rectangle([0, top - 50, W, top + lh * len(lines) + 40], fill=(0, 0, 0, 150))
    band = band.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), band)
    d = ImageDraw.Draw(img)
    y = top
    for ln in lines:
        w = d.textlength(ln, font=f)
        x = (W - w) / 2
        d.text((x + 4, y + 4), ln, font=f, fill=(0, 0, 0))
        d.text((x, y), ln, font=f, fill=(205, 25, 30) if title else (238, 230, 220))
        y += lh
    p = f"{B}/f{i}.png"
    img.convert("RGB").save(p)
    return p


items = [story["hook"]] + story["lines"]
parts = []
for i, it in enumerate(items):
    raw, a = f"{B}/a{i}.wav", f"{B}/b{i}.wav"
    synth(it["text"], raw)
    run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
         "asetrate=22050*0.88,aresample=44100,aecho=0.8:0.7:60:0.25,lowpass=f=5000,apad=pad_dur=0.7",
         "-ar", "44100", "-ac", "1", a])
    dur = dur_of(a)
    frames = int(round(dur * 30))
    png = frame(it["text"], it["scene"], i, title=(i == 0))
    z = "min(1+0.0009*on,1.15)" if i % 2 == 0 else "max(1.15-0.0009*on,1)"
    vf = (f"scale=1296:2304,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
          f"noise=alls=6:allf=t,format=yuv420p,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(dur-0.3,0):.3f}:d=0.3")
    tmp = f"{B}/s{i}.tmp.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", png, "-i", a, "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-crf", "26", "-maxrate", "3M", "-bufsize", "6M", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", tmp])
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
print(out, round(total, 1), os.path.getsize(out) // 1024, "KB")
