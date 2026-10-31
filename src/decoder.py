import numpy as np

class Hamming74Decoder:
    """
    Sistematik Hamming (7,4) Blok Kod Çözücü.
    Sendrom hesaplaması (Syndrome Decoding) ile her 7 bitlik bloktaki
    1 bitlik hataları tespit edip düzeltir ve 4 bitlik orijinal mesajı çıkarır.
    """
    def __init__(self):
        self.n = 7
        self.k = 4
        
        # Parity Alt Matrisi P (4x3) - Encoder ile birebir aynı olmalı
        self.P = np.array([
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1]
        ], dtype=int)
        
        self.I_nk = np.eye(self.n - self.k, dtype=int) # 3x3 Birim Matris
        
        # Eşlik Denetim Matrisi: H = [P^T | I_3] (3x7)
        self.H = np.hstack((self.P.T, self.I_nk))
        
        # H^T (7x3) matrisinin her satırı, o indeksteki bit hatasının sendromunu verir.
        # Hızlı arama (Lookup Table) için sendromları sözlüğe kaydediyoruz:
        # Anahtar: Sendrom tuple'ı (örn: (1, 0, 1)) -> Değer: Hatalı bit indeksi (0..6)
        self.syndrome_table = {}
        for idx, row in enumerate(self.H.T):
            self.syndrome_table[tuple(row)] = idx

    def decode(self, received_data: np.ndarray) -> np.ndarray:
        """
        Gelen 1D kodlanmış (ve gürültülü) bit dizisini 7'şerli bloklara ayırır,
        sendrom tablosuyla tek bitlik hataları düzeltir ve 4 bitlik verileri döndürür.
        """
        received_data = np.asarray(received_data, dtype=int)
        
        if len(received_data) % self.n != 0:
            raise ValueError(f"Gelen veri uzunluğu {self.n}'nin tam katı olmalıdır!")
            
        num_blocks = len(received_data) // self.n
        blocks = received_data.reshape((num_blocks, self.n)).copy()
        
        # Tüm bloklar için sendrom matrisini tek seferde hesapla: S = (R * H^T) mod 2
        syndromes = np.dot(blocks, self.H.T) % 2
        
        # Sendromu sıfırdan farklı olan (hatalı) blokları bul ve düzelt
        for i in range(num_blocks):
            s_tuple = tuple(syndromes[i])
            if s_tuple != (0, 0, 0):
                # Sendrom tablosundan hangi bitin bozulduğunu bul
                error_bit_idx = self.syndrome_table.get(s_tuple)
                if error_bit_idx is not None:
                    # Hatalı biti tersine çevir (0->1, 1->0)
                    blocks[i, error_bit_idx] ^= 1
                    
        # Sistematik kod olduğu için her bloğun ilk 4 biti (k=4) mesaj verisidir
        decoded_messages = blocks[:, :self.k]
        
        return decoded_messages.flatten()


# --- TEST KISMI (Encoder + Kanal Hatası + Decoder) ---
if __name__ == "__main__":
    from encoder import Hamming74Encoder
    
    encoder = Hamming74Encoder()
    decoder = Hamming74Decoder()
    
    # 1. Orijinal 8 bitlik (2 blok) telemetri verisi
    orijinal_veri = np.array([1, 0, 1, 1,   0, 1, 1, 0])
    
    # 2. Hamming (7,4) ile kodla (14 bit)
    kodlu_veri = encoder.encode(orijinal_veri)
    
    # 3. Yapay hata enjekte et (Her iki 7 bitlik bloğun da 1'er bitini bozalım)
    bozuk_veri = kodlu_veri.copy()
    bozuk_veri[2] ^= 1   # 1. bloğun 2. indeksini (3. bitini) bozduk
    bozuk_veri[11] ^= 1  # 2. bloğun 4. indeksini (parity bitini) bozduk
    
    # 4. Decoder ile hatayı tespit et ve çöz
    cozulen_veri = decoder.decode(bozuk_veri)
    
    print("=== HAMMING (7,4) UÇTAN UCA HATA DÜZELTME TESTİ ===")
    print(f"1. Orijinal Veri (8 bit)   : {orijinal_veri}")
    print(f"2. Kodlanmış Veri (14 bit) : {kodlu_veri}")
    print(f"3. Kanalda Bozulan Veri    : {bozuk_veri}  <-- (2 adet bit hatası var!)")
    print(f"4. Çözülen (Kurtarılan)    : {cozulen_veri}")
    
    basari = np.array_equal(orijinal_veri, cozulen_veri)
   