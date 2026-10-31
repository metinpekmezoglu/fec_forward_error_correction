import struct
import numpy as np
from dataclasses import dataclass

@dataclass
class TelemetryData:
    """İHA / Model Uydu Telemetri Veri Yapısı"""
    packet_id: int      # Paket Sayacı (0 - 65535)
    altitude: float     # İrtifa (metre)
    pressure: float     # Atmosferik Basınç (Pascal)
    voltage: float      # Görev Yükü Pil Voltajı (Volt)


class TelemetryPacket:
    """
    Sensör verilerini binary (bit) akışına dönüştüren (Serialization/Framing)
    ve alıcıda tekrar anlamlı mühendislik verilerine çözen modül.
    
    Paket Yapısı (<Hfff):
    - '<' : Little-Endian byte sıralaması (STM32/ARM uyumlu)
    - 'H' : uint16 (2 Byte) -> packet_id
    - 'f' : float32 (4 Byte) -> altitude
    - 'f' : float32 (4 Byte) -> pressure
    - 'f' : float32 (4 Byte) -> voltage
    Toplam: 14 Byte = 112 Bit
    """
    FORMAT = '<Hfff'
    BYTE_SIZE = struct.calcsize(FORMAT)  # 14 Byte
    BIT_SIZE = BYTE_SIZE * 8             # 112 Bit

    @classmethod
    def pack_to_bits(cls, data: TelemetryData) -> np.ndarray:
        """
        TelemetryData nesnesini alır, önce 14 Byte'lık binary pakete,
        ardından RF kanala ve FEC kodlayıcıya girecek 112 elemanlı (0 ve 1) bit dizisine çevirir.
        """
        raw_bytes = struct.pack(
            cls.FORMAT,
            data.packet_id,
            data.altitude,
            data.pressure,
            data.voltage
        )
        # Byte dizisini (uint8) 0 ve 1 bitlerine aç
        byte_array = np.frombuffer(raw_bytes, dtype=np.uint8)
        return np.unpackbits(byte_array)

    @classmethod
    def unpack_from_bits(cls, bits: np.ndarray) -> TelemetryData:
        """
        FEC çözücüden çıkan 112 bitlik diziyi tekrar 14 Byte'a paketler
        ve sensör değerlerine (TelemetryData) dönüştürür.
        """
        if len(bits) < cls.BIT_SIZE:
            raise ValueError(f"Paket çözülemedi: En az {cls.BIT_SIZE} bit gerekli, {len(bits)} bit geldi.")

        # İlk 112 biti al ve 14 Byte'a sıkıştır
        clean_bits = bits[:cls.BIT_SIZE].astype(np.uint8)
        raw_bytes = np.packbits(clean_bits).tobytes()

        # Binary Byte'ları değişkenlere çöz
        packet_id, alt, press, volt = struct.unpack(cls.FORMAT, raw_bytes)
        
        return TelemetryData(
            packet_id=int(packet_id),
            altitude=round(float(alt), 2),
            pressure=round(float(press), 1),
            voltage=round(float(volt), 2)
        )


# --- HIZLI DOĞRULAMA TESTİ ---
if __name__ == "__main__":
    # 1. Örnek bir uçuş telemetri verisi oluştur
    tx_data = TelemetryData(packet_id=42, altitude=645.75, pressure=93850.5, voltage=11.85)
    print("=== 1. Gönderilen Telemetri Paketi ===")
    print(tx_data)

    # 2. Veriyi 112 bitlik (0 ve 1) diziye çevir
    tx_bits = TelemetryPacket.pack_to_bits(tx_data)
    print(f"\n=== 2. Binary Bit Akışı ({len(tx_bits)} Bit) ===")
    print(f"İlk 32 Bit: {tx_bits[:32]}")

    # 3. Alıcıda bitleri tekrar telemetri verisine çöz
    rx_data = TelemetryPacket.unpack_from_bits(tx_bits)
    print("\n=== 3. Alıcıda Çözülen Telemetri Paketi ===")
    print(rx_data)