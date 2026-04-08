#include "G85hal.h"
#include  <math.h> 

int  g85_makeuint16(int msb, int lsb) 
{
    return ((msb & 0xFF) << 8) | (lsb & 0xFF);
}

//进入校准模式
void  Init_HMC5883L_HAL_test(I2C_HandleTypeDef *hi2c1)
{
		unsigned char cdata[3]={0x71,0x40,0X01};
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_A, I2C_MEMADD_SIZE_8BIT,cdata, 1, 1000);          
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_B, I2C_MEMADD_SIZE_8BIT, cdata+1, 1, 1000);            
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_MODECONFIG, I2C_MEMADD_SIZE_8BIT, cdata+2, 1, 1000);     
}

//正常测量模式
void  Init_HMC5883L_HAL(I2C_HandleTypeDef *hi2c1)
{
		unsigned char cdata[3]={0x70,0xE0,0X00};
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_A, I2C_MEMADD_SIZE_8BIT,cdata, 1, 1000);          
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_B, I2C_MEMADD_SIZE_8BIT, cdata+1, 1, 1000);            
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_MODECONFIG, I2C_MEMADD_SIZE_8BIT, cdata+2, 1, 1000);     
}

void hmc5883l_rawread(float *GaX, float *GaY,float *GaZ)
{
		
		uint8_t data[6];
	  HAL_I2C_Mem_Read(&hi2c1,HMC5883L_Addr, 0x03,1,data,6 , 1000); //连续读取
		int16_t dxra,dyra,dzra;
		dxra = (data[0] << 8) | data[1]; 
		*GaX = (float)dxra /230;	
		dyra = (data[4] << 8) | data[5]; 
		*GaY = (float)dyra /230 ;	
	  dzra = (data[2] << 8) | data[3];	
		*GaZ = (float)dzra /230 ;		

}

void caliboration(float *Xoffset,float *Yoffset,float *Zoffset,float *Kx,float *Ky,float *Kz)
{
	uint8_t i=0 ;
	float GaX,GaY,GaZ,GaXmax=0,GaXmin=0,GaYmax=0,GaYmin=0,GaZmax=0,GaZmin=0;
	while(i != 100)
	{
		hmc5883l_rawread(&GaX, &GaY, &GaZ);
		GaXmax = GaXmax < GaX? GaX:GaXmax;
		GaXmin = GaXmin > GaX? GaX:GaXmin;	
		GaYmax = GaYmax < GaY? GaY:GaYmax;
		GaYmin = GaYmin > GaY? GaY:GaYmin;
		GaZmax = GaZmax < GaZ? GaZ:GaZmax;
		GaZmin = GaZmin > GaZ? GaZ:GaZmin;	
		HAL_Delay(200);		
		i++;
	}	
	*Xoffset = (GaXmax+GaXmin)/2;
	*Yoffset = (GaYmax+GaYmin)/2;
	*Zoffset = (GaZmax+GaZmin)/2;
	*Kx = 2/(GaXmax-GaXmin);
	*Ky = 2/(GaYmax-GaYmin);
	*Kz = 2/(GaZmax-GaZmin);
}
