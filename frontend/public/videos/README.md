# Video da rota /investidores

Este diretorio contem o video exibido no hero da pagina `/investidores`.

## Caminho obrigatorio

Coloque o arquivo exatamente neste path:

- `public/videos/investidores.mp4`

Na aplicacao, o source usado e:

- `/videos/investidores.mp4`

## Especificacoes recomendadas

- Formato: MP4 (codec H.264)
- Resolucao: 1920x1080 (desktop)
- Frame rate: 24 a 30 fps
- Duracao: 10 a 30 segundos (loop)
- Audio: opcional, mas o player usa `muted`

## Conversao rapida com FFmpeg

```bash
ffmpeg -i origem.mov \
	-c:v libx264 -preset medium -crf 23 \
	-pix_fmt yuv420p \
	-movflags +faststart \
	-an \
	investidores.mp4
```

Depois mova para:

```bash
mv investidores.mp4 public/videos/investidores.mp4
```

## Validacao

1. Rode o frontend.
2. Abra `/investidores`.
3. Confirme se o video inicia automatico e cobre toda a tela.

## Troubleshooting

- Tela preta: confirme se o arquivo existe em `public/videos/investidores.mp4`.
- Video nao toca no browser: reconverta para H.264 com `yuv420p`.
- Download lento: reduza bitrate e duracao do arquivo.
