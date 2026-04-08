#ifndef __G85HAL_H
#define __G85HAL_H		

#include "main.h"
//#include "stm32f1xx_hal.h"
#include "i2c.h"

#define	ITG3205_Addr    0x68	  
#define	HMC5883L_Addr   0x3C	

#define HMC5883l_CONFIG_A     0x00
#define HMC5883l_CONFIG_B     0x01
#define HMC5883l_MODECONFIG   0x02
#define HMC5883_REG_STATUS   0x09

struct HMC5883L_Data {
	unsigned char vtemp[12];
	 int  x_h;		
	 int  y_h;	
	 int  z_h;		
	float angle;
};

//***************************************
int g85_makeuint16(int msb, int lsb) ;
void  Init_HMC5883L_HAL(I2C_HandleTypeDef *hi2c1);
void  Init_HMC5883L_HAL_test(I2C_HandleTypeDef *hi2c1);
void hmc5883l_rawread(float *GaX, float *GaY,float *GaZ);

void calibo_x0y0();
void calibo_z0();
void calibo_x1y1();
void calibo_z1();
#endif
