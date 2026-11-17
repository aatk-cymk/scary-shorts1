import ctypes, wave, sys, numpy as np
import espeakng_loader as e

lib = ctypes.CDLL(e.get_library_path())
RETRIEVAL = 1
rate = lib.espeak_Initialize(RETRIEVAL, 0, e.get_data_path().encode(), 0)
samples = []
CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)

@CB
def cb(wav, n, events):
    if wav and n > 0:
        samples.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
    return 0

lib.espeak_SetSynthCallback(cb)
lib.espeak_SetVoiceByName(b"en-us+m3")
lib.espeak_SetParameter(1, 130, 0)  # rate wpm
lib.espeak_SetParameter(3, 30, 0)   # pitch
lib.espeak_SetParameter(4, 20, 0)   # range


def synth(text, out):
    samples.clear()
    b = text.encode()
    lib.espeak_Synth(b, len(b) + 1, 0, 0, 0, 0x1000 | 0, None, None)  # espeakCHARS_AUTO, SSML off
    lib.espeak_Synchronize()
    data = np.concatenate(samples) if samples else np.zeros(1, np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data.tobytes())
    return len(data) / rate

if __name__ == "__main__":
    print(synth(sys.argv[1], sys.argv[2]))
