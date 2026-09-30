#!/usr/bin/env bash
# TikTok edit: upright 3:4 source -> 1080x1920, soft-blurred background behind a person matte,
# reference-style captions (captions.ass), cleaned voice; optional music bed ducked under the voice.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p renders
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/upright.mp4)

VF="[0:v]fps=30,scale=1440:1920:flags=lanczos,crop=1080:1920:180:0,split[a][b];
[a]gblur=sigma=14,eq=brightness=-0.05:saturation=0.85[bg];
[b]unsharp=5:5:0.6,eq=contrast=1.04:saturation=0.95[fg];
[1:v]fps=30,alphaextract,scale=1440:1920:flags=bicubic,crop=1080:1920:180:0,gblur=sigma=2,format=gray[m];
[fg][m]alphamerge[fga];
[bg][fga]overlay=format=auto,vignette=PI/5,ass=captions.ass,format=yuv420p[v]"

# 1) Video + clean voice only (safe to add music later inside TikTok)
ffmpeg -v error -stats -y -i assets/upright.mp4 -i assets/person.mov -i assets/voice_clean.wav \
  -filter_complex "$VF;[2:a]aformat=channel_layouts=stereo,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -preset slow -crf 16 -maxrate 14M -bufsize 28M -profile:v high -level 4.2 -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart renders/wander_tiktok_sin_musica.mp4

# 2) Same picture (stream copy) + music bed ducked under the voice
ffmpeg -v error -y -i renders/wander_tiktok_sin_musica.mp4 -i assets/voice_clean.wav -i assets/music.m4a \
  -filter_complex "[1:a]aformat=channel_layouts=stereo,asplit[vo][key];
[2:a]aformat=channel_layouts=stereo,aresample=48000,volume=0.22,afade=t=in:d=2,afade=t=out:st=136:d=5[mu];
[mu][key]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[duck];
[vo][duck]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  renders/wander_tiktok_con_musica.mp4
