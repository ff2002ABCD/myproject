#ifndef __MENU_H
#define __MENU_H
typedef enum
{
	MAIN=0,
	MEA_JOURNEY,
	MEA_ANGLE,
	SET_STEP,
	MEA_TIME,
	QUERY_JOURNEY,
	QUERY_ANGLE,
	QUERY_TIME,
	OUTPUTING,
	OUTPUT_OK
}PAGE;
extern PAGE page;

typedef enum
{
	MAIN_MEA_JOURNEY=1,
	MAIN_MEA_ANGLE=2,
	MAIN_MEA_TIME=3,
	MAIN_QUERY_JOURNEY=4,
	MAIN_QUERY_ANGLE=5,
	MAIN_QUERY_TIME=6
}CURSOR_MAIN;
extern CURSOR_MAIN cursor_main;

typedef enum
{
	MEA_JOURNEY_NONE=0,
	MEA_JOURNEY_SET_ZERO=1,
	MEA_JOURNEY_START=3,
	MEA_JOURNEY_EXIT=4,
	MEA_JOURNEY_DATA_CLEAR=2
}CURSOR_MEA_JOURNEY;
extern CURSOR_MEA_JOURNEY cursor_mea_journey;

typedef enum
{
	MEA_ANGLE_NONE=0,
	MEA_ANGLE_SET_ZERO=1,
	MEA_ANGLE_START=3,
	MEA_ANGLE_EXIT=4,
	MEA_ANGLE_DATA_CLEAR=2
}CURSOR_MEA_ANGLE;
extern CURSOR_MEA_ANGLE cursor_mea_angle;


typedef enum
{
	MEA_TIME_NONE=0,
	MEA_TIME_SET_ZERO=1,
	MEA_TIME_START=3,
	MEA_TIME_EXIT=4,
	MEA_TIME_DATA_CLEAR=2
}CURSOR_MEA_TIME;
extern CURSOR_MEA_TIME cursor_mea_time;

typedef enum
{
	QUERY_JOURNEY_NONE=0,
	QUERY_JOURNEY_DATA_OUPUT=1,
	QUERY_JOURNEY_EXIT=2
}CURSOR_QUERY_JOURNEY;
extern CURSOR_QUERY_JOURNEY cursor_query_journey;

typedef enum
{
	QUERY_ANGLE_NONE=0,
	QUERY_ANGLE_DATA_OUPUT=1,
	QUERY_ANGLE_EXIT=2
}CURSOR_QUERY_ANGLE;
extern CURSOR_QUERY_ANGLE cursor_query_angle;

typedef enum
{
	QUERY_TIME_NONE=0,
	QUERY_TIME_DATA_OUPUT=1,
	QUERY_TIME_EXIT=2
}CURSOR_QUERY_TIME;
extern CURSOR_QUERY_TIME cursor_query_time;

typedef enum
{
	_10s=100,
	_1s=10,
	_01s=1,
}STEP;
extern STEP step;

typedef enum
{
	MEA_STOP=2,
	MEA_START=1,
	MEA_PAUSE=0,
}MEA_STATE;
extern MEA_STATE mea_state;

typedef enum
{
	OFFSET_MOVE_1=1,
	OFFSET_MOVE_10=10,
	OFFSET_MOVE_100=100
	
}OFFSET_MOVE;
extern OFFSET_MOVE x_offset_move;
extern _Bool button_called;

void up_button();
void down_button();
void left_button();
void right_button();
void confirm_button();
void cancel_button();
void fun_button();
void renew_menu();

#endif

