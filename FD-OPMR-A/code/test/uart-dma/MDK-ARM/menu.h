#ifndef __MENU_H
#define __MENU_H

typedef enum
{
	T_LIGHT=0,
	T_POOL=1,
	CTRL=2,
	I_HORI=3,
	I_VERT=4,
	I_SCAN=5,
	SCAN_SHAPE=6,
	FREQ=7,
	TIME_GRID=8,
	MAG_SCALE=9,
	LIGHT_SCALE=10,
	TRIG_MODE=11,
	MAG_OFFSET=12,
	LIGHT_OFFSET=13,
	TRIG_VALUE=14,
	MAG_COUPLE=15,
	LIGHT_COUPLE=16,
	CALIBO=17
}CURSOR;

typedef enum
{
	NONE=0,
	CH1_OFFSET=1,
	CH1_K_1=2,
	CH1_K_2=3,
	CH2_OFFSET=4,
	CH2_K_1=5,
	CH2_K_2=6,
	SAVE=7
}CALIBORATION_STATE;

#define scan_shape_max 3
#define time_grid_max 3
#define mag_scale_max 5
#define light_scale_max 3

void right_button();
void left_button();
void up_button();
void down_button();
void confirm_button();
void fun_button();
void cancel_button();
void renew_menu();

extern _Bool start_ctrl;
extern float temp_light_set,temp_pool_set,temp_pool_now,temp_light_now,current_hori,current_vert,current_scan;
extern uint16_t freq_scan;
extern uint8_t scan_shape_now,time_grid_now,mag_scale_now,light_scale_now,trig_mode_now;
extern CALIBORATION_STATE caliboration_state;
#endif