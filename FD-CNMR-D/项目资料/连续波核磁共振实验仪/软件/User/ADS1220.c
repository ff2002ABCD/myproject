#include "main.h"

/***************************************************************************
函数名称:WriteOneByte(unsigned char 命令)
用途:写入一个字节到ADS1220
*************************************************************************/
void WriteOneByte(u8 command){
  u8 i;
  for(i=0;i<8;i++){
		ADS1220_SCLK = 1;
		if(command&0x80){
			ADS1220_DIN  = 1;
		}else{
			ADS1220_DIN  = 0;
		}
		command <<= 1;
		delay_us(1);
		ADS1220_SCLK = 0;
		delay_us(1);
  }
}
 
 
/***************************************************************************
*函数名称:ReadOneByte()
*用途:从ADS1220读取一个字节
*************************************************************************/
u8 ReadOneByte(void){
  u8 result,i;

	result = 0;
  for(i=0;i<8;i++){
		ADS1220_SCLK = 1;
		delay_us(1);
		result <<= 1;
		result += ADS1220_DOUT;
		ADS1220_SCLK = 0;
		delay_us(1);
  }

  return result;
}

/*******************************************************************************
* 函 数 名         : ADS1220_Init
* 函数功能		   : ADS1220初始化
* 输    入         : 无
* 输    出         : 无
*******************************************************************************/
void ADS1220_Init(void){
	GPIO_InitTypeDef GPIO_InitStructure;//定义结构体变量
	u8 Config[4];
	int temp_i;
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_2|GPIO_Pin_3|GPIO_Pin_5;  //选择你要设置的IO口
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_Out_PP;	 //设置推挽输出模式
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;	  //设置传输速率
	GPIO_Init(GPIOA,&GPIO_InitStructure); 	   /* 初始化GPIO */
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_4;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;//上拉输入
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	
	ADS1220_CS = 1;
	ADS1220_SCLK = 0;
	ADS1220_DIN = 0;
	delay_ms(1);
	
	ADS1220_CS = 0;
	delay_us(1);
	WriteOneByte(ADS1220_RESET);//复位器件
	delay_us(1);
	ADS1220_CS = 1;
	delay_ms(5);
	
	Config[0] = MUX_A0 + PGA_A0 + PGA_BYPASS;
	Config[1] = DR + MODE + ConverMode;
	Config[2] = VREF + FIR;
	Config[3] = DRDY_Mode;
	
	ADS1220_CS = 0;
	delay_us(1);
	ADS1220_WriteRegister(Register_0,4,Config);
	delay_us(1);
	ADS1220_CS = 1;
	delay_us(1);
	
//	temp_i = ADS1220_Single_shot();//1对应 VREF/2^23
//	Reality_VREF = 8388608.0 / temp_i * 2.5;	
	Reality_VREF = 5.0;
}

/*******************************************************************************
* 函 数 名         : ADS1220_Config
* 函数功能		   	 : 设置采集端口
* 输    入         : MUX_A0,2.5V确定基准;MUX_A1,励磁电压;MUX_A2,射频幅度;MUX_A3,毫特计
* 输    出         : 结果
*******************************************************************************/
int ADS1220_Config(u8 ain){
	u8 Config[2];
	u8 a,b,c;
	int jg,js;
	switch(ain){
		case 0: 
			Config[0] = MUX_A0 + PGA_A0 + PGA_BYPASS; 
			break;
		case 1: 
			Config[0] = MUX_A1 + PGA_A0 + PGA_BYPASS; 
			break;
		case 2: 
			Config[0] = MUX_A2 + PGA_A0 + PGA_BYPASS; 
			break;
		case 3: 
			Config[0] = MUX_A3 + PGA_A0 + PGA_BYPASS; 
			break;
		case 4: 
			Config[0] = MUX_A4 + PGA_A0 + PGA_BYPASS; 
			break;
		case 5: 
			Config[0] = MUX_A5 + PGA_A0 + PGA_BYPASS; 
			break;
	}
	
	ADS1220_CS = 0;
	delay_us(1);
	ADS1220_WriteRegister(Register_0,1,Config);
	delay_us(10);
	
	js = 0;
	while(ADS1220_DOUT == 1 && js < 100000){
		delay_us(10);
		js++;
	}
	delay_us(10);
	a = ReadOneByte();
	b = ReadOneByte();
	c = ReadOneByte();
	jg = a;
	jg = (jg<<8) | b;
	jg = (jg<<8) | c;

	delay_us(1);
	ADS1220_CS = 1;
	
	return jg;
}

/*******************************************************************************
* 函 数 名         : ADS1220_Single_shot
* 函数功能		   	 : 单次采集
* 输    入         : 无
* 输    出         : 结果
*******************************************************************************/
int ADS1220_Single_shot(void){
	u8 a,b,c;
	int jg,js;
	
	ADS1220_CS = 0;
	delay_us(1);
	WriteOneByte(ADS1220_START);//启动或重启转换
	delay_us(10);
	
	js = 0;
	while(ADS1220_DOUT == 1 && js < 100000){
		delay_us(10);
		js++;
	}
	delay_us(10);
	a = ReadOneByte();
	b = ReadOneByte();
	c = ReadOneByte();
	jg = a;
	jg = (jg<<8) | b;
	jg = (jg<<8) | c;
	
	delay_us(1);
	ADS1220_CS = 1;
	
	return jg;
}


/***************************************************************************
*函数名:ADS1220_WriteRegister(u8 StartAddress, u8 NumRegs, u8 * pData)
*用途:向寄存器写入数据 
* StartAddress	初始寄存器
* NumRegs				寄存器总数
* pData					写入的内容
*************************************************************************/
void ADS1220_WriteRegister(u8 StartAddress, u8 NumRegs, u8 *pData)
{
  u8 i,data;
  
	data = ADS1220_WREG + StartAddress + (NumRegs - 1);
  WriteOneByte(data);

  for (i=0;i<NumRegs;i++){
    WriteOneByte(pData[i]);
  }
}

//读寄存器
int ADS1220_ReadRegister(void){
	u8 data,a,b,c,d;
	int jg;
	
  ADS1220_CS = 0;
	delay_us(1);
	data = ADS1220_RREG + Register_0 + 3;
  WriteOneByte(data);
	a = ReadOneByte();
	b = ReadOneByte();
	c = ReadOneByte();
	d = ReadOneByte();
	jg = a;
	jg = (jg<<8) | b;
	jg = (jg<<8) | c;
	jg = (jg<<8) | d;
	
	delay_us(1);
	ADS1220_CS = 1;
	
	return jg;
}





