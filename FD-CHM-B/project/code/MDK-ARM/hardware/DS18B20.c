#include "DS18B20.h"


#define DQ_H     HAL_GPIO_WritePin(GPIOB,GPIO_PIN_1,GPIO_PIN_SET)       			//PB1拉高
#define DQ_L     HAL_GPIO_WritePin(GPIOB,GPIO_PIN_1,GPIO_PIN_RESET)				//PB1拉低
#define DQ_Read  HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_1)   //PB1读取

uint8_t flag=0;

void DS18B20_Init(void) 																		//PB1初始化
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};
	__HAL_RCC_GPIOB_CLK_ENABLE();
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, GPIO_PIN_SET);
  GPIO_InitStruct.Pin = GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}

void DS18B20_Output(void)      //输出模式            
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};
	__HAL_RCC_GPIOB_CLK_ENABLE();
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, GPIO_PIN_SET);
	GPIO_InitStruct.Pin = GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}

void DS18B20_Input(void)      //输入模式
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};
	__HAL_RCC_GPIOB_CLK_ENABLE();
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, GPIO_PIN_SET);
  GPIO_InitStruct.Pin = GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}

uint8_t DS18B20_Reset(void)      //复位
{
	uint8_t flag;
	DS18B20_Output();
	DQ_H;
	HAL_Delay(5);
	
	DQ_L;
	HAL_Delay(480);
	DQ_H;
	HAL_Delay(60);
	DS18B20_Input();
	flag=DQ_Read;
	HAL_Delay(480);
	DS18B20_Output();
	DQ_H;
	return flag;
}

void DS18B20_WriteData(uint8_t data)     // 写数据
{
	for(uint8_t i=0;i<8;i++)
	{
		DS18B20_Output();  //输出状态
		DQ_L;
		HAL_Delay(2);
		if(data&0x01)     //低位开始，看上一节视频有详细讲解
		{
			DQ_H;
		}
		else
		{
			DQ_L;
		}
		HAL_Delay(60);
		DQ_H;
		data = data>>1;
	}
	
}

uint8_t DS18B20_ReadData(void)      //读数据
{
	uint8_t data =0;
	
	for(uint8_t i=0;i<8;i++)
	{
		data=data>>1;
		DS18B20_Output();   //输出状态
		DQ_L;
		HAL_Delay(2);
		DQ_H;
		HAL_Delay(2);
		DS18B20_Input();   //输入状态
		if(DQ_Read)
			data|=0x80;     //放入高位，再移位到低位
		HAL_Delay(60);
	}
	return data;
}

uint16_t DS18B20_ReadTemp(void)   //读取温度
{
	uint8_t DL,DH;
	uint16_t data;	
	uint16_t Temperature=0;
	flag=0;
	DS18B20_Reset();              //复位
	DS18B20_WriteData(0XCC);      //跳过ROM检测
	DS18B20_WriteData(0X44);      //启动温度转换
	HAL_Delay(750);                //延时，等待转换完成
	DS18B20_Reset();              //复位
	DS18B20_WriteData(0XCC);      //跳过ROM检测
	DS18B20_WriteData(0XBE);      //读取暂存器指令
	DL=DS18B20_ReadData();        //读温度低位
	DH=DS18B20_ReadData();        //读温度高位
	data=DH;
	data=data<<8;
	data|=DL;
	if((data&0XF800)==0XF800)  
	{
		data=~data+0X01;
		flag=1;
	}
		
	Temperature=data * 0.0625*10;
	return Temperature;
}

