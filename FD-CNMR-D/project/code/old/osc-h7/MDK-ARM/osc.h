#ifndef __OSC_H
#define __OSC_H
//void delay_us(uint32_t us);
//void delay_ms(uint32_t ms);
#define K 10
#define S 6000
void display_osc(void);
void doKey(void);
void Key0_scan(void);
void Init_Osc(void);
void renew_data(void);
void ADC_8CH(void);		
void ADC_DMA(void);
void set_offset_ch1(int16_t offset);
void set_offset_ch2(int16_t offset);
extern uint16_t x1,x2,y1,y2,step;
extern uint8_t menu_status,Ouhe,Ouhe1,Channel,time_per_grid,voltage_per_grid,Trigger_state,voltage_per_grid_1,cursor_status,hengzong,cursor_num;;
extern uint16_t i,j,mem2[S*K];
extern int16_t ad1[S*K],ad2[S*K],offset_ch1,offset_ch2,offset;
extern uint8_t Trigger_set;
extern int16_t TriggerPoint,Trigger_set_offset;
extern _Bool CH1_enable,CH2_enable,xy_enable,tim3_flag,CH1_status,CH2_status,fft_enable,get_freq_enable;
extern int32_t temp,temp0;
extern int tim1ch1flag,tim1ch2flag,tim1ch3flag,tim1ch4flag,dmatxflag;
extern uint8_t menu2_status,parament_flag;
extern int16_t caliboration_ch1,caliboration_ch2;
extern uint8_t Trigger_ANS,single_flag;
extern uint32_t freq_counter;
extern uint8_t single_flag_1,single_flag_2;
#endif

