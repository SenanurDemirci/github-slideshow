# LEO / GEO NTN Doppler & Kapsama Simülatörü

`leo_geo_doppler.py` — Python sürümü (numpy + matplotlib).
`leo_geo_doppler_colab.ipynb` — Google Colab notebook'u (kod içine gömülü, tek dosya yeterli).

## Google Colab'da çalıştırma

1. https://colab.research.google.com adresine gidin.
2. *Dosya → Not defteri yükle* (File → Upload notebook) ile `leo_geo_doppler_colab.ipynb` dosyasını seçin.
3. *Çalışma zamanı → Tümünü çalıştır* (Runtime → Run all).

Kurulum gerekmez (numpy, matplotlib, ipywidgets Colab'da hazır). Notebook'ta tek kare,
kaydırıcılı etkileşimli çizim, oynat/durdur düğmeli animasyon ve GIF indirme hücreleri vardır.

## Kurulum

```
pip install numpy matplotlib pillow
```

## Çalıştırma

```
python leo_geo_doppler.py                         # etkileşimli pencere (kaydırıcılar + butonlar)
python leo_geo_doppler.py --layer GEO --fc 20     # GEO, Ka-band 20 GHz ile başla
python leo_geo_doppler.py --save sim.gif --frames 120   # animasyonu GIF olarak kaydet
python leo_geo_doppler.py --png ekran.png --t 600       # t = 600 s anındaki tek kare
python leo_geo_doppler.py --coverage kapsama.png        # kapsama (footprint) analizi figürü
```

Pencerede: LEO irtifası, düzlemdeki uydu sayısı, minimum elevasyon, GEO konumu,
simülasyon hızı, LEO/GEO servis katmanı ve taşıyıcı frekansı değiştirilebilir.

## Neyi değiştirmek isterseniz

- Kullanıcılar (hız, irtifa, başlangıç yeri): dosyanın başındaki `UES` listesi
- Varsayılan parametreler: `Sim.__init__`
- Doppler / yol kaybı formülleri: `link()` fonksiyonu
- Handover kuralı: `Sim.eval_serving()`
- Kapsama analizi (λ, yarıçap, gereken uydu sayısı): `Sim.coverage()` ve `coverage_figure()`

`leo-geo-doppler.html` aynı simülasyonun tarayıcı sürümüdür (isteğe bağlı).
