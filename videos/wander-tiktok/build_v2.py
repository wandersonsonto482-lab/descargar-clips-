"""v2 edit: ~50s highlight cut with hook-first order, jump cuts, alternating punch-in,
soft background blur (person matte), bold pop captions, ducked music bed."""
import json, subprocess, os, re

SRC, MATTE, VOICE, MUSIC = "assets/upright.mp4", "assets/person.mov", "assets/voice_clean.wav", "assets/music.m4a"
OUT = "renders/v2"; os.makedirs(OUT, exist_ok=True)
W = json.load(open("transcript.fixed.json"))

# (source start, source end, framing)  framing: M = medium, C = close punch-in
SEGS = [
    (44.01, 47.13, "C"),   # hook: mensaje para mi yo de cinco años en el futuro
    (11.28, 17.12, "M"),   # mi nombre es Wander, 21 años, redes sociales
    (17.31, 20.51, "C"),   # voy a construir una marca personal
    (28.91, 34.19, "M"),   # luchando por tu sueño, por tu meta
    (34.51, 36.11, "C"),   # se está volviendo duro
    (36.89, 40.65, "M"),   # pero yo sé que tú puedes lograrlo
    (48.17, 49.61, "C"),   # pudiste lograrlo
    (50.30, 56.22, "M"),   # la vida que siempre quisiste, sacar a toda tu familia
    (56.94, 60.34, "C"),   # a tus hermanos, a tus padres, salir de
    (61.42, 62.30, "C"),   # la pobreza
    (86.78, 88.38, "M"),   # gracias por luchar
    (89.18, 92.38, "C"),   # y por no rendirte todo ese tiempo
    (92.62, 95.26, "M"),   # por confiar en Dios principalmente
    (139.55, 142.83, "C"), # apóyenme porque se viene un buen cambio
    (143.63, 146.43, "M"), # síganme para que sean parte de ese cambio
]
PRE, POST = 0.10, 0.22
# upright source is 480x640; crops are 9:16 regions scaled to 1080x1920
CROP = {"M": "360:640:60:0", "C": "288:512:96:8"}

def run(cmd): subprocess.run(cmd, check=True)

parts, words_out, t_out = [], [], 0.0
for i, (s, e, fr) in enumerate(SEGS):
    a, b = max(0, s - PRE), e + POST
    d = b - a
    seg = f"{OUT}/seg{i:02d}.mp4"
    vf = (f"[0:v]split[s1][s2];[s1]gblur=sigma=4.5,eq=brightness=-0.06:saturation=0.85[bg];"
          f"[1:v]alphaextract,gblur=sigma=0.8,format=gray[m];[s2][m]alphamerge[fg];"
          f"[bg][fg]overlay=format=auto,crop={CROP[fr]},scale=1080:1920:flags=lanczos,"
          f"unsharp=5:5:0.5,eq=contrast=1.05:saturation=1.02,fps=30,format=yuv420p[v];"
          f"[2:a]atrim=0:{d:.3f},afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,aformat=channel_layouts=stereo[a]")
    if not os.path.exists(seg.replace(".mp4", ".mov")): run(["ffmpeg", "-v", "error", "-y",
         "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", SRC,
         "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", MATTE,
         "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", VOICE,
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}",
         "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-c:a", "pcm_s16le", seg.replace(".mp4", ".mov")])
    parts.append(seg.replace(".mp4", ".mov"))
    for w in W:
        if w["start"] >= s - 0.05 and w["start"] < e:
            words_out.append({"text": w["text"], "start": t_out + (w["start"] - a), "end": t_out + (min(w["end"], b) - a)})
    t_out += d

TOTAL = t_out
json.dump(words_out, open(f"{OUT}/words.json", "w"), ensure_ascii=False, indent=0)

# ---- captions: 1–3 words, bold, pop-in ----
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
groups, cur = [], []
for i, w in enumerate(words_out):
    cur.append(w)
    nxt = words_out[i + 1] if i + 1 < len(words_out) else None
    txt = " ".join(x["text"] for x in cur)
    if not nxt or len(cur) >= 3 or len(txt) >= 16 or w["text"][-1] in ".,?!" or nxt["start"] - w["end"] > 0.3:
        groups.append(cur); cur = []
KEEP = {"Wander", "Wander,", "Dios", "Dios."}
def clean(g):
    t = " ".join(x["text"] for x in g)
    t = re.sub(r"[.,;:]", "", t)
    return t.upper()
ev = []
for gi, g in enumerate(groups):
    st, en = g[0]["start"], g[-1]["end"] + 0.12
    if gi + 1 < len(groups): en = min(en, groups[gi + 1][0]["start"])
    en = max(en, st + 0.35)
    ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Cap,,0,0,0,,{{\\fscx86\\fscy86\\t(0,90,\\fscx100\\fscy100)}}{clean(g)}")
hook_end = SEGS[0][1] - SEGS[0][0] + PRE + POST
ev.append(f"Dialogue: 1,{ts(0)},{ts(hook_end)},Hook,,0,0,0,,{{\\fad(0,200)}}Mensaje para mi yo\\Ndel futuro")
ev.append(f"Dialogue: 1,{ts(hook_end)},{ts(TOTAL)},Brand,,0,0,0,,wander")
ev.append(f"Dialogue: 1,{ts(TOTAL-3.2)},{ts(TOTAL)},Cta,,0,0,0,,{{\\fad(150,0)}}sígueme")
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,1,0,1,6,4,5,100,100,0,1
Style: Hook,Inter ExtraBold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,24,0,8,120,120,1330,1
Style: Brand,Inter Bold,34,&H26FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,8,0,1,0,2,7,70,0,235,1
Style: Cta,Inter ExtraBold,58,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,2,0,3,24,0,8,0,0,1330,1
"""
# Cap alignment 5 = middle-center; place at ~62% height via \pos
ev = [e.replace("{\\fscx86", "{\\pos(540,1190)\\fscx86") for e in ev]
open(f"{OUT}/captions.ass", "w").write(head + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(ev) + "\n")

# ---- concat + captions + music ----
open(f"{OUT}/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/joined.mov"])
fc = (f"[0:v]ass={OUT}/captions.ass,format=yuv420p[v];"
      f"[0:a]asplit[vo][key];"
      f"[1:a]aformat=channel_layouts=stereo,aresample=48000,volume=0.30,afade=t=in:d=1.2,afade=t=out:st={TOTAL-2.5:.2f}:d=2.5[mu];"
      f"[mu][key]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
      f"[vo][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
for name, mus in (("wander_v2_con_musica", True), ("wander_v2_sin_musica", False)):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/joined.mov"]
    if mus: cmd += ["-ss", "33", "-i", MUSIC, "-filter_complex", fc]
    else: cmd += ["-filter_complex", f"[0:v]ass={OUT}/captions.ass,format=yuv420p[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=9[a]"]
    cmd += ["-map", "[v]", "-map", "[a]", "-t", f"{TOTAL:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
            "-maxrate", "4M", "-bufsize", "8M", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", f"renders/{name}.mp4"]
    run(cmd)
print(f"total {TOTAL:.2f}s, {len(groups)} captions")
