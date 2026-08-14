# Mission Planner yarışma görevleri

## Görev 1 — yalnızca Mission Planner AUTO

1. Hakemden kalkış yönü onayı alınır.
2. Gerçek Direk 1 ve Direk 2 koordinatları Mission Planner'a girilir.
3. Kalkış çizgisinden Direk 2'ye giden rota oluşturulur.
4. Direklerin dışından güvenli dönüş yarıçapıyla waypoint yayları çizilir.
5. Direk 2 ve Direk 1 çevresindeki yaylar iki tam `∞` tur oluşturacak sırada
   tekrarlanır.
6. İkinci turdan sonra rota Direk 2'nin arkasından ve dışından geçirilir.
7. Başlangıç/bitiş çizgisi mutlaka geçilir.
8. `LAND`, bitiş çizgisini geçen waypointten sonra ve iki direk arasındaki uygun
   alana eklenir.
9. Görev Cube'a yazılır, tekrar okunur ve waypoint sırası haritada doğrulanır.

Görev 1 sırasında Raspberry Pi uçuş rotasına müdahale etmez.

## Görev 2 — Mission Planner AUTO + görüntü işleme

Mission Planner görevi şu kapıları açık biçimde içermelidir:

- Direk 2 dış geçiş waypointi
- Tarama alanı çıkış waypointi
- Başlangıç/bitiş çizgisi geçilmiş waypoint
- Bu noktadan sonraki `LAND`

Bu üç waypointin Mission Planner sıra numarası `mission2_route.json` dosyasına,
`mission2_route.example.json` örneğine göre yazılır. Hedef koordinatları bu dosyaya
veya Mission Planner'a girilmez.

Uçuş akışı:

1. Cube AUTO görevine başlar; görüntü işleme kilitlidir.
2. `pole_2_outside_waypoint` görüldüğünde tarama yetkisi açılır.
3. Hedef doğrulanınca aktif waypoint kaydedilir ve araç GUIDED moda alınır.
4. Hedef merkezleme ve yük bırakma tamamlanır.
5. Bir sonraki güvenli waypoint seçilir ve araç AUTO moda döner.
6. İkinci yükten sonra görüntü işleme kapanır; AUTO çıkış rotası sürer.
7. `finish_line_crossed_waypoint` geçildikten sonra Mission Planner'daki LAND
   uygulanır.

## Uçuş öncesi zorunlu doğrulamalar

- Mission Planner görevini Cube'a yazdıktan sonra geri oku.
- Üç kapı waypointinin numaralarını geri okunan görevden kontrol et.
- Direk 2 waypointinin gerçekten direğin dışından geçtiğini haritada doğrula.
- Tarama çıkışının iki yük tamamlanmadan aşılması yazılımda görevi ABORT yapar.
- AUTO–GUIDED–AUTO geçişini önce SITL, sonra pervaneler sökülüyken doğrula.
- Kamera eksenlerinin gövde eksenleriyle yön dönüşümünü pervanesiz test etmeden
  gerçek merkezleme komutlarını açma.
- RC pilotun her an LOITER/BRAKE ile devralabileceğini doğrula.
