#ifndef __MENU_H
#define __MENU_H
#include "main.h"

#define HIGHLIGHT 61277
#define NORMAL 50779
#define MAX_CURRENT 150

typedef enum
{
	MAIN,
	XY_CALIBO,
	Z_CALIBO,
	PLACE,
	XY_CALIBO_1,
	Z_CALIBO_1,
	CALIBO_SUCCESS,
	MEASURE_GROUND,
	AUTO_SETZERO,
	MEASURE_COIL,
	SELECT_INPUTMODE,
	GENERATE_COORDINATES,
	MEASUER_START,
	MEASUER_START_1,
	DATA_OUTPUT,
	DATA_SHEET,
	OUTPUTING,
	OUTPUT_COMPLETE,
	PLACE_UP,
	PLACE_RIGHT,
	PLACE_UP_1,
	PLACE_RIGHT_1
}	PAGE;

typedef enum
{
	CALIBO,
	MEA_GND,
	MEA_COIL,
	DATA,
	CAL
}CURSOR_MAIN;

typedef enum
{
	DATA_RECORD,
	SWITCH_MODE
}CURSOR_MEASURE_COIL;

typedef enum
{
	A1,
	A2,
	A3,
	A4
}CURSOR_MEASURE_COIL_CURRENT;

typedef enum
{
	MANUAL,
	AUTO
}CURSOR_SELECT_INPUTMODE;

typedef enum
{
	START1,
	START2,
	START3,
	START4,
	END1,
	END2,
	END3,
	END4,
	STEP1,
	STEP2,
	STEP3,
	STEP4
}CURSOR_GENERATE_COORDINATES;

typedef enum
{
	P1,
	P2,
	P3,
	P4
}CURSOR_MEASUER_START;

typedef enum
{
	X0Y0,
	Z0,
	X1Y1,
	Z1,
	NONE
}CALIBO_STATE;
//***************************************

extern unsigned int group_num,sheet_num,cursor_group_num,cursor_sheet_num;
extern _Bool input_mode;//0手动 1自动
extern PAGE page;
extern CURSOR_MAIN cursor_main;
extern CURSOR_MEASURE_COIL cursor_measure_coil;
extern CURSOR_MEASURE_COIL_CURRENT cursor_measure_coil_current;
extern CURSOR_SELECT_INPUTMODE cursor_select_inputmode;
extern CURSOR_GENERATE_COORDINATES cursor_generate_coordinates;	
extern CURSOR_MEASUER_START cursor_measuer_start;
extern CALIBO_STATE calibo_state;
extern _Bool input_judge;//0错误 1正确
extern _Bool output_flag;
extern uint8_t s1,s2,s3,s4,e1,e2,e3,e4,u1,u2,u3,u4,p1,p2,p3,p4,beishu;
extern float x0,y0,z0,x1,y1,z1;
void up_button();
void down_button();
void confirm_button();
void cancel_button();
void func_button();
void clockwise();
void counter_clockwise();

#endif
