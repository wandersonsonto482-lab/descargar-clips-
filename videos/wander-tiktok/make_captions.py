import json, re
W = json.load(open("transcript.json"))
fix = {"Wandel,": "Wander,", "Wandel": "Wander", "Johnny.": "yo del", "confi": "confiar", "hiciste": "quisiste"}
for w in W: w["text"] = fix.get(w["text"], w["text"])
json.dump(W, open("transcript.fixed.json", "w"), ensure_ascii=False, indent=0)

# Reference style: phrase-length cues (≤7 words / ~38 chars), break on sentence end, comma, or pause
groups, cur = [], []
for i, w in enumerate(W):
    cur.append(w)
    nxt = W[i + 1] if i + 1 < len(W) else None
    gap = (nxt["start"] - w["end"]) if nxt else 9
    txt = " ".join(x["text"] for x in cur)
    sent_end = w["text"][-1] in ".?!"
    comma = w["text"].endswith(",") and len(cur) >= 3
    if not nxt or sent_end or comma or gap > 0.5 or len(cur) >= 7 or len(txt) >= 38:
        groups.append(cur); cur = []
# merge a trailing 1-word cue into its predecessor when they're close
merged = []
for g in groups:
    prev = merged[-1] if merged else None
    joinable = prev and prev[-1]["text"][-1] not in ".?!" and g[0]["start"] - prev[-1]["end"] < 0.8 and len(prev) + len(g) <= 7 and len(" ".join(x["text"] for x in prev + g)) <= 42
    if joinable or (prev and len(g) == 1 and g[0]["start"] - prev[-1]["end"] < 0.5 and len(prev) < 8):
        merged[-1] += g
    else:
        merged.append(g)
groups = merged

KEEP_CAP = {"Wander", "Wander,", "Wanderson,", "Wanderson", "Dios", "Dios.", "Dios,"}
def fmt(g):
    t = " ".join(x["text"] for x in g)
    t = re.sub(r",$", "", t)
    first = g[0]["text"]
    if first not in KEEP_CAP and t[:1].isupper():
        t = t[0].lower() + t[1:]
    return t

def ts(t):
    return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"

ev = []
for gi, g in enumerate(groups):
    start = g[0]["start"]
    end = g[-1]["end"] + 0.3
    if gi + 1 < len(groups): end = min(end, groups[gi + 1][0]["start"] - 0.02)
    end = max(end, start + 0.6)
    ev.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{\\fad(80,60)}}{fmt(g)}")

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Medium,54,&H00FFFFFF,&H00FFFFFF,&H64000000,&H5A000000,0,0,0,0,100,100,0,0,1,1.4,3,2,130,130,760,1
Style: Brand,Inter SemiBold,30,&H4DFFFFFF,&H00FFFFFF,&H80000000,&H80000000,0,0,0,0,100,100,6,0,1,0,1.5,7,72,0,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
dur = 147.4
ev.append(f"Dialogue: 1,{ts(0)},{ts(dur)},Brand,,0,0,0,,wander")
open("captions.ass", "w").write(head + "\n".join(ev) + "\n")
print(len(groups), "cues")
for g in groups[:14]: print(" ", fmt(g))
