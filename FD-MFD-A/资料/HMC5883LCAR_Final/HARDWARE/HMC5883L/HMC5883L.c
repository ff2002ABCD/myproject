#include "HMC5883L.h"
#include "myiic.h"
#include "delay.h"
#include "oled.h"
#include "math.h"
#include "key.h"
#include "led.h"

void hmc_write_reg(u8 reg,u8 data)
{
	IIC_Start();
	IIC_Send_Byte(WRITE_ADDRESS);
	IIC_Wait_Ack();
	IIC_Send_Byte(reg);
	IIC_Wait_Ack();
	IIC_Send_Byte(data);
	IIC_Wait_Ack();
	IIC_Stop();
	//delay_ms(5);
}

u8 hmc_read_reg(u8 reg)
{
	unsigned char data;
	IIC_Start();
	IIC_Send_Byte(WRITE_ADDRESS);
	IIC_Wait_Ack();
	IIC_Send_Byte(reg);
	IIC_Wait_Ack();
	IIC_Stop();
	IIC_Start();
	IIC_Send_Byte(READ_ADDRESS);
	IIC_Wait_Ack();
	data = IIC_Read_Byte();
	IIC_NAck();
	IIC_Stop();
	return data;
}

extern double x,y,z,h;
void hmc_read_XYZ(void)
{
	short int data[3];

	u16 temp;
	temp=hmc_read_reg(DATAX_M);
	data[0]=(temp<<8)+hmc_read_reg(DATAX_L);
	temp=hmc_read_reg(DATAY_M);
	data[1]=(temp<<8)+hmc_read_reg(DATAY_L);
	temp=hmc_read_reg(DATAZ_M);
	data[2]=(temp<<8)+hmc_read_reg(DATAZ_L);
	if(data[0]>=32768)  
  {  
    data[0] = -(0xFFFF - data[0]+ 1);  
  }  
    
  if(data[1]>=32768)  
  {  
    data[1] = -(0xFFFF - data[1] + 1);  
  }  
  if(data[2]>=32768)  
  {  
    data[2] = -(0xFFFF - data[2] + 1);  
  }  
	x = data[0];
	y = data[1];
	z = data[2];
	h = sqrt(x*x+y*y+z*z);
}




void hmc_init(void)
{
	hmc_write_reg(CONFIGA,0x14);
	hmc_write_reg(CONFIGB,0x80);
	hmc_write_reg(MODE,0x00);
	delay_ms(10);
}




