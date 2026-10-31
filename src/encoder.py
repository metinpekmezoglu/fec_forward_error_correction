import numpy as np

class Hamming74Encoder:
    """
    Sistematik Hamming (7,4) Blok Kodlayıcı.
    4 bitlik mesaj vektörlerini (d), 7 bitlik kod kelimelerine (c) dönüştürür.
    Kod Oranı (Code Rate): R = k / n = 4 / 7 (~0.571)
    """
    def __init__(self):
        self.n = 7  # Kod kelimesi uzunluğu
        self.k = 4  # Mesaj biti uzunluğu
        
        # Parity (Eşlik) Alt Matrisi P (4x3)
        self.P = np.array([
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1]
        ], dtype=int)
        
        # Birim Matrisler
        self.I_k = np.eye(self.k, dtype=int)          # 4x4 Birim Matris
        self.I_nk = np.eye(self.n - self.k, dtype=int) # 3x3 Birim Matris
        
        # Sistematik Üreteç Matrisi: G = [I_4 | P] (4x7)
        self.G = np.hstack((self.I_k, self.P))
        
        # Eşlik Denetim Matrisi: H = [P^T | I_3] (3x7) -> Decoder için referans
        self.H = np.hstack((self.P.T, self.I_nk))

    def encode(self, data: np.ndarray) -> np.ndarray:
        """
        Gelen 1D bit dizisini 4'erli bloklara ayırır ve G matrisi ile çarpar.
        Eğer veri uzunluğu 4'ün tam katı değilse sonuna sıfır ekler (zero-padding).
        """
        data = np.asarray(data, dtype=int)
        
        # Uzunluk 4'ün katı değilse eksik kalan kısmı 0 ile tamamla
        remainder = len(data) % self.k
        if remainder != 0:
            pad_len = self.k - remainder
            data = np.pad(data, (0, pad_len), 'constant', constant_values=0)
            
        # Veriyi (N, 4) boyutunda matrise dönüştür
        num_blocks = len(data) // self.k
        data_blocks = data.reshape((num_blocks, self.k))
        
        # Matris çarpımı ve Mod 2 (GF(2) aritmetiği / XOR eşdeğeri)
        encoded_blocks = np.dot(data_blocks, self.G) % 2
        
        # Tekrar 1D dizi (vektör) haline getirip döndür
        return encoded_blocks.flatten()


# --- TEST KISMI ---
if __name__ == "__main__":
    encoder = Hamming74Encoder()
    
    print("=== 1. Üreteç Matrisi (G) [4x7] ===")
    print(encoder.G)
    
    print("\n=== 2. Eşlik Denetim Matrisi (H) [3x7] ===")
    print(encoder.H)
    
    # Doğrulama: G * H^T (Mod 2) her zaman sıfır matrisi olmalıdır!
    orthogonality_check = np.dot(encoder.G, encoder.H.T) % 2
    print("\n=== 3. Diklik Kontrolü (G * H^T mod 2 == 0) ===")
    print(orthogonality_check)
    
    # Örnek 8 bitlik (2 blok) veri kodlama testi
    ornek_veri = np.array([1, 0, 1, 1,   0, 1, 1, 0])
    kodlanmis_veri = encoder.encode(ornek_veri)
    
    print("\n=== 4. Kodlama Testi ===")
    print(f"Giriş Verisi (8 bit)     : {ornek_veri}")
    print(f"Kodlanmış Çıkış (14 bit) : {kodlanmis_veri}")
    print(f"1. Blok: {ornek_veri[:4]} -> {kodlanmis_veri[:7]} (İlk 4 bit veri, son 3 bit parity)")
    print(f"2. Blok: {ornek_veri[4:]} -> {kodlanmis_veri[7:]}")