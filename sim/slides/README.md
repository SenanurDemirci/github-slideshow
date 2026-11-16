# NTN simülasyon slaytları

`NTN_Simulation_LEO_GEO.pptx`: 17 LEO karesi (t = 0–480 s, 30 s aralık, 4 handover), 1 GEO karesi,
LEO vs GEO karşılaştırması, formüller ve kaynaklar. Sol taraf simülasyon görüntüsü, sağ taraf düzenlenebilir metin.

Yeniden üretmek için:

```
pip install numpy matplotlib pillow
python make_frames.py ../ frames          # ../ = leo_geo_doppler.py ve ntn_3gpp.py'nin bulunduğu klasör
npm install pptxgenjs@3.12.0
node build_deck.js $PWD/NTN_Simulation_LEO_GEO.pptx <pptx skill>/scripts/apply_theme.js
```
