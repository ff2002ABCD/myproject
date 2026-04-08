#include "G85hal.h"
#include "function.h"
#include "math.h"
#include "key.h"

#define k_standard_mag 0.944
uint8_t status;

int  g85_makeuint16(int msb, int lsb) 
{
    return ((msb & 0xFF) << 8) | (lsb & 0xFF);
}

//进入校准模式
void  Init_HMC5883L_HAL_test(I2C_HandleTypeDef *hi2c1)
{
		if(HAL_I2C_IsDeviceReady(hi2c1, HMC5883L_Addr, 3, 100)!=HAL_OK) return;
 		unsigned char cdata[3]={0x71,0x40,0X01};
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_A, I2C_MEMADD_SIZE_8BIT,cdata, 1, 100);          
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_B, I2C_MEMADD_SIZE_8BIT, cdata+1, 1, 100);            
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_MODECONFIG, I2C_MEMADD_SIZE_8BIT, cdata+2, 1, 100);     
}

//正常测量模式
void  Init_HMC5883L_HAL(I2C_HandleTypeDef *hi2c1)
{
	
		if(HAL_I2C_IsDeviceReady(hi2c1, HMC5883L_Addr, 3, 100)!=HAL_OK) return;
		if(init_flag==0) return;
		else if(init_flag==1)init_flag=0;
		unsigned char cdata[3]={0x70,0xE0,0X00};
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_A, I2C_MEMADD_SIZE_8BIT,cdata, 1, 100);          
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_CONFIG_B, I2C_MEMADD_SIZE_8BIT, cdata+1, 1, 100);            
		HAL_I2C_Mem_Write(hi2c1,HMC5883L_Addr,HMC5883l_MODECONFIG, I2C_MEMADD_SIZE_8BIT, cdata+2, 1, 100);     
}



void hmc5883l_rawread(float *GaX, float *GaY,float *GaZ)
{
	
		if(HAL_I2C_IsDeviceReady(&hi2c1, HMC5883L_Addr, 3, 100)!=HAL_OK) return;
//	if(HAL_I2C_Mem_Read(&hi2c1, HMC5883L_Addr, 0x09,I2C_MEMADD_SIZE_8BIT, &status, 1, 100) != HAL_OK) return;
//	if(!(status & 0x01)) return;
//	uint8_t status;
//do {
//    HAL_I2C_Mem_Read(&hi2c1, HMC5883L_Addr, HMC5883_REG_STATUS, I2C_MEMADD_SIZE_8BIT, &status, 1, 100);
//} while(!(status & 0x01));
//	if(status & 0x02) return;
		uint8_t data[6];
		if(HAL_I2C_Mem_Read(&hi2c1,HMC5883L_Addr, 0x03,1,data,6 , 100)!=HAL_OK)return ; //连续读取
		int16_t dxra,dyra,dzra;
		dxra = (data[0] << 8) | data[1];
		if(dxra>3000||dxra<-3000) return;
		*GaX = (float)dxra /230.0f;	
		dyra = (data[4] << 8) | data[5]; 
		if(dyra>3000||dyra<-3000) return;
		*GaY = (float)dyra /230.0f ;	
	  dzra = (data[2] << 8) | data[3];	
		if(dzra>3000||dzra<-3000) return;
		*GaZ = (float)dzra /230.0f ;		

}

void calibo_x0y0()
{
		static float GaX=0,GaY=0,GaZ=0;
		
		hmc5883l_rawread(&GaX, &GaY, &GaZ);
		GaXmax = GaXmax < GaX? GaX:GaXmax;
		GaXmin = GaXmin > GaX? GaX:GaXmin;
		GaYmax = GaYmax < GaY? GaY:GaYmax;
		GaYmin = GaYmin > GaY? GaY:GaYmin;
		
	printf("xmax.txt=\"%.1f\"\xff\xff\xff",GaXmax*100);
	printf("xmin.txt=\"%.1f\"\xff\xff\xff",GaXmin*100);
	printf("ymax.txt=\"%.1f\"\xff\xff\xff",GaYmax*100);
	printf("ymin.txt=\"%.1f\"\xff\xff\xff",GaYmin*100);
	printf("xnow.txt=\"%.1f\"\xff\xff\xff",GaX*100);
	printf("ynow.txt=\"%.1f\"\xff\xff\xff",GaY*100);
	x0 = (GaXmax+GaXmin)/2;
	y0 = (GaYmax+GaYmin)/2;
//	printf("t6.txt=\"X0:%.1f\"\xff\xff\xff",x0*100);
//	printf("t7.txt=\"Y0:%.1f\"\xff\xff\xff",y0*100);
}

void calibo_z0()
{

	static float GaX=0,GaY=0,GaZ=0;

		hmc5883l_rawread(&GaX, &GaY, &GaZ);
		GaZmax = GaZmax < GaZ? GaZ:GaZmax;
		GaZmin = GaZmin > GaZ? GaZ:GaZmin;
	printf("zmax.txt=\"%.1f\"\xff\xff\xff",GaZmax*100);
	printf("zmin.txt=\"%.1f\"\xff\xff\xff",GaZmin*100);
	printf("znow.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
	z0 = (GaZmax+GaZmin)/2;
//	printf("t3.txt=\"Z0:%.1f\"\xff\xff\xff",z0*100);
}

void calibo_x1y1()
{

	static float GaX=0,GaY=0,GaZ=0;

		hmc5883l_rawread(&GaX, &GaY, &GaZ);
		GaXmax = GaXmax < GaX? GaX:GaXmax;
		GaXmin = GaXmin > GaX? GaX:GaXmin;
		GaYmax = GaYmax < GaY? GaY:GaYmax;
		GaYmin = GaYmin > GaY? GaY:GaYmin;

	printf("xmax.txt=\"%.1f\"\xff\xff\xff",GaXmax*100);
	printf("xmin.txt=\"%.1f\"\xff\xff\xff",GaXmin*100);
	printf("ymax.txt=\"%.1f\"\xff\xff\xff",GaYmax*100);
	printf("ymin.txt=\"%.1f\"\xff\xff\xff",GaYmin*100);
	printf("xnow.txt=\"%.1f\"\xff\xff\xff",GaX*100);
	printf("ynow.txt=\"%.1f\"\xff\xff\xff",GaY*100);
	x1 = 4.5*k_standard_mag/(GaXmax-GaXmin)*2;
	y1 = 4.5*k_standard_mag/(GaYmax-GaYmin)*2;
//	printf("t6.txt=\"X1:%.1f\"\xff\xff\xff",x1);
//	printf("t7.txt=\"Y1:%.1f\"\xff\xff\xff",y1);
	
}

void calibo_z1()
{

	static float GaX=0,GaY=0,GaZ=0;
	
	hmc5883l_rawread(&GaX, &GaY, &GaZ);
	GaZmax = GaZmax < GaZ? GaZ:GaZmax;
	GaZmin = GaZmin > GaZ? GaZ:GaZmin;
	
	printf("zmax.txt=\"%.1f\"\xff\xff\xff",GaZmax*100);
	printf("zmin.txt=\"%.1f\"\xff\xff\xff",GaZmin*100);
	printf("znow.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
	z1= 4.5*k_standard_mag/(GaZmax-GaZmin)*2;
//	printf("t3.txt=\"Z1:%.1f\"\xff\xff\xff",z1);
}

