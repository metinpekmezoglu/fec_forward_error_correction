import numpy as np
from reedsolo import RSCodec, ReedSolomonError

class FECDecoder:
    """
    İHA ve Model Uydu Telemetri Sistemi için İleri Hata Düzeltme (FEC) Çözücü.
    - Sendrom (Syndrome) tabanlı Hamming(7,4) hata düzeltme
    - Reed-Solomon hata çözme algoritmalarını içerir.
    """

    def __init__(self, rs_nsym: int = 10):
        # Hamming(7,4) Eşlik Kontrol Matrisi: H = [P^T | I_3] (Boyut: 3x7)
        self.H = np.array([
            [1, 1, 0, 1, 1, 0, 0],
            [1, 0, 1, 1, 0, 1, 0],
            [0, 1, 1, 1, 0, 0, 1]
        ], dtype=np.uint8)

        # H matrisinin sütunlarını hızlı arama (Lookup Table) için tam sayıya (1..7) eşle
        self.syndrome_map = {}
        weights = np.array([4, 2, 1], dtype=np.uint8)
        for col_idx in range(7):
            syndrome_val = int(np.dot(weights, self.H[:, col_idx]))
            self.syndrome_map[syndrome_val] = col_idx

        self.rs_nsym = rs_nsym
        self.rs_codec = RSCodec(rs_nsym)

    def decode_hamming(self, received_bits: np.ndarray, original_bit_len: int = None) -> np.ndarray:
        """
        Alınan 7'li blokların sendromunu (S = R * H^T mod 2) hesaplar,
        tek bitlik hataları tespit edip ters çevirerek (XOR) düzeltir.
        """
        blocks = received_bits.astype(np.uint8).reshape(-1, 7).copy()

        # Tüm bloklar için tek seferde Sendrom Hesabı: S = (R @ H^T) % 2
        syndromes = np.matmul(blocks, self.H.T) % 2

        # 3-bitlik sendromları onluk tabanda tam sayıya çevir (0 ise hata yok, 1..7 ise hata var)
        weights = np.array([4, 2, 1], dtype=np.uint8)
        syndrome_ints = np.dot(syndromes, weights)

        # Sadece sendromu 0 OLMAYAN (hatalı) blokları bul ve ilgili biti ters çevir
        error_block_indices = np.nonzero(syndrome_ints)[0]
        for blk_idx in error_block_indices:
            s_val = int(syndrome_ints[blk_idx])
            corrupted_bit_pos = self.syndrome_map[s_val]
            blocks[blk_idx, corrupted_bit_pos] ^= 1

        # Sistematik kodda ilk 4 sütun orijinal veridir
        decoded_bits = blocks[:, :4].flatten()

        if original_bit_len is not None:
            return decoded_bits[:original_bit_len]
        return decoded_bits

    def decode_rs(self, received_bits: np.ndarray, original_bit_len: int) -> np.ndarray:
        """
        Alınan bitleri Byte'lara çevirir ve Reed-Solomon çözücüden geçirir.
        """
        rx_bytes = np.packbits(received_bits.astype(np.uint8)).tobytes()
        try:
            decoded_bytearray, _, _ = self.rs_codec.decode(rx_bytes)
            decoded_bits = np.unpackbits(np.frombuffer(bytes(decoded_bytearray), dtype=np.uint8))
            return decoded_bits[:original_bit_len]
        except ReedSolomonError:
            return received_bits[:original_bit_len].astype(np.uint8)


# --- HIZLI DOĞRULAMA TESTİ ---
if __name__ == "__main__":
    from encoder import FECEncoder

    enc = FECEncoder(rs_nsym=4)
    dec = FECDecoder(rs_nsym=4)

    # 1. Hamming(7,4) Testi: 4 bit veri gönder, kanalda 1 bitini kasten boz!
    veri = np.array([1, 0, 1, 1], dtype=np.uint8)
    kodlu = enc.encode_hamming(veri)
    print("=== 1. Hamming(7,4) Testi ===")
    print(f"Orijinal 4 Bit Veri : {veri}")
    print(f"Kodlanmış 7 Bit (c) : {kodlu}")

    bozuk = kodlu.copy()
    bozuk[2] ^= 1
    print(f"Kanalda Bozulan (r) : {bozuk}  <-- 3. bit (indeks 2) bozuldu!")

    cozulen = dec.decode_hamming(bozuk, original_bit_len=4)
    print(f"Onarılan Çıkış Bit  : {cozulen}  <-- %100 Kurtarıldı!\n")

    # 2. Reed-Solomon Testi: 16 bit (2 Byte) veri gönder, ardışık 5 biti (Burst Error) boz!
    veri_rs = np.array([1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1], dtype=np.uint8)
    kodlu