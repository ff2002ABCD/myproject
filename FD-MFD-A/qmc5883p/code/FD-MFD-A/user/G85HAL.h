#ifndef __G85HAL_H
#define __G85HAL_H		

#include "main.h"
//#include "stm32f1xx_hal.h"
#include "i2c.h"
 
#define	QMC5883P_Addr   0x58	


struct QMC5883P_Data {
	unsigned char vtemp[12];
	 int  x_h;		
	 int  y_h;	
	 int  z_h;		
	float angle;
};

//***************************************
int g85_makeuint16(int msb, int lsb) ;
void  Init_QMC5883P_HAL(I2C_HandleTypeDef *hi2c1);
void  Init_QMC5883P_HAL_test(I2C_HandleTypeDef *hi2c1);
void QMC5883P_rawread(float *GaX, float *GaY,float *GaZ);

void calibo_x0y0();
void calibo_z0();
void calibo_x1y1();
void calibo_z1();
#endif
