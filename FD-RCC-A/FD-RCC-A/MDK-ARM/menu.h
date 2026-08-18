#ifndef __MENU_H
#define __MENU_H

typedef enum
{
	TEMP=0,
	PULSE_WIDTH=1,
	DUTY=2,
	VOL_SUM=3,
	CURSOR_NONE=99
}CURSOR;
extern CURSOR cursor;
#define CURSOR_MAX 4

typedef enum
{
	TEMP1=0,
	TEMP2=1,
	TEMP3=2,
	TEMP4=3, //开始控温
	CURSOR_TEMP_NONE=99
}CURSOR_TEMP;
extern CURSOR_TEMP cursor_temp;
#define CURSOR_TEMP_MAX 4
#define CURSOR_TEMP_DIGIT 3

typedef enum
{
	PULSE1=0,
	PULSE2=1,
	PULSE3=2,
	PULSE4=3,
	PULSE5=4,
	PULSE6=5,
	PULSE7=6,
	CURSOR_PULSE_NONE=99
}CURSOR_PULSE;
extern CURSOR_PULSE cursor_pulse;
#define CURSOR_PULSE_MAX 7
#define CURSOR_PULSE_DIGIT 7

typedef enum
{
	DUTY1=0,
	DUTY2=1,
	DUTY3=2,
	DUTY4=3,
	DUTY5=4,//直流输出
	CURSOR_DUTY_NONE=99
}CURSOR_DUTY;
extern CURSOR_DUTY cursor_duty;
#define CURSOR_DUTY_MAX 5
#define CURSOR_DUTY_DIGIT 4

void right_button();
void left_button();
void up_button();
void down_button();
void confirm_button();
//void fun_button();
void cancel_button();
void renew_menu();
void renew_menu_all();

#define VOLTAGE_SUM_MV_MAX 8192
extern _Bool start_temp_ctrl,direct_current_output,voltage_sum_ctrl;
extern char *txtname[];
extern int voltage_sum_mv,temperature_set;
extern float temperature_now;
extern float current;
extern float voltage_led;
extern uint32_t pulse_width_us;
extern int duty_cycle;
#endif