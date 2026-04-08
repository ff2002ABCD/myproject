/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
//#include "HMC5883.h"
//#include "5883.h"
#include "G85HAL.h"
#include "stdio.h"
#include "math.h"
#include "oled.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
_Bool flag_1s=0,flag_write;
double fangle,inclination; 
float rawGaX,rawGaY,rawGaZ,Xoffest=0,Yoffest=0,Zoffest=0,Kx=1,Ky=1,Kz=1,GaX,GaY,GaZ,Magangle,K_x,K_y,K_z;
int modify_num=0;
float *modify_now=NULL;
uint32_t writeFlashData;
uint16_t Count=10000,last_Count=10000;
uint16_t Diretion=0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

#ifdef __GNUC__
#define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
#define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif
PUTCHAR_PROTOTYPE
{
    //huart2
    HAL_UART_Transmit(&huart2 , (uint8_t *)&ch, 1 , 0xffff);
    return ch;
}

//debug 查看对应地址，是否正确，如果显示的是问号，则无此位置
//C6T6 32k  最大地址 0x08007FF0
//C8T6 64k  最大地址 0x0800FFE0
#define FLASH_SAVE_ADDR  0x08007000

static FLASH_EraseInitTypeDef EraseInitStruct = {
	.TypeErase = FLASH_TYPEERASE_PAGES,       //页擦除
	.PageAddress = FLASH_SAVE_ADDR,                //擦除地址
	.NbPages = 1                              //擦除页数
};

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  

	
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
	
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
 
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_I2C1_Init();
  MX_I2C2_Init();
  MX_TIM2_Init();
  MX_TIM1_Init();
  /* USER CODE BEGIN 2 */

	OLED_Init();
	//Init_HMC5883L_HAL_test(&hi2c1);
	//HAL_Delay(10);
	//hmc5883l_rawread(&rawGaX,&rawGaY,&rawGaZ);
//	K_x=(951+0.001)/820/rawGaX;
//	K_y=(951+0.001)/820/rawGaY;
//	K_z=(886+0.001)/820/rawGaZ;
	Init_HMC5883L_HAL(&hi2c1);
	TIM2->ARR=7200-1;
	TIM2->PSC=5000-1;
	HAL_TIM_Base_Start_IT(&htim2);
	TIM1->ARR=50000;
	TIM1->PSC=2-1;
	HAL_TIM_Encoder_Start(&htim1,TIM_CHANNEL_ALL);
	__HAL_TIM_SetCounter(&htim1,30000);
	
	Xoffest=(*(__IO uint32_t*)0x08007000+0.0001)/100;
	if(Xoffest>8) Xoffest-=10;
 // printf("%.2f",Kx);
	Kx=(*(__IO uint32_t*)0x08007004+0.0001)/100;
	Yoffest=(*(__IO uint32_t*)0x08007008+0.0001)/100;
	if(Yoffest>8) Yoffest-=10;
	Ky=(*(__IO uint32_t*)0x0800700C+0.0001)/100;
	Zoffest=(*(__IO uint32_t*)0x08007010+0.0001)/100;
	Kz=(*(__IO uint32_t*)0x08007014+0.0001)/100;
	if(Zoffest>8) Zoffest-=10;
//	caliboration(&Xoffest,&Yoffest,&Zoffest,&Kx,&Ky,&Kz);
	
//	Xoffest=-0.18;
//	Kx=2.49;
//	Yoffest=0.14;
//	Ky=2.79;
//	Zoffest=0.68;
//	Kz=1.47;
	
	
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */

  while (1)
  {				
				
//				HAL_Delay(500);
				//判断写入是否按下
				if(flag_write==1)
				{
					flag_write=0;
					HAL_FLASH_Unlock();
					uint32_t PageError = 0;
					__disable_irq();                             //擦除前关闭中断
					if (HAL_FLASHEx_Erase(&EraseInitStruct,&PageError) == HAL_OK)
					{
							printf("擦除 成功\r\n");
					}
					__enable_irq();                             //擦除后打开中断
					
					if(Xoffest<0) writeFlashData = Xoffest*100+1000;
					else writeFlashData = Xoffest*100;        //待写入的值
					uint32_t addr = 0x08007000;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					
					writeFlashData = Kx*100;        //待写入的值
					addr=0x08007004;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					
					if(Yoffest<0) writeFlashData =Yoffest*100+1000;
					else writeFlashData = Yoffest*100;        //待写入的值
					addr=0x08007008;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					
					writeFlashData = Ky*100;        //待写入的值
					addr=0x0800700C;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					
					if(Zoffest<0) writeFlashData =Zoffest*100+1000;
					writeFlashData = Zoffest*100;        //待写入的值
					addr=0x08007010;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					

					writeFlashData = Kz*100;        //待写入的值
					addr=0x08007014;                  //写入的地址
					HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
					printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
					
					
					OLED_ShowString(4,15,"ok");
					HAL_Delay(2000);
					OLED_ShowString(4,15,"  ");
					
					HAL_FLASH_Lock();
				}
				
				if(flag_1s==1)
				{
					flag_1s=0;
					hmc5883l_rawread(&rawGaX,&rawGaY,&rawGaZ);
					GaX = (rawGaX - Xoffest) * Kx;
					GaY = (rawGaY - Yoffest) * Ky;
					GaZ = (rawGaZ - Zoffest) * Kz;
					if((GaX > 0)&&(GaY > 0)) Magangle = atan(GaY/GaX)*57;
					else if((GaX > 0)&&(GaY < 0)) Magangle = 360+atan(GaY/GaX)*57;
					else if((GaX == 0)&&(GaY > 0)) Magangle = 90;
					else if((GaX == 0)&&(GaY < 0)) Magangle = 270;
					else if(GaX < 0) Magangle = 180+atan(GaY/GaX)*57;
					double temp=sqrt(GaX*GaX+GaY*GaY);
					inclination= atan((GaZ+0.001)/temp)*57.3;  
					char temp_c[20];
					
					switch(modify_num)
					{
						case 0:break;
						case 1:
						{
							OLED_ShowString(1,7,"     ");
							modify_now=&Xoffest;
						}break;
						case 2:
						{
							OLED_ShowString(1,13,"    ");
							modify_now=&Kx;
						}break;
						case 3:
						{
							OLED_ShowString(2,7,"     ");
							modify_now=&Yoffest;
						}break;
						case 4:
						{
							OLED_ShowString(2,13,"    ");
							modify_now=&Ky;
						}break;
						case 5:
						{
							OLED_ShowString(3,7,"     ");
							modify_now=&Zoffest;
						}break;
						case 6:
						{
							OLED_ShowString(3,13,"    ");
							modify_now=&Kz;
						}break;
					}
					
					sprintf(temp_c,"%.2f ",GaX);
					//OLED_ShowString(1,1,"      ");
					OLED_ShowString(1,1,temp_c);
					sprintf(temp_c,"%.2f",Xoffest);
					//OLED_ShowString(1,7,"     ");
					OLED_ShowString(1,7,temp_c);
					sprintf(temp_c,"%.2f",Kx);
					//OLED_ShowString(1,13,"     ");
					OLED_ShowString(1,13,temp_c);
					
					sprintf(temp_c,"%.2f ",GaY);
				//	OLED_ShowString(2,1,"      ");
					OLED_ShowString(2,1,temp_c);
					sprintf(temp_c,"%.2f",Yoffest);
					//OLED_ShowString(2,7,"     ");
					OLED_ShowString(2,7,temp_c);
					sprintf(temp_c,"%.2f",Ky);
					//OLED_ShowString(2,13,"     ");
					OLED_ShowString(2,13,temp_c);
					
					sprintf(temp_c,"%.2f ",GaZ);
				//	OLED_ShowString(3,1,"      ");
					OLED_ShowString(3,1,temp_c);
					sprintf(temp_c,"%.2f",Zoffest);
					//OLED_ShowString(3,7,"     ");
					OLED_ShowString(3,7,temp_c);
					sprintf(temp_c,"%.2f",Kz);
					//OLED_ShowString(2,13,"     ");
					OLED_ShowString(3,13,temp_c);
					
					sprintf(temp_c,"%.2f",Magangle);
				//	OLED_ShowString(4,1,"     ");
					OLED_ShowString(4,1,temp_c);
					
					sprintf(temp_c,"%.2f",inclination);
				//	OLED_ShowString(4,8,"     ");
					OLED_ShowString(4,8,temp_c);
					
					//修改参数
				last_Count=Count;
				Diretion =  __HAL_TIM_IS_TIM_COUNTING_DOWN(&htim1);     
				Count = __HAL_TIM_GET_COUNTER(&htim1);
				printf("转动方向:%d  脉冲数:%d \r\n",Diretion,Count );
				if(Diretion==0) if(Count-last_Count<0) last_Count=Count-1;
				if(Diretion==1) if(Count-last_Count>0) last_Count=Count+1;
				if(modify_num!=0) *modify_now+=0.01*(Count-last_Count);
				
					HAL_TIM_Base_Start_IT(&htim2);
				}
				
	
    
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
						
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{		
	if(GPIO_Pin==GPIO_PIN_12)
	{
		HAL_Delay(20);
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)==GPIO_PIN_RESET)
		{
			HAL_Delay(400);
			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)==GPIO_PIN_RESET)
			{
				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)==GPIO_PIN_RESET)
				{
				
				}
				//changan
				flag_write=1;
				printf("changan\r\n");
				
			}
			else
			{
				//duanan
				printf("duanan\r\n");
				modify_num+=1;
				if(modify_num==7) modify_num=0;
			}
		}
	}
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{	
	if(htim->Instance==htim2.Instance)
	{			
				HAL_TIM_Base_Stop(&htim2);
				flag_1s=1;
	}
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
