
# Sifteroxy (TR)

**sift(er) + proxy** — ücretsiz proxy’leri toplar, süzer, doğrular ve çalışanları **atomik** biçimde `.txt` olarak yayınlar.

### Neden Sifteroxy?

* **Atomik yayın**: `.tmp → fsync → rename` ile asla yarım dosya yok.
* **Önizleme yedeği**: bir önceki sağlam dosya `*.prev` olarak tutulur.
* **Paralel doğrulama**: ayarlanabilir eşzamanlılık.
* **Protokol filtreleri**: HTTP, HTTPS, SOCKS4, SOCKS5.
* **Metrik JSON** (isteğe bağlı): gecikme, toplam süre, durum, adet.
* **Cron/systemd uyumlu**: hazır betikler.

### Kurulum

#### Hızlı Kurulum (Önerilen)

Otomatik systemd service/timer kurulumu için:

```bash
sudo ./install.sh
sudo ./active.sh  # Timer'ı etkinleştir
```

Bu işlem:
- Python bağımlılıklarını yükler
- Dosyaları `/opt/sifteroxy` klasörüne kopyalar
- Systemd service ve timer'ı kurar
- Her 30 dakikada bir otomatik çalışmayı yapılandırır

#### Manuel Kurulum

1. **Bağımlılıkları Yükle:**
```bash
pip install -U requests "requests[socks]"
```

2. **Dosyaları Kopyala:**
```bash
sudo mkdir -p /opt/sifteroxy
sudo cp sifteroxy.py sources.json proxy_update.sh /opt/sifteroxy/
sudo chmod +x /opt/sifteroxy/sifteroxy.py
sudo chmod +x /opt/sifteroxy/proxy_update.sh
```

3. **Systemd Service & Timer Kur:**
```bash
sudo cp sifteroxy.service /etc/systemd/system/
sudo cp sifteroxy.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

4. **Timer'ı Etkinleştir:**
```bash
sudo ./active.sh
# Veya manuel olarak:
sudo systemctl enable --now sifteroxy.timer
```

5. **Kurulumu Doğrula:**
```bash
sudo systemctl status sifteroxy.timer
sudo systemctl status sifteroxy.service
```

#### Timer'ı Devre Dışı Bırak

Otomatik çalışmayı durdurmak için:

```bash
sudo ./deactive.sh
# Veya manuel olarak:
sudo systemctl stop sifteroxy.timer
sudo systemctl disable sifteroxy.timer
```

### Hızlı Başlangıç

```bash
python3 sifteroxy.py                                    # varsayılan
python3 sifteroxy.py --protocols http,https              # sadece HTTP/HTTPS
python3 sifteroxy.py --metrics metrics.json            # metrik yaz
python3 sifteroxy.py --out /var/www/alive.txt          # özel çıktı yolu
python3 sifteroxy.py --no-preview                      # .prev yedeğini kapat
python3 sifteroxy.py --language en                     # İngilizce loglar
python3 sifteroxy.py --order asc                       # en yavaştan en hızlıya
```

**Atomik yayın + .prev** Sifteroxy’nin içinde hazırdır; okuyan servisler ya eski **tam** dosyayı ya da yeni **tam** dosyayı görür.

### Cron & systemd

* **systemd timer** (önerilen): Her 30 dakikada bir otomatik çalışır
* **Cron** (alternatif): `*/10 * * * * /opt/sifteroxy/proxy_update.sh`

### Kaynaklar & Hukuki Not

Kaynak listeleri topluluk tarafından tutulur; `sources.json` dosyasından güncelleyebilirsin. Bu JSON dosyası her protokol (http, https, socks4, socks5) için kaynak URL'lerini içerir. Aracı sadece **yasal ve yetkili** testler için kullan.

### Yeni Özellikler

* **Dil Desteği**: `--language tr|en` parametresi ile log mesajları Türkçe veya İngilizce olabilir (varsayılan: `tr`)
* **Sıralama**: `--order desc|asc` parametresi ile çalışan proxy'ler hızına göre sıralanır (varsayılan: `desc` = en hızlıdan en yavaşa)
* **İlerleme Yüzdesi**: Doğrulama sırasında toplam ilerleme yüzdesi gösterilir
* **JSON Kaynaklar**: Proxy kaynakları artık `sources.json` dosyasından okunur

---

## Branding

* **Name:** Sifteroxy (sift(er) + proxy)
* **Repo:** `sifteroxy`
* **CLI:** `sifteroxy` (alias: `siftx`)
* **Tagline:** *“fetch, sift, verify, publish — atomically.”*
