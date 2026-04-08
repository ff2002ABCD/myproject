#ifndef __FUNCTION_H
#define __FUNCTION_H
#include "main.h"
#define MAX_NUM_JOURNEY 40000
#define MAX_NUM_ANGLE 10000
#define MAX_NUM_TIME 30000
#define VOLTAGE_INPUT_RANGE 6
#define VOLTAGE_CENTER 2
#define htim_journey_process htim2
#define htim_angle_process htim7
#define htim_time_process htim6
#define TIM_TIME_PROCESS TIM6
#define htim_journey_encoder htim1
#define TIM_JOURNEY_ENCODER TIM1
#define htim_angle_encoder htim4
#define TIM_ANGLE_ENCODER TIM4
#define hadc_lightstrength hadc3
#define htim_key htim5

extern _Bool renew_screen_flag;
//动镜行程
#define xgrid_multiple_journey_index_max 6
#define ygrid_multiple_journey_index_max 6
extern int32_t count[MAX_NUM_JOURNEY];
extern int16_t voltage[MAX_NUM_JOURNEY];
extern uint32_t index_send,index_save;
extern int32_t round_now;
extern char *xgrid_txt_journey[];
extern char *ygrid_txt_journey[];
extern uint16_t xgrid_multiple_journey[];
extern uint8_t xgrid_multiple_journey_index;
extern uint16_t ygrid_multiple_journey[];
extern uint8_t ygrid_multiple_journey_index;
extern int32_t x_offset_journey;
extern _Bool measure_journey_state;
void measure_journey_start();
void journey_data_clear();
void measure_journey_pause();
void measure_journey_continue();

//角度
#define xgrid_multiple_angle_index_max 8
#define ygrid_multiple_angle_index_max 6
extern int32_t angle[MAX_NUM_ANGLE];
extern int16_t voltage_angle[MAX_NUM_ANGLE];
extern uint32_t index_send_angle,index_save_angle;
extern int32_t round_now_angle;
extern char *xgrid_txt_angle[];
extern char *ygrid_txt_angle[];
extern uint16_t xgrid_multiple_angle[];
extern uint8_t xgrid_multiple_angle_index;
extern uint16_t ygrid_multiple_angle[];
extern uint8_t ygrid_multiple_angle_index;
extern int32_t x_offset_angle;
extern _Bool measure_angle_state;
void measure_angle_start();
void angle_data_clear();
void measure_angle_pause();
void measure_angle_continue();

//时间
#define query_grid 50 //黄线到右侧距离
#define ygrid_multiple_time_index_max 6
#define xgrid_multiple_time_index_max 7
extern uint16_t sample_interval;
extern int32_t time[MAX_NUM_TIME];
extern int16_t voltage_time[MAX_NUM_TIME];
extern uint32_t index_send_time,index_save_time;
extern char *xgrid_txt_time[];
extern char *ygrid_txt_time[];
extern uint16_t xgrid_multiple_time[];
extern uint8_t xgrid_multiple_time_index;
extern uint16_t ygrid_multiple_time[];
extern uint8_t ygrid_multiple_time_index;
extern int32_t x_offset_time;
extern _Bool measure_time_state;
void measure_time_start();
void time_data_clear();
void measure_time_pause();
void measure_time_continue();


void save_data();
void save_angle();
void save_time();
void Send_Coordinate_I32_I16(int32_t x, int16_t y);
void Send_Coordinates_I32_I16(int32_t *x_values, int16_t *y_values, uint16_t count);
//void CH376_SetBaudRate(uint32_t new_baudrate);
#endif