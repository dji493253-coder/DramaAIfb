# Rahasia 20 Tahun - Episode 1 (Story Behind Life)

Edit sinematik 9:16 untuk Facebook Reels, dibuat dengan Remotion.

- `public/clips/` klip asli dari Flow (c01..c09, urut cerita)
- `data/ep01_edit.json` daftar shot: potongan, zoom, fokus, suasana, SFX
- `scripts/build_ep.py` membangun timeline (`data/ep01.json`) dan mix audio (`public/audio/ep01_mix.wav`)
- `scripts/prep.sh` memperbesar klip ke 1080x1920
- Render: tab Actions > Render Episode > Run workflow. Hasil ada di Releases.

Ganti klip dengan versi resolusi lebih tinggi: timpa file di `public/clips/` dengan nama yang sama.
