#ifndef __WAVEFORM_GENERATOR_H
#define __WAVEFORM_GENERATOR_H
#include "main.h"
#define M_PI 3.1415
#define WAVE_POINTS 50  // ???????
#define DAC_RESOLUTION 4095  // 12-bit DAC

typedef enum {
    WAVE_SINE,
    WAVE_TRIANGLE,
    WAVE_SQUARE
} WaveformType;

typedef struct {
    WaveformType type;
    uint16_t frequency;  // ?? (5-50Hz)
    uint16_t amplitude;  // ?? (0-2047)
    uint16_t offset;     // ???? (2048±amplitude)
} WaveformParams;

void update_waveform_buffer(uint16_t *buffer);
void set_waveform_parameters(WaveformType type, uint16_t freq, uint16_t amp);

extern WaveformParams current_wave;
#endif
