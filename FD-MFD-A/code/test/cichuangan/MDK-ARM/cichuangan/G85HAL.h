#ifndef __G85HAL_H
#define __G85HAL_H		

#include "stm32f1xx_hal.h"
#include "i2c.h"

#define	ITG3205_Addr    0x68	  
#define	HMC5883L_Addr   0x3C	

#define HMC5883l_CONFIG_A     0x00
#define HMC5883l_CONFIG_B     0x01
#define HMC5883l_MODECONFIG   0x02

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
void caliboration(float *Xoffset,float *Yoffset,float *Zoffset,float *Kx,float *Ky,float *Kz);
#endif
