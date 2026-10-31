import numpy as np
from reedsolo import RSCodec

class FECEncoder:
    """
    İHA ve Model Uydu Telemetri Sistemi için İleri Hata Düzeltme (FEC) Kodlayıcı.
    - Bit seviyesinde Hamming(7,4) blok kodlama (Matris tabanlı)
    - Byte/Sembol seviyesinde Reed-Solomon kodlama içerir.
    """

    def __init__(self, rs_nsym: int = 10):
        """
        Parametreler:
            rs_nsym (int): Reed-Solomon için eklenecek hata düzeltme sembol (byte) sayısı.
                           Varsayılan 10 byte (nsym/2 = 5 byte'a kadar ardışık hatayı düzeltir).
        """
        # Hamming(7,4) Sistematik Üreteç Matrisi: G = [I_4 | P] (Boyut: 4x7)
        self.G = np.array([
            [1, 0, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 0, 1],
            [0, 0, 1, 0, 0, 1, 1],
            [0, 0, 0, 1, 1, 1, 1]
        ], dtype=np.uint8)

        self.rs_nsym = rs_nsym
        self.rs_codec = RSCodec(rs_nsym)

    def encode_hamming(self, bits: np.ndarray) -> np.ndarray:
        """
        Giriş bit dizisini 4'lü bloklara ayırır ve G matrisi ile çarparak
        7'li Hamming kod kelimelerine dönüştürür.

        Parametreler:
            bits (np.ndarray): Kodlanacak 0 ve 1'lerden oluşan 1 boyutlu dizi.

        Dönüş:
            np.ndarray: Hamming(7,4) ile kodlanmış bit dizisi.
        """
        bits = bits.astype(np.uint8)
        
        # 1. Padding (Dolgu): Bit sayısı 4'ün tam katı değilse sonuna 0 ekle
        remainder = len(bits) % 4
        if remainder != 0:
            pad_len = 4 - remainder
            bits = np.append(bits, np.zeros(pad_len, dtype=np.uint8))

        # 2. Vektörü (N, 4) boyutunda matrise dönüştür (Her satır 4 bitlik bir veri bloğu)
        data_blocks = bits.reshape(-1, 4)

        # 3. Galois Alanı GF(2) Matris Çarpımı: C = (D @ G) % 2
        encoded_blocks = np.matmul(data_blocks, self.G) % 2

        # 4. Matrisi tekrar 1 boyutlu bit akışına (stream) düzleştir
        return encoded_blocks.flatten().astype(np.uint8)

    def encode_rs(self, bits: np.ndarray) -> np.ndarray:
        """
        Bit dizisini Byte'lara paketler, Reed-Solomon eşlik byte'larını ekler
        ve kanala gönderilmek üzere tekrar bit dizisine (uint8) dönüştürür.

        Parametreler:
            bits (np.ndarray): Kodlanacak bit dizisi (8'in katı uzunlukta).

        Dönüş:
            np.ndarray: Reed-Solomon ile kodlanmış bit dizisi.
        """
        # 1. Bitleri Byte dizisine çevir (Örn: 112 bit -> 14 Byte)
        raw_bytes = np.packbits(bits.astype(np.uint8)).tobytes()

        # 2. Reed-Solomon Kodlaması (14 Byte veri + 10 Byte Parity = 24 Byte)
        encoded_bytearray = self.rs_codec.encode(raw_bytes)

        # 3. Kodlanmış Byte'ları kanala basmak için tekrar 0 ve 1 bitlerine aç (192 bit)
        encoded_bits = np.unpackbits(np.frombuffer(bytes(encoded_bytearray), dtype=np.uint8))
        return encoded_bits