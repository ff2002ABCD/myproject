#include "waveform_generator.h"
#include <math.h>

WaveformParams current_wave = {
    .type = WAVE_SINE,
    .frequency = 50,
    .amplitude = 2000,
    .offset = 2048
};


void generate_sine_wave(uint16_t *buffer, uint16_t points) {
    for(uint16_t i = 0; i < points; i++) {
        float angle = 2 * M_PI * i / points;
        buffer[i] = current_wave.offset + current_wave.amplitude * sin(angle);
    }
}


void generate_triangle_wave(uint16_t *buffer, uint16_t points) {
    uint16_t half = points / 2;
    for(uint16_t i = 0; i < points; i++) {
        if(i < half) {
            buffer[i] = current_wave.offset + current_wave.amplitude * (2.0 * i / half - 1.0);
        } else {
            buffer[i] = current_wave.offset + current_wave.amplitude * (3.0 - 2.0 * i / half);
        }
    }
}


void generate_square_wave(uint16_t *buffer, uint16_t points) {
    uint16_t half = points / 2;
    for(uint16_t i = 0; i < points; i++) {
        buffer[i] = (i < half) ? 
                   (current_wave.offset + current_wave.amplitude) : 
                   (current_wave.offset - current_wave.amplitude);
    }
}


void update_waveform_buffer(uint16_t *buffer) {
    switch(current_wave.type) {
        case WAVE_SINE:
            generate_sine_wave(buffer, WAVE_POINTS);
            break;
        case WAVE_TRIANGLE:
            generate_triangle_wave(buffer, WAVE_POINTS);
            break;
        case WAVE_SQUARE:
            generate_square_wave(buffer, WAVE_POINTS);
            break;
    }
}


void set_waveform_parameters(WaveformType type, uint16_t freq, uint16_t amp) {
    current_wave.type = type;
    current_wave.frequency = (freq < 5) ? 5 : (freq > 50) ? 50 : freq;
    current_wave.amplitude = (amp > 2047) ? 2047 : amp;
    current_wave.offset = 2048;  
}