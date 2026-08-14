# Görev 2 saha ve algılama tasarımı

Bu tasarım 2026 Uluslararası İHA Yarışması Döner Kanat Görev 2 için saha
bilgileri ile kamera tarafından bulunacak bilgileri kesin olarak ayırır.

## Önceden girilen saha bilgileri

- Başlangıç/bitiş çizgisinin iki ucu
- Direk 1 ve Direk 2
- Görüntü işleme/tarama alanı poligonu
- Güvenli iniş noktası
- Görev, tarama ve bırakma irtifaları

Bu değerler yarışma duyurusu veya sahadaki yetkili hazırlık süreci sonucunda
`field_config.json` dosyasına girilir. Örnek dosyadaki koordinatlar gerçek uçuş
için kullanılmaz.

## Kameradan bulunan bilgiler

- Mavi düzgün altıgen: kırmızı yük
- Kırmızı eşkenar üçgen: mavi yük

Hedef koordinatları saha dosyasına girilmez. Hedefler görüntü işleme ile bulunur.
Mavi ve kırmızı kareler sabit kanat hedefleridir ve görev hedefi olarak kabul
edilmez.

## Zorunlu güvenlik kapısı

Kamera hedef araması ve yük bırakma yetkisi, Direk 2'nin dışarıdan geçildiği
uçuş kontrol verisiyle doğrulanana kadar kapalıdır. İki yük tamamlandığında arama
yetkisi kapanır ve araç çıkış rotasına geçer.

## Yarışma günü akışı

1. Saha bilgileri tek dosyaya girilir.
2. Dosya şema, koordinat, irtifa ve mesafe kontrollerinden geçirilir.
3. Aynı dosyadan Cube rotası ve Raspberry Pi görev sınırları üretilir.
4. Harita önizlemesi takım pilotu tarafından onaylanır.
5. Cube'a yazılan görev geri okunup kaynak görevle karşılaştırılır.
6. Hedef konumu girilmeden görev başlatılır.

Gerçek uçuş entegrasyonu, SITL ve pervanesiz donanım testleri tamamlanmadan
etkinleştirilmez.
