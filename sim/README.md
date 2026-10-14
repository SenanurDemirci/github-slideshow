# LEO / GEO NTN Doppler & Kapsama Simülatörü

`leo_geo_doppler.py` — Python sürümü (numpy + matplotlib).
`leo_geo_doppler_colab.ipynb` — Google Colab notebook'u (kod içine gömülü, tek dosya yeterli).
`matlab/` — MATLAB sürümü (`leo_geo_doppler_sim.m`, `coverage_analysis.m`).
`ntn_3gpp.py` — 3GPP TR 38.811 / TR 38.821 formülleriyle link budget, radyo kapsaması ve kapasite.

## 3GPP link budget, kapsama ve kapasite (`ntn_3gpp.py`)

```
python ntn_3gpp.py      # TR 38.821 Tablo 6.1.3.3-1'deki 30 vakayı (60 CNR) yeniden üretir ve karşılaştırır
```

| İçerik | Kaynak |
|---|---|
| CNR, G/T, EIRP, CNIR | TR 38.821 (6.1.3.1-1 … -5) |
| Uydu / UE parametreleri, bant genişliği, kayıplar | TR 38.821 Tablo 6.1.1.1-1/2/3, 6.1.3.2-1 |
| FSPL, eğik mesafe, atmosfer kaybı | TR 38.811 (6.6-2), (6.6-3), (6.6-8) |
| LOS olasılığı, gölgeleme, clutter kaybı, sintilasyon | TR 38.811 Tablo 6.6.1-1, 6.6.2-1/2/3, 6.6.6.2.1-1 |
| Kapasite: Shannon C = B·log2(1+CNIR) | belgelerde yok (üst sınır); TR 38.821 Tablo 6.1.1.3-1 SLS ile karşılaştırılır |

Colab notebook'unda 7–9. hücreler (link budget, radyo kapsaması, kapasite) bu dosyayı kullanır.

## MATLAB'da çalıştırma

İki dosyayı (`leo_geo_doppler_sim.m`, `coverage_analysis.m`) aynı klasöre koyun, MATLAB'da o klasöre geçin:

```matlab
leo_geo_doppler_sim                                   % etkileşimli pencere (kaydırıcılar + butonlar)
leo_geo_doppler_sim('Layer','GEO')                    % sadece GEO
leo_geo_doppler_sim('Layer','LEO','Fc',20,'NSat',10)  % Ka-band, 10 uydu (kapsama boşlukları)
leo_geo_doppler_sim('SavePng','ekran.png','T',120)    % t = 120 s anındaki tek kare
leo_geo_doppler_sim('SaveGif','sim.gif','Frames',60,'StepS',20)   % animasyonu GIF olarak kaydet
coverage_analysis(600, 10, 12)                        % kapsama analizi: irtifa, min elevasyon, uydu sayısı
```

Ek toolbox gerekmez (MATLAB R2016b+). GNU Octave 6+ ile de çalışır.

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
