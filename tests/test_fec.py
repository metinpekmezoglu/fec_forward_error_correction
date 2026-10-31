import os
import sys
import numpy as np

# Dosya nereden çalıştırılırsa çalıştırılsın proje ana dizinini Python'a tanıtır
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.channel import RFChannel
from src.encoder import FECEncoder
from src.decoder import FECDecoder
from src.telemetry import TelemetryData, TelemetryPacket


def test_telemetry_pack_unpack():
    """Telemetri verisinin 112 bite paketlenip kayıpsız çözüldüğünü doğrular."""
    original = TelemetryData(packet_id=255, altitude=1250.5, pressure=89500.2, voltage=11.45)
    bits = TelemetryPacket.pack_to_bits(original)
    
    assert len(bits) == 112
    assert bits.dtype == np.uint8

    recovered = TelemetryPacket.unpack_from_bits(bits)
    assert recovered == original


def test_hamming_single_bit_error_correction():
    """Hamming(7,4) kodunun 7 bitlik bloktaki her olası tek bitlik hatayı %100 düzelttiğini doğrular."""
    encoder = FECEncoder()
    decoder = FECDecoder()
    data_bits = np.array([1, 0, 1, 1], dtype=np.uint8)
    encoded = encoder.encode_hamming(data_bits)

    # 7 bitin her birini sırayla tek tek boz ve çözücünün her seferinde kurtardığını test et
    for bit_pos in range(7):
        corrupted = encoded.copy()
        corrupted[bit_pos] ^= 1
        decoded = decoder.decode_hamming(corrupted, original_bit_len=4)
        assert np.array_equal(data_bits, decoded), f"Bit {bit_pos} hatası düzeltilemedi!"


def test_reed_solomon_burst_error_correction():
    """Reed-Solomon(24,14) kodunun ardışık 24 bitlik (3 Byte) ağır burst hatasını düzelttiğini doğrular."""
    encoder = FECEncoder(rs_nsym=10)
    decoder = FECDecoder(rs_nsym=10)

    sample = TelemetryData(packet_id=7, altitude=300.0, pressure=100000.0, voltage=12.0)
    tx_bits = TelemetryPacket.pack_to_bits(sample)
    encoded_bits = encoder.encode_rs(tx_bits)

    # Yan yana 24 biti (3 Byte) tamamen ters çevir (Burst Error)
    corrupted_bits = encoded_bits.copy()
    corrupted_bits[16:40] ^= 1

    decoded_bits = decoder.decode_rs(corrupted_bits, original_bit_len=len(tx_bits))
    assert np.array_equal(tx_bits, decoded_bits), "Reed-Solomon burst hatasını düzeltemedi!"


def test_channel_bsc_bounds():
    """BSC kanalında p=0 iken hiç hata olmadığını, p=1 iken tüm bitlerin ters döndüğünü doğrular."""
    channel = RFChannel(seed=10)
    bits = np.array([1, 0, 1, 0, 1, 1, 0, 0], dtype=np.uint8)

    assert np.array_equal(channel.bsc(bits, p_error=0.0), bits)
    assert np.array_equal(channel.bsc(bits, p_error=1.0), 1 - bits)


if __name__ == "__main__":
    import pytest
    # Dosya doğrudan çalıştırıldığında pytest'i otomatik tetikler
    sys.exit(pytest.main(["-v", __file__]))