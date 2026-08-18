#ifndef __OSC_H
#define __OSC_H


void display_osc(void);
void doKey(void);
void Key0_scan(void);
void Init_Osc(void);
void renew_data(void);

void delay_us(uint32_t nus);
void delay_ms(uint16_t nms);

extern _Bool dac_need_update;
#endif

