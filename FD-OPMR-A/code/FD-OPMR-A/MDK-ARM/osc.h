#ifndef __OSC_H
#define __OSC_H
//void delay_us(uint32_t us);
//void delay_ms(uint32_t ms);
//测量值取Num个平均值，波形取K个平均值,采样点数量S
#define Num 3
#define K 1
#define S 4000
#define DelayTime 0
#define DelayTime2 0
#define grid_up 12
#define grid_down 397
#define grid_left 83
#define half_txt_height 15
#define DATA_NUM 451 //串口屏每次刷新波形点数

typedef enum
{
	FREE,
	CH1_PREPARING,
	CH1_PREPARE_OK,
	CH1_SENDING,
	CH1_SEND_OK,
	CH2_PREPARING,
	CH2_PREPARE_OK,
	CH2_SENDING,
	CH2_SEND_OK,
}OSC_STATE;

extern OSC_STATE osc_state;
typedef enum
{
	_10V=0,
	_5V=1,
	_2V=2,
	_1V=3,
	_500mV=4,
	_200mV=5,
	_100mV=6,
	_50mV=7,
	_20mV=8,
	_10mV=9,
}VOLTAGE_PER_GRID;	

typedef enum
{
	_100ms=0,
	_50ms=1,
	_20ms=2,
	_10ms=3,
	_5ms=4,
	_2ms=5,
	_1ms=6,
	_500us=7,
	_200us=8,
	_100us=9,
	_50us=10,
	_20us=11,
	_10us=12,
	_5us=13,
	_2us=14
}TIME_PER_GRID;

void display_osc(void);
void doKey(void);
void Key0_scan(void);
void Init_Osc(void);
void renew_data(void);
void ADC_8CH(void);		
void ADC_DMA(void);
void set_offset_ch1(int16_t offset);
void set_offset_ch2(int16_t offset);
void delay_us(uint32_t nus);
void delay_ms(uint16_t nms);
extern uint16_t x1,x2,y1,y2,step;
extern uint8_t menu_status,Ouhe,Ouhe1,Channel,time_per_grid,voltage_per_grid,Trigger_state,voltage_per_grid_1,cursor_status,hengzong,cursor_num;;
extern uint16_t i,j,mem2[S*K];
extern int16_t ad1[S*K],ad2[S*K],offset_ch1,offset_ch2,offset;
extern uint8_t Trigger_set;
extern int16_t TriggerPoint,Trigger_set_offset_ch1,Trigger_set_offset_ch2;
extern _Bool CH1_enable,CH2_enable,xy_enable,tim3_flag,CH1_status,CH2_status,fft_enable,get_freq_enable;
extern int32_t temp,temp0;
extern int tim1ch1flag,tim1ch2flag,tim1ch3flag,tim1ch4flag,dmatxflag;
extern uint8_t menu2_status,parament_flag;
extern int16_t caliboration_ch1,caliboration_ch2;
extern uint8_t Trigger_ANS,single_flag;
extern uint32_t freq_counter;
extern uint8_t single_flag_1,single_flag_2,cursor_switch,cursor_mode;
extern float del_zero_ch1,del_zero_ch2,del_k_ch1,del_k_ch2;
extern int8_t caliboration_mode,calibo_ch;
extern float calibo_step_zero,calibo_step_k;
extern HAL_StatusTypeDef UART4_DMA_Send(uint8_t *data, uint16_t size);
#endif

