# =====================================================================
# FIRE SOUND ENGINE
# =====================================================================
# What this does:
#   You show a photo of a fire map. This code plays a sound that matches it.
#   More fire detections = scarier sound.
#   More fire power (MW)  = louder sound.
#
# When you click next / previous, the sound does NOT jump or cut.
# It slowly slides from the old sound to the new one.
#
# Install once:  pip install sounddevice numpy
# =====================================================================

import numpy as np           
import sounddevice as sd    

# ---------------------------------------------------------------------
# SETTINGS YOU CAN PLAY WITH
# ---------------------------------------------------------------------
SR = 44100        # quality of the sound (samples per second)
BLOCK = 1024      # the sound is made in small pieces of this size
GLIDE = 1.0       # seconds to slide from one photo's sound to the next
                  # (0.3 = fast change, 3 = very slow change)
GAIN = 0.2        # master volume

# --- Fire power (volume) ---
FRP_MAX = 80.0    # the strongest fire we expect, in megawatts (MW).
                  # A photo with 80 MW gets the maximum volume.
POWER_CURVE = 0.5 # makes weak fires louder. 1 = no boost,
                  # 0.5 = good boost (square root), 0.3 = very strong boost
V_MIN = 0.15      # quietest allowed volume, so we always hear a little

# --- Main sound ---
F_BASE = 440.0    # the main note (Hz). It never changes.
BEAT_MAX = 30.0   # the 2nd note goes up to this many Hz above the main note.
                  # Two close notes together make a "wobbling" sound.
DRONE_F0 = 110.0  # low background note (Hz) when there is no fire
DRONE_DROP = 45.0 # the low note goes down by this much when the fire is big
R_MIN = 0.5       # slowest wobble (times per second)
R_RANGE = 5.0     # how much faster the wobble gets with big fires
TREMOLO_DEPTH = 0.6 # how strong the wobble is (0 = none, 1 = maximum)
EXP_K = 3.0       # higher = sound stays calm longer, then gets scary fast

# --- Scary effects (put 0 to turn one off) ---
DISSONANCE = 0.8    # adds an "unpleasant" note when the fire grows
NOISE_AMOUNT = 0.1  # crackling noise, like burning wood
DISTORTION = 3.5    # makes the sound harsh and aggressive
SUB_BOOST = 0.7     # deep rumble you feel more than you hear

TWO_PI = 2 * np.pi  # one full turn of a wave (maths constant)


# =====================================================================
# THE SOUND ENGINE
# =====================================================================
class FireSound:
    def __init__(self, N, FRP):
        # N   = number of fire detections, one number per photo
        # FRP = total fire power in MW, one number per photo
        N = np.array(N, dtype=float)
        FRP = np.array(FRP, dtype=float)

        # Keep the raw data so we can show it next to the photo number
        self.N = N
        self.FRP = FRP

        # ----- Step A: turn the data into numbers between 0 and 1 -----

        # I = "how many fires", from 0 (none) to 1 (the most we have).
        # We use a log so a photo with 3000 fires doesn't make a photo
        # with 50 fires sound like nothing.
        I = np.log1p(N) / np.log1p(N.max())

        # E = same idea, but it stays small for a long time and then
        # shoots up. Big fires will feel much more dramatic.
        E = (np.exp(EXP_K * I) - 1) / (np.exp(EXP_K) - 1)

        # P = "how powerful", from 0 to 1, based on the megawatts.
        # We compare to FRP_MAX (80 MW), not to the biggest photo.
        # np.clip makes sure P never goes above 1.
        P = np.log1p(FRP) / np.log1p(FRP_MAX)
        P = np.clip(P, 0, 1)

        # Boost the weak values so small fires are still audible.
        P = P ** POWER_CURVE

        # ----- Step B: turn those numbers into sound settings -----
        f_2 = F_BASE + BEAT_MAX * I          # 2nd note: goes up with the fires
        f_drone = DRONE_F0 - DRONE_DROP * E  # low note: goes down (heavier feeling)
        R = R_MIN + R_RANGE * E              # wobble speed: faster with more fires
        vol = V_MIN + (1 - V_MIN) * P        # volume: louder with more power

        # One row per photo. Columns: [f_2, f_drone, R, E, vol]
        self.targets = np.column_stack([f_2, f_drone, R, E, vol])

        self.n_frames = len(N)  # how many photos we have
        self.index = 0          # which photo we are on (0 = the first one)

        # ----- Memory of the sound -----
        # cur = the settings the sound uses right now.
        # They move slowly toward the new photo's settings.
        # This is what makes the smooth slide.
        self.cur = self.targets[0].copy()

        # Each wave remembers where it is in its cycle.
        # If we restarted the waves at every piece, we would hear clicks.
        # 6 waves: main note, 2nd note, low note, deep rumble,
        # unpleasant note, wobble.
        self.phases = np.zeros(6)

        # Random number generator, used for the crackling
        self.rng = np.random.default_rng(0)

        # Prepare the sound output. It does not play yet.
        # The computer will call _callback again and again to ask for sound.
        self.stream = sd.OutputStream(samplerate=SR, blocksize=BLOCK,
                                      channels=1, callback=self._callback)

    # ---------------- Buttons you can connect to your app ----------------
    def start(self):
        """Start the sound."""
        self.stream.start()

    def stop(self):
        """Stop the sound. Call this when you close the app."""
        self.stream.stop()

    def set_frame(self, i):
        """Jump to photo number i (0 = first photo)."""
        # np.clip stops us from going before the first or after the last photo
        self.index = int(np.clip(i, 0, self.n_frames - 1))

    def next(self):
        """Go to the next photo."""
        self.set_frame(self.index + 1)

    def previous(self):
        """Go to the previous photo."""
        self.set_frame(self.index - 1)

    # ---------------- Small helper: makes one wave ----------------
    def _osc(self, k, freq):
        """
        Gives the "position" of wave number k for this piece of sound.
        freq = the frequency wanted at each moment.
        Later we do sin(position) to get the actual wave.
        """
        # Add up small steps to move forward in the wave.
        # We start from where we stopped last time, so there is no click.
        ph = self.phases[k] + np.cumsum(TWO_PI * freq / SR)
        # Remember where we stopped, for the next piece
        self.phases[k] = ph[-1] % TWO_PI
        return ph

    # ---------------- The part that creates the sound ----------------
    def _callback(self, outdata, frames, time, status):
        # The computer calls this about 40 times per second and says:
        # "give me 'frames' numbers of sound to play".
        # It has to be quick, or the sound will stutter.

        # --- 1. Slide a little toward the current photo's settings ---
        target = self.targets[self.index]              # where we want to go
        a = 1 - np.exp(-frames / SR / GLIDE)           # how big a step to take
        new = self.cur + (target - self.cur) * a       # take that step
        # Make a smooth ramp between old and new settings
        curve = np.linspace(self.cur, new, frames, endpoint=False)
        self.cur = new                                 # remember for next time
        f_2, f_drone, R, E, vol = curve.T              # split into 5 settings

        # --- 2. Move each wave forward ---
        ph_base = self._osc(0, np.full(frames, F_BASE))         # main note
        ph_2 = self._osc(1, f_2)                                # 2nd note
        ph_drone = self._osc(2, f_drone)                        # low note
        ph_sub = self._osc(3, f_drone / 2)                      # deep rumble
        ph_tri = self._osc(4, np.full(frames, F_BASE * 1.414))  # unpleasant note
        ph_R = self._osc(5, R)                                  # wobble

        # --- 3. Build each layer of the sound ---

        # Music: main note + 2nd note + unpleasant note.
        # The unpleasant note is multiplied by E, so it only
        # shows up when the fire is big.
        music = (0.4 * np.sin(ph_base) + 0.4 * np.sin(ph_2)
                 + DISSONANCE * 0.3 * E * np.sin(ph_tri))

        # Low background note. We add higher copies of it (x2, x3)
        # so you can hear it even on small laptop speakers.
        drone = (np.sin(ph_drone) + 0.5 * np.sin(2 * ph_drone)
                 + 0.25 * np.sin(3 * ph_drone)) / 1.75

        # Deep rumble: louder when the fire is bigger
        sub = SUB_BOOST * E * np.sin(ph_sub)

        # Crackling: random noise, kept only at random moments.
        # The bigger the fire, the more often we keep it.
        noise = self.rng.standard_normal(frames)
        crackle = noise * (self.rng.random(frames) < 0.02 + 0.2 * E)
        crackle = NOISE_AMOUNT * E * crackle

        # --- 4. Mix all layers together ---
        mix = 0.5 * music + 0.4 * drone + sub + crackle

        # --- 5. Wobble: the volume goes up and down R times per second ---
        tremolo = (1 - TREMOLO_DEPTH) + TREMOLO_DEPTH * 0.5 * (1 + np.sin(ph_R))
        mix *= tremolo

        # --- 6. Distortion: squash the loud parts to sound harsh ---
        # The bigger the fire (E), the harsher it gets.
        drive = 1 + DISTORTION * E
        mix = np.tanh(drive * mix) / np.tanh(drive)

        # --- 7. Final volume: fire power (MW) and master volume ---
        mix *= vol * GAIN

        # Send to the speakers.
        # np.clip = never go above the maximum (avoids ugly digital noise)
        outdata[:, 0] = np.clip(mix, -1, 1).astype(np.float32)


# =====================================================================
# QUICK TEST (runs only if you start this file directly)
# =====================================================================
if __name__ == "__main__":
    # Example data, one value per photo. Replace with your real data.
    N = [7, 41, 46, 1260, 3214, 1377, 1945, 128, 233, 216, 33, 6, 2, 0]
    FRP = [2, 6, 8, 45, 80, 50, 62, 18, 25, 24, 7, 3, 1, 0]   # MW, max 80

    fs = FireSound(N, FRP)   # create the engine
    fs.start()               # start playing
    print("n = next, p = previous, q = quit")

    while True:
        # Build the text shown before the cursor:
        # photo number, number of detections, and fire power in MW
        i = fs.index
        info = (f"Photo {i + 1}/{fs.n_frames} | "
                f"Detections: {int(fs.N[i])} | "
                f"Power: {fs.FRP[i]:.0f} MW")

        # Wait for you to type a letter and press Enter
        key = input(info + " > ").strip().lower()
        if key == "n":
            fs.next()
        elif key == "p":
            fs.previous()
        elif key == "q":
            break

    fs.stop()                