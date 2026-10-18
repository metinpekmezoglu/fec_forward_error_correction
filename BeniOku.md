# İHA ve Model Uydu Telemetri Sinyallerinde FEC Sistemi

Bu proje, kablosuz haberleşme hatlarında gürültü ve kanal bozulmaları nedeniyle oluşan veri kayıplarını ve bit hatalarını en aza indirmek amacıyla geliştirilmiş bir Forward Error Correction - FEC simülasyon ve uygulama projesidir.



# Projenin Amacı ve Kapsamı

Model uydular ve İHA'lar uçuş sırasında yer istasyonuna anlık telemetri verileri  gönderirler. Ancak RF  ortamındaki gürültüler, çok yollu yayılım ve sinyal zayıflamaları paket kayıplarına yol açabilir.



Bu projede:



Gerçekçi bir İkili Simetrik Kanal  ve AWGN gürültü modeli simüle edilmiştir.



Hata tespiti ve düzeltmesi için Hamming Kodları ve Reed-Solomon algoritmaları entegre edilmiştir.



FEC kullanan ve kullanmayan sistemlerin Bit Hata Oranı  performans kıyaslamaları grafiksel olarak raporlanmıştır.





# **Sistem Mimarisi ve Akış**



\[ Veri Kaynağı (Sensörler) ]

&#x20;      │

&#x20;      ▼

\[ Kanal Kodlayıcı (FEC Encoder) ] ──> (Hamming / Reed-Solomon)

&#x20;      │

&#x20;      ▼

\[ RF Kanal / Gürültü Simülasyonu ] ──> (AWGN / Bit Flip)

&#x20;      │

&#x20;      ▼

\[ Kanal Kod Çözücü (FEC Decoder) ] ──> Hata Tespiti ve Düzeltme

&#x20;      │

&#x20;      ▼

\[ Alıcı / Yer İstasyonu (Clean Payload) ]







# **Proje Dosya Yapısı**



├── src/

│   ├── encoder.py         # FEC kodlama modülleri (Hamming, vb.)

│   ├── decoder.py         # Hata düzeltme ve çözme algoritmaları

│   ├── channel.py         # Gürültü ve kanal simülasyon modelleri

│   └── telemetry.py       # Paket formatı (Framing) ve serileştirme

├── tests/

│   └── test\_fec.py        # Birim testler (Unit tests)

├── assets/

│   └── ber\_curve.png      # Başarım analizi grafikleri

├── main.py                # Simülasyonun çalıştırıldığı ana script

├── requirements.txt       # Gerekli kütüphaneler

└── README.md              # Proje dokümantasyonu







# **Kurulum ve Çalıştırma**



Projeyi yerel bilgisayarında çalıştırmak için aşağıdaki adımları izleyebilirsin:



1-) Repoyu klonla:



git clone https://github.com/metinpekmezoglu/FEC\_Forward\_Error\_Correction.git



cd FEC\_Forward\_Error\_Correction



2-) Gerekli kütüphaneleri yükle:



pip install -r requirements.txt



3-) Simülasyonu çalıştır:



python main.py



# **İletişim**



**\*\*Metin Pekmezoğlu\*\***

**\* Elektrik-Elektronik Mühendisliği**

**\* \[GitHub Profilim](https://github.com/metinpekmezoglu)**

**\* \[LinkedIn Profilim](https://www.linkedin.com/in/metin-pekmezo%C4%9Flu-44baba259/)**

