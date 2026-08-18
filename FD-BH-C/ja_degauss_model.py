# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

class DegaussModel:
    """Pure mathematical scaling - no boundary tracking"""
    
    def __init__(self, B_sat=314.0, Br_ratio=0.24):
        self.B_sat = B_sat
        self.Br_ratio = Br_ratio
        self.I_max = 600.0
        
        self._I = 0.0
        self._B = 0.0
        self._dir = 0
        self._turn_I = 0.0
        self._turn_B = 0.0
        self._amp = 600.0
        
    def _curve(self, I, amp, offset_sign):
        """Hysteresis curve with given amplitude and offset direction"""
        if amp < 1:
            return 0
        scale = amp / self.I_max
        I_norm = I / amp
        B_base = self.B_sat * scale * np.tanh(1.5 * I_norm)
        Br = self.B_sat * self.Br_ratio * scale
        offset = Br * (1 - abs(np.tanh(1.2 * I_norm)))
        return B_base + offset_sign * offset
    
    def set_initial_remanence(self, Br):
        self._B = Br
        self._I = 0.0
        self._dir = 0
        self._turn_I = 0.0
        self._turn_B = Br
        
    def set_amplitude(self, amp):
        self._amp = amp
        
    def get_B(self, I):
        dI = I - self._I
        if abs(dI) < 0.5:
            return self._B
        
        new_dir = 1 if dI > 0 else -1
        
        if self._dir != 0 and new_dir != self._dir:
            self._turn_I = self._I
            self._turn_B = self._B
        
        self._dir = new_dir
        
        # Target: upper branch when going down, lower when going up
        offset_sign = 1 if new_dir < 0 else -1
        B_target = self._curve(I, self._amp, offset_sign)
        
        # Smooth transition
        dI_travel = abs(I - self._turn_I)
        I_range = 2 * self._amp
        progress = min(1.0, dI_travel / I_range) if I_range > 1 else 0
        t = progress * progress * (3 - 2 * progress)
        
        B_new = self._turn_B + (B_target - self._turn_B) * t
        
        # Clamp to current amplitude's envelope only
        B_up = self._curve(I, self._amp, 1)
        B_lo = self._curve(I, self._amp, -1)
        B_new = np.clip(B_new, B_lo, B_up)
        
        self._I = I
        self._B = B_new
        return B_new


def test():
    m = DegaussModel(B_sat=314.0, Br_ratio=0.24)
    m.set_initial_remanence(75.0)
    
    Is, Bs = [], []
    amps = [600, 500, 400, 300, 200, 100]
    
    for i, amp in enumerate(amps):
        polarity = 1 if i % 2 == 0 else -1
        m.set_amplitude(amp)
        
        for I in np.linspace(0, polarity * amp, 300):
            Is.append(I)
            Bs.append(m.get_B(I))
        
        for I in np.linspace(polarity * amp, 0, 300):
            Is.append(I)
            Bs.append(m.get_B(I))
    
    Hs = [I * 2943 / 600 for I in Is]
    
    plt.figure(figsize=(10, 8))
    plt.plot(Hs, Bs, 'b-', lw=1.2)
    plt.xlabel('H (A/m)')
    plt.ylabel('B (mT)')
    plt.title('Degauss Model')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', lw=0.5)
    plt.axvline(x=0, color='k', lw=0.5)
    plt.plot(Hs[0], Bs[0], 'ro', ms=8, label='Start')
    plt.plot(Hs[-1], Bs[-1], 'gs', ms=8, label='End')
    plt.legend()
    plt.tight_layout()
    plt.savefig('degauss_model_test.png', dpi=150)
    print(f'Start: B={Bs[0]:.1f}mT, End: B={Bs[-1]:.1f}mT')
    plt.show()

if __name__ == '__main__':
    test()
