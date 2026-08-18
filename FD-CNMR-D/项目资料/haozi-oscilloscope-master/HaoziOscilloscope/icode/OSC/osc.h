#ifndef __OSC_H
#define __OSC_H

/*
	author：Haozi
	
	Author URI：https://blog.csdn.net/weixin_46253745
	
	Describe：获取ADC的值，并利用GUI进行显示
*/

#include "stdint.h"		// uint16_t 定义

extern uint8_t oscState;

void setAdcFrequency(uint8_t t);
void setWaveEnlarge(uint8_t inc);
void setWaveOffset(uint8_t inc);

void OSC_Init(void);
void updateWaveFrequency(void);
void OSC_ShowWave(void);
void OSC_ShowInfo(void);

#endif


