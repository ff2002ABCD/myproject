#include "18b20_1.h"
#include "delay.h"

#define DQ2_GPIO_Port GPIOC

#define DQ2_Pin	GPIO_PIN_4

#define DS18B20_DQ2_OUT_HIGH_1 HAL_GPIO_WritePin(DQ2_GPIO_Port, DQ2_Pin, GPIO_PIN_SET)

#define DS18B20_DQ2_OUT_LOW_1	HAL_GPIO_WritePin(DQ2_GPIO_Port, DQ2_Pin, GPIO_PIN_RESET)

#define DS18B20_DQ2_IN_1       HAL_GPIO_ReadPin(DQ2_GPIO_Port, DQ2_Pin)

//void delay_us(uint32_t time)

//{

//	time *= 10;

//	while(time)

//	time--;

//}

void DS18B20_IO_IN_1(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = DQ2_Pin;

	GPIO_InitStructure.Mode = GPIO_MODE_INPUT;

	HAL_GPIO_Init(DQ2_GPIO_Port,&GPIO_InitStructure);

}




void DS18B20_IO_OUT_1(void){

	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = DQ2_Pin;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(DQ2_GPIO_Port,&GPIO_InitStructure);

}

void DS18B20_Rst_1(void){

	DS18B20_IO_OUT_1();

	DS18B20_DQ2_OUT_LOW_1;

	delay_us(650);

	DS18B20_DQ2_OUT_HIGH_1;

	delay_us(15);

}

uint8_t DS18B20_Check_1(void){

	uint8_t retry = 0;

	DS18B20_IO_IN_1();

	while(DS18B20_DQ2_IN_1 && retry < 200){

		retry++;

		delay_us(1);

	}



	if(retry >= 200)

	return 1;

	else

	retry = 0;

	while(!DS18B20_DQ2_IN_1 && retry < 240){

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

			DS18B20_DQ2_OUT_LOW_1;

			delay_us(2);

			DS18B20_DQ2_OUT_HIGH_1;

			delay_us(60);

		}
		else{

			DS18B20_DQ2_OUT_LOW_1;

			delay_us(60);

			DS18B20_DQ2_OUT_HIGH_1;

			delay_us(2);

		}

	}

}



uint8_t DS18B20_Read_Bit_1(void){

	uint8_t data;

	DS18B20_IO_OUT_1();

	DS18B20_DQ2_OUT_LOW_1;

	delay_us(2);

	DS18B20_DQ2_OUT_HIGH_1;

	DS18B20_IO_IN_1();

	delay_us(12);



	if(DS18B20_DQ2_IN_1)

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


void DS18B20_Start_1(void){

	DS18B20_Rst_1();

	DS18B20_Check_1();

	DS18B20_Write_Byte_1(0xcc);

	DS18B20_Write_Byte_1(0x44);

}


uint8_t DS18B20_Init_1(void){


	GPIO_InitTypeDef GPIO_InitStructure;

	GPIO_InitStructure.Pin = DQ2_Pin;

	GPIO_InitStructure.Mode = GPIO_MODE_OUTPUT_PP;

	GPIO_InitStructure.Pull = GPIO_PULLUP;

	GPIO_InitStructure.Speed = GPIO_SPEED_FREQ_HIGH;

	HAL_GPIO_Init(DQ2_GPIO_Port,&GPIO_InitStructure);



	DS18B20_Rst_1();

	return DS18B20_Check_1();

}

float DS18B20_Get_Temperature_1(void){


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

	temperature = (float)temperature;

	if(temperature)

	return temperature;

	else

	return -temperature;

}

// ??????9?(????93.75ms)
void DS18B20_SetLowResolution_1(void) {
    DS18B20_Rst_1();
    DS18B20_Write_Byte_1(0xCC);  // ??ROM
    DS18B20_Write_Byte_1(0x4E);  // ??????
    DS18B20_Write_Byte_1(0x7F);  // TH
    DS18B20_Write_Byte_1(0x80);  // TL
    DS18B20_Write_Byte_1(0x1F);  // 9????(0x1F = 00011111)
    DS18B20_Rst_1();
    DS18B20_Write_Byte_1(0xCC);
    DS18B20_Write_Byte_1(0x48);  // ???EEPROM
}

//typedef enum {
//    TEMP_IDLE,
//    TEMP_START_CONVERSION,
//    TEMP_WAIT_CONVERSION,
//    TEMP_READ_DATA
//} temp_state_t;

//temp_state_t temp_state = TEMP_IDLE;
//uint32_t temp_last_conv_time = 0;
//float current_temperature = 0.0f;

//void DS18B20_AsyncUpdate(void) {
//    switch(temp_state) {
//        case TEMP_IDLE:
//            if(HAL_GetTick() - temp_last_conv_time > 1000) {  // ??????
//                DS18B20_Rst_1();
//                DS18B20_Write_Byte_1(0xCC);
//                DS18B20_Write_Byte_1(0x44);  // ????
//                temp_state = TEMP_START_CONVERSION;
//                temp_last_conv_time = HAL_GetTick();
//            }
//            break;
//            
//        case TEMP_START_CONVERSION:
//            temp_state = TEMP_WAIT_CONVERSION;
//            break;
//            
//        case TEMP_WAIT_CONVERSION:
//            if(HAL_GetTick() - temp_last_conv_time > 750) {  // ??????
//                DS18B20_Rst_1();
//                DS18B20_Write_Byte_1(0xCC);
//                DS18B20_Write_Byte_1(0xBE);  // ?????
//                temp_state = TEMP_READ_DATA;
//            }
//            break;
//            
//        case TEMP_READ_DATA: {
//            uint8_t temp_l = DS18B20_Read_Byte_1();
//            uint8_t temp_h = DS18B20_Read_Byte_1();
//            int16_t temp = (temp_h << 8) | temp_l;
//            current_temperature = temp * 0.0625f;
//            temp_state = TEMP_IDLE;
//            break;
//        }
//    }
//}