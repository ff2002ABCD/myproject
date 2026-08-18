#include "DS18B20_1.h"

#define DQ_GPIO_Port_1 GPIOA
#define DQ_GPIO_Port_2 GPIOA
#define DQ_GPIO_Port_3 GPIOA
#define DQ_GPIO_Port_4 GPIOA

#define DQ_Pin_1	GPIO_PIN_1
#define DQ_Pin_2	GPIO_PIN_2
#define DQ_Pin_3	GPIO_PIN_3
#define DQ_Pin_4	GPIO_PIN_4


#define DS18B20_DQ_OUT_HIGH_1 HAL_GPIO_WritePin(DQ_GPIO_Port_1, DQ_Pin_1, GPIO_PIN_SET)
#define DS18B20_DQ_OUT_HIGH_2 HAL_GPIO_WritePin(DQ_GPIO_Port_2, DQ_Pin_2, GPIO_PIN_SET)
#define DS18B20_DQ_OUT_HIGH_3 HAL_GPIO_WritePin(DQ_GPIO_Port_3, DQ_Pin_3, GPIO_PIN_SET)
#define DS18B20_DQ_OUT_HIGH_4 HAL_GPIO_WritePin(DQ_GPIO_Port_4, DQ_Pin_4, GPIO_PIN_SET)

#define DS18B20_DQ_OUT_LOW_1	HAL_GPIO_WritePin(DQ_GPIO_Port_1, DQ_Pin_1, GPIO_PIN_RESET)
#define DS18B20_DQ_OUT_LOW_2	HAL_GPIO_WritePin(DQ_GPIO_Port_2, DQ_Pin_2, GPIO_PIN_RESET)
#define DS18B20_DQ_OUT_LOW_3	HAL_GPIO_WritePin(DQ_GPIO_Port_3, DQ_Pin_3, GPIO_PIN_RESET)
#define DS18B20_DQ_OUT_LOW_4	HAL_GPIO_WritePin(DQ_GPIO_Port_4, DQ_Pin_4, GPIO_PIN_RESET)

#define DS18B20_DQ_IN_1       HAL_GPIO_ReadPin(DQ_GPIO_Port_1, DQ_Pin_1)
#define DS18B20_DQ_IN_2       HAL_GPIO_ReadPin(DQ_GPIO_Port_2, DQ_Pin_2)
#define DS18B20_DQ_IN_3       HAL_GPIO_ReadPin(DQ_GPIO_Port_3, DQ_Pin_3)
#define DS18B20_DQ_IN_4       HAL_GPIO_ReadPin(DQ_GPIO_Port_4, DQ_Pin_4)





void DS18B20_IO_IN_1(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_1;

	GPIO_InitStructure.Mode = GPIO_MODE_INPUT;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}


void DS18B20_IO_IN_2(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_2;

	GPIO_InitStructure.Mode = GPIO_MODE_INPUT;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}


void DS18B20_IO_IN_3(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_3;

	GPIO_InitStructure.Mode = GPIO_MODE_INPUT;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}


void DS18B20_IO_IN_4(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_4;

	GPIO_InitStructure.Mode = GPIO_MODE_INPUT;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}


void DS18B20_IO_OUT_1(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_1;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}


void DS18B20_IO_OUT_2(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_2;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}

void DS18B20_IO_OUT_3(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_3;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}

void DS18B20_IO_OUT_4(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_4;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);

}



void DS18B20_Rst_1(void){

	DS18B20_IO_OUT_1();

	DS18B20_DQ_OUT_LOW_1;

	delay_us(750);

	DS18B20_DQ_OUT_HIGH_1;

	delay_us(15);

}


void DS18B20_Rst_2(void){

	DS18B20_IO_OUT_2();

	DS18B20_DQ_OUT_LOW_2;

	delay_us(750);

	DS18B20_DQ_OUT_HIGH_2;

	delay_us(15);

}

void DS18B20_Rst_3(void){

	DS18B20_IO_OUT_3();

	DS18B20_DQ_OUT_LOW_3;

	delay_us(750);

	DS18B20_DQ_OUT_HIGH_3;

	delay_us(15);

}

void DS18B20_Rst_4(void){

	DS18B20_IO_OUT_4();

	DS18B20_DQ_OUT_LOW_4;

	delay_us(750);

	DS18B20_DQ_OUT_HIGH_4;

	delay_us(15);

}
uint8_t DS18B20_Check_1(void){

	uint8_t retry = 0;

	DS18B20_IO_IN_1();

	while(DS18B20_DQ_IN_1 && retry < 200){

		retry++;

		delay_us(1);

	}



	if(retry >= 200)

	return 1;

	else

	retry = 0;

	while(!DS18B20_DQ_IN_1 && retry < 240){

		retry++;

		delay_us(1);

	}



	if(retry >= 240)

	return 2;



	return 0;

}

uint8_t DS18B20_Check_2(void){

	uint8_t retry = 0;

	DS18B20_IO_IN_2();

	while(DS18B20_DQ_IN_2 && retry < 200){

		retry++;

		delay_us(1);

	}



	if(retry >= 200)

	return 1;

	else

	retry = 0;

	while(!DS18B20_DQ_IN_2 && retry < 240){

		retry++;

		delay_us(1);

	}



	if(retry >= 240)

	return 2;



	return 0;

}

uint8_t DS18B20_Check_3(void){

	uint8_t retry = 0;

	DS18B20_IO_IN_3();

	while(DS18B20_DQ_IN_3 && retry < 200){

		retry++;

		delay_us(1);

	}



	if(retry >= 200)

	return 1;

	else

	retry = 0;

	while(!DS18B20_DQ_IN_3 && retry < 240){

		retry++;

		delay_us(1);

	}



	if(retry >= 240)

	return 2;



	return 0;

}

uint8_t DS18B20_Check_4(void){

	uint8_t retry = 0;

	DS18B20_IO_IN_4();

	while(DS18B20_DQ_IN_4 && retry < 200){

		retry++;

		delay_us(1);

	}



	if(retry >= 200)

	return 1;

	else

	retry = 0;

	while(!DS18B20_DQ_IN_4 && retry < 240){

		retry++;

		delay_us(1);

	}



	if(retry >= 240)

	return 2;



	return 0;

}

void DS18B20_Write_Byte_1(uint8_t data){

	uint8_t j;

	uint8_t databit;

	DS18B20_IO_OUT_1();

	for(j=1;j<=8;j++){

		databit=data&0x01;

		data=data>>1;

		if(databit){

			DS18B20_DQ_OUT_LOW_1;

			delay_us(2);

			DS18B20_DQ_OUT_HIGH_1;

			delay_us(60);

		}
		else{

			DS18B20_DQ_OUT_LOW_1;

			delay_us(60);

			DS18B20_DQ_OUT_HIGH_1;

			delay_us(2);

		}

	}

}

void DS18B20_Write_Byte_2(uint8_t data){

	uint8_t j;

	uint8_t databit;

	DS18B20_IO_OUT_2();

	for(j=1;j<=8;j++){

		databit=data&0x01;

		data=data>>1;

		if(databit){

			DS18B20_DQ_OUT_LOW_2;

			delay_us(2);

			DS18B20_DQ_OUT_HIGH_2;

			delay_us(60);

		}
		else{

			DS18B20_DQ_OUT_LOW_2;

			delay_us(60);

			DS18B20_DQ_OUT_HIGH_2;

			delay_us(2);

		}

	}

}

void DS18B20_Write_Byte_3(uint8_t data){

	uint8_t j;

	uint8_t databit;

	DS18B20_IO_OUT_3();

	for(j=1;j<=8;j++){

		databit=data&0x01;

		data=data>>1;

		if(databit){

			DS18B20_DQ_OUT_LOW_3;

			delay_us(2);

			DS18B20_DQ_OUT_HIGH_3;

			delay_us(60);

		}
		else{

			DS18B20_DQ_OUT_LOW_3;

			delay_us(60);

			DS18B20_DQ_OUT_HIGH_3;

			delay_us(2);

		}

	}

}

void DS18B20_Write_Byte_4(uint8_t data){

	uint8_t j;

	uint8_t databit;

	DS18B20_IO_OUT_4();

	for(j=1;j<=8;j++){

		databit=data&0x01;

		data=data>>1;

		if(databit){

			DS18B20_DQ_OUT_LOW_4;

			delay_us(2);

			DS18B20_DQ_OUT_HIGH_4;

			delay_us(60);

		}
		else{

			DS18B20_DQ_OUT_LOW_4;

			delay_us(60);

			DS18B20_DQ_OUT_HIGH_4;

			delay_us(2);

		}

	}

}



uint8_t DS18B20_Read_Bit_1(void){

	uint8_t data;

	DS18B20_IO_OUT_1();

	DS18B20_DQ_OUT_LOW_1;

	delay_us(2);

	DS18B20_DQ_OUT_HIGH_1;

	DS18B20_IO_IN_1();

	delay_us(12);



	if(DS18B20_DQ_IN_1)

	data = 1;

	else

	data = 0;



	delay_us(50);

	return data;

}

uint8_t DS18B20_Read_Bit_2(void){

	uint8_t data;

	DS18B20_IO_OUT_2();

	DS18B20_DQ_OUT_LOW_2;

	delay_us(2);

	DS18B20_DQ_OUT_HIGH_2;

	DS18B20_IO_IN_2();

	delay_us(12);



	if(DS18B20_DQ_IN_2)

	data = 1;

	else

	data = 0;



	delay_us(50);

	return data;

}

uint8_t DS18B20_Read_Bit_3(void){

	uint8_t data;

	DS18B20_IO_OUT_3();

	DS18B20_DQ_OUT_LOW_3;

	delay_us(2);

	DS18B20_DQ_OUT_HIGH_3;

	DS18B20_IO_IN_3();

	delay_us(12);



	if(DS18B20_DQ_IN_3)

	data = 1;

	else

	data = 0;



	delay_us(50);

	return data;

}

uint8_t DS18B20_Read_Bit_4(void){

	uint8_t data;

	DS18B20_IO_OUT_4();

	DS18B20_DQ_OUT_LOW_4;

	delay_us(2);

	DS18B20_DQ_OUT_HIGH_4;

	DS18B20_IO_IN_4();

	delay_us(12);



	if(DS18B20_DQ_IN_4)

	data = 1;

	else

	data = 0;



	delay_us(50);

	return data;

}


uint8_t DS18B20_Read_Byte_1(void){

	uint8_t i,j,data;

	data = 0;

	for(i=1;i<=8;i++){

		j = DS18B20_Read_Bit_1();

		data = (j<<7)|(data>>1);


	}

	return data;

}

uint8_t DS18B20_Read_Byte_2(void){

	uint8_t i,j,data;

	data = 0;

	for(i=1;i<=8;i++){

		j = DS18B20_Read_Bit_2();

		data = (j<<7)|(data>>1);


	}

	return data;

}

uint8_t DS18B20_Read_Byte_3(void){

	uint8_t i,j,data;

	data = 0;

	for(i=1;i<=8;i++){

		j = DS18B20_Read_Bit_3();

		data = (j<<7)|(data>>1);


	}

	return data;

}

uint8_t DS18B20_Read_Byte_4(void){

	uint8_t i,j,data;

	data = 0;

	for(i=1;i<=8;i++){

		j = DS18B20_Read_Bit_4();

		data = (j<<7)|(data>>1);


	}

	return data;

}

void DS18B20_Start_1(void){

	DS18B20_Rst_1();

	DS18B20_Check_1();

	DS18B20_Write_Byte_1(0xcc);

	DS18B20_Write_Byte_1(0x44);

}

void DS18B20_Start_2(void){

	DS18B20_Rst_2();

	DS18B20_Check_2();

	DS18B20_Write_Byte_2(0xcc);

	DS18B20_Write_Byte_2(0x44);

}

void DS18B20_Start_3(void){

	DS18B20_Rst_3();

	DS18B20_Check_3();

	DS18B20_Write_Byte_3(0xcc);

	DS18B20_Write_Byte_3(0x44);

}

void DS18B20_Start_4(void){

	DS18B20_Rst_4();

	DS18B20_Check_4();

	DS18B20_Write_Byte_4(0xcc);

	DS18B20_Write_Byte_4(0x44);

}


uint8_t DS18B20_Init_1(void){


	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_1;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Pull = GPIO_PULLUP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);



	DS18B20_Rst_1();

	return DS18B20_Check_1();

}

uint8_t DS18B20_Init_2(void){


	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_2;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Pull = GPIO_PULLUP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);



	DS18B20_Rst_2();

	return DS18B20_Check_2();

}

uint8_t DS18B20_Init_3(void){


	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_3;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Pull = GPIO_PULLUP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);



	DS18B20_Rst_3();

	return DS18B20_Check_3();

}

uint8_t DS18B20_Init_4(void){


	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = GPIO_PIN_4;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Pull = GPIO_PULLUP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(GPIOA,&GPIO_InitStructure);



	DS18B20_Rst_4();

	return DS18B20_Check_4();

}

short DS18B20_Get_Temperature_1(void){


	uint8_t TL,TH;

	short temperature;

	DS18B20_Start_1();

	DS18B20_Rst_1();

	DS18B20_Check_1();

	DS18B20_Write_Byte_1(0xcc);

	DS18B20_Write_Byte_1(0xbe);
	TL = DS18B20_Read_Byte_1();
	TH = DS18B20_Read_Byte_1();

	if(TH>0x70){

		TH = ~TH;

		TL = ~TL;


	}else


	temperature = TH;

	temperature <<= 8;

	temperature += TL;

	temperature = (float)temperature*0.625;

	if(temperature)

	return temperature;

	else

	return -temperature;

}

short DS18B20_Get_Temperature_2(void){


	uint8_t TL,TH;

	short temperature;

	DS18B20_Start_2();

	DS18B20_Rst_2();

	DS18B20_Check_2();

	DS18B20_Write_Byte_2(0xcc);

	DS18B20_Write_Byte_2(0xbe);
	TL = DS18B20_Read_Byte_2();
	TH = DS18B20_Read_Byte_2();

	if(TH>0x70){

		TH = ~TH;

		TL = ~TL;


	}else


	temperature = TH;

	temperature <<= 8;

	temperature += TL;

	temperature = (float)temperature*0.625;

	if(temperature)

	return temperature;

	else

	return -temperature;

}

short DS18B20_Get_Temperature_3(void){


	uint8_t TL,TH;

	short temperature;

	DS18B20_Start_3();

	DS18B20_Rst_3();

	DS18B20_Check_3();

	DS18B20_Write_Byte_3(0xcc);

	DS18B20_Write_Byte_3(0xbe);
	TL = DS18B20_Read_Byte_3();
	TH = DS18B20_Read_Byte_3();

	if(TH>0x70){

		TH = ~TH;

		TL = ~TL;


	}else


	temperature = TH;

	temperature <<= 8;

	temperature += TL;

	temperature = (float)temperature*0.625;

	if(temperature)

	return temperature;

	else

	return -temperature;

}

short DS18B20_Get_Temperature_4(void){


	uint8_t TL,TH;

	short temperature;

	DS18B20_Start_4();

	DS18B20_Rst_4();

	DS18B20_Check_4();

	DS18B20_Write_Byte_4(0xcc);

	DS18B20_Write_Byte_4(0xbe);
	TL = DS18B20_Read_Byte_4();
	TH = DS18B20_Read_Byte_4();

	if(TH>0x70){

		TH = ~TH;

		TL = ~TL;


	}else


	temperature = TH;

	temperature <<= 8;

	temperature += TL;

	temperature = (float)temperature*0.625;

	if(temperature)

	return temperature;

	else

	return -temperature;

}
