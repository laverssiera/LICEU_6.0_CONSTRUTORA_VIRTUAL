# Videos do hero institucional

Este diretorio contem os videos usados na pagina institucional do `cv-frontend`.

## Caminhos obrigatorios

Os arquivos esperados pela aplicacao sao:

- `public/videos/liceu-hero.mp4` (desktop)
- `public/videos/liceu-hero-mobile.mp4` (mobile)

Na pagina, os sources usados sao:

- `/videos/liceu-hero.mp4`
- `/videos/liceu-hero-mobile.mp4`

## Especificacoes recomendadas

- Formato: MP4 (H.264)
- Perfil de pixel: `yuv420p`
- Desktop: 1920x1080
- Mobile: 1280x720 ou 720p equivalente
- Duracao: 10 a 20 segundos (loop)
- Audio: opcional; player roda com `muted`

## Conversao rapida (FFmpeg)

Gerar versao desktop:

```bash
ffmpeg -i video.mov \
  -c:v libx264 -preset medium -crf 22 \
  -pix_fmt yuv420p -movflags +faststart \
  -an \
  liceu-hero.mp4
```

Gerar versao mobile:

```bash
ffmpeg -i video.mov \
  -vf scale=1280:-2 \
  -c:v libx264 -preset medium -crf 24 \
  -pix_fmt yuv420p -movflags +faststart \
  -an \
  liceu-hero-mobile.mp4
```

Mover os arquivos para a pasta publica:

```bash
mv liceu-hero.mp4 public/videos/liceu-hero.mp4
mv liceu-hero-mobile.mp4 public/videos/liceu-hero-mobile.mp4
```

## Validacao

1. Rode o `cv-frontend`.
2. Abra a pagina institucional.
3. Confirme troca automatica entre video desktop e mobile conforme viewport.

## Troubleshooting

- Video nao carrega: valide nomes e paths em `public/videos/`.
- Falha de reproducao em browser antigo: reconverta para H.264 + `yuv420p`.
- Inicio lento: reduza bitrate/CRF e mantenha `+faststart`.
