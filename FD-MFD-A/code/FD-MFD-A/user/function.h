#ifndef __FUNCTION_H
#define __FUNCTION_H
#include "main.h"
#define MAX_GROUP 16
#define MAX_NUMBER 100
#define AVER_NUM 20//磁场大小取平均数
typedef struct
{
		float Pos,Current,Strength,GaX,GaY,GaZ;
}TABLE;

void gener_cordinate();
void start_measure();
void record_data();
void data_sheet();
void Current_control();
void system_init();
void get_averdata();
void set_zero();
void measure_ground();
extern int start_position_int,end_position_int,position_step_int;
extern uint8_t group_now,number_now,sheet_now,table_length[MAX_NUMBER],sheet_length;
extern float GaX,GaY,GaZ,rawGaX,rawGaY,rawGaZ,GaXmax,GaXmin,GaYmax,GaYmin,GaZmax,GaZmin,strength,Current,position,Voltage_dac,k;
extern float GaX_array[AVER_NUM],GaY_array[AVER_NUM],GaZ_array[AVER_NUM],strength_array[AVER_NUM];
extern float pos_measure_start;
extern double test_position[MAX_NUMBER];
extern double start_position,end_position,position_step,position_num;
extern TABLE table[MAX_GROUP][MAX_NUMBER];
#endif
