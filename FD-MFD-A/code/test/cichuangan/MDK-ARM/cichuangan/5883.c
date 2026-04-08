#include "5883.h"

#define R_SDA    IPB13          
#define W_SDA    OPB13          
#define W_SCL    OPB14         
  

#define Xmsb 0     //X??????8?
#define Xlsb 1       //X??????8? 	
#define Zmsb 2     //Z??????8?
#define Zlsb 3       //Z??????8?
#define Ymsb 4     //Y??????8?
#define Ylsb 5       //Y??????8?

#define GPIOB_ODR_Addr    (GPIOB_BASE+12) //0x40010C0C 
#define GPIOB_IDR_Addr    (GPIOB_BASE+8) //0x40010C08   

#define BITBAND_Addr(Addr,num)  ((volatile unsigned long *)(0x42000000+32*(Addr-0x40000000)+4*num))

#define IPB13    *BITBAND_Addr(GPIOB_IDR_Addr,13)
#define OPB13   *BITBAND_Addr(GPIOB_ODR_Addr,13)
#define OPB14   *BITBAND_Addr(GPIOB_ODR_Addr,14)

void _delay()
{
	int TIM=72*5;	
	while(TIM--);
}
void _iic_Start()
{
     W_SCL=1;    
     W_SDA=1;
     _delay();
     W_SDA=0;     //SCL??,??SDA,????IIC??,????
     _delay();
     W_SCL=0;     //??SCL
     _delay();
}

void _iic_Stop()
{
     W_SCL=1;     //??SCL(?????????,SCL????)
     W_SDA=0;     
     _delay();
     W_SDA=1;   //SCL???,??SDA????ICC??,????
}

uint8_t _iic_SendByte(uint8_t dat)          
{
        uint8_t i;
     for(i=0;i<8;i++)
    {
        _delay();
        W_SDA=dat>>7;     //SCL?????SDA
        dat=dat<<1;
        _delay();
        W_SCL=1;         //??SCL,???????SDA 
        _delay();
        W_SCL=0;         //????SCL
    }
       W_SDA=1;             //??SDA
       W_SCL=1;             //??SCL,?????????
      //   ???? 
    i=100;
    while(i&&R_SDA)  {i--;_delay();}
    if(i==0)               //???
    {
        W_SCL=0;         //????SCL
        return 0;
    }
    else {                 //???
        _delay();
        W_SCL=0;         //????SCL
        return 1;
}
}

uint8_t _iic_ReadByte(uint8_t Ack)  
{
     uint8_t temp,i;
     W_SDA=1;              //??SDA
     _delay();
    for(i=0;i<8;i++)
    {
        _delay();
        W_SCL=1;          //??SCL????SDA          
        temp=temp<<1;      
        temp|=R_SDA;      //SCL??????SDA
        W_SCL=0;              //??SCL,?????????
     }
     //??????
    if(Ack)W_SDA=0;             //??SDA????
    W_SCL=1;             //??SCL,?????????
    _delay();
    W_SCL=0;             //????SCL
    W_SDA=1;             //??SDA
    return temp;
}

void HMC5883L_Init()
 {     
     _iic_Start();
     _iic_SendByte(0x3c); //???
     _iic_SendByte(0x00); //????00,?????A 
     _iic_SendByte(0x78);  //?????????75hz
     _iic_Start();          //?????02,?????
     _iic_SendByte(0x3c);
     _iic_SendByte(0x02);
     _iic_SendByte(0x00);  //??????
     _iic_Stop();
 }
 
 int16_t HMC5883L_ReadAngle()
{
static uint8_t i; 
static uint8_t XYZ_Data[6]; //?????????????

_iic_Start();
_iic_SendByte(0x3c); // ??HMC5883L?????0x3c,???
_iic_SendByte(0x03); //????03,X msb???   
_iic_Start();          
_iic_SendByte(0x3d); //?????

//???????????
for(i=0;i<5;i++)        //?5?????????
{
XYZ_Data[i]=_iic_ReadByte(1);
}
XYZ_Data[5] =_iic_ReadByte(0);  //???
_iic_Stop();
return atan2( (double)((int16_t)((XYZ_Data[Ymsb]<<8)+XYZ_Data[Ylsb]) ),(double)((int16_t)((XYZ_Data[Xmsb]<<8)+XYZ_Data[Xlsb])))*(180/3.14159265)+180;       //????,????math.h???
}