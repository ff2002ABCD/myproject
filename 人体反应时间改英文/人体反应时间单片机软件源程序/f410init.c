/////////////////////////////////////
//  Generated Initialization File  //
/////////////////////////////////////

#include "F410INIT.h"

// Peripheral specific initialization functions,
// Called from the Init_Device() function
void PCA_Init()
{
    PCA0MD    &= ~0x40;
    PCA0MD    = 0x0A;
    PCA0CPM1  = 0xC2;
    PCA0CPM5  = 0x48;
    PCA0L     = 0x01;
}

void Timer_Init()
{
    TCON      = 0x50;
    TMOD      = 0x25;
    TH1       = 0x30;
    TMR2CN    = 0x05;
    TMR2RLL   = 0xE2;
    TMR2RLH   = 0xFF;
    TMR2L     = 0xE2;
    TMR2H     = 0xFF;
    TMR3CN    = 0x05;
    TMR3RLL   = 0x24;
    TMR3RLH   = 0xFA;
    TMR3L     = 0x24;
    TMR3H     = 0xFA;
}

void UART_Init()
{
    SCON0     = 0x10;
}

void SPI_Init()
{
    SPI0CFG   = 0x40;
    SPI0CN    = 0x01;
    SPI0CKR   = 0x3C;
}

void ADC_Init()
{
    ADC0MX    = 0x10;
    ADC0CF    = 0xC8;
    ADC0CN    = 0x40;
    ADC0TK    = 0xF7;
}

void DAC_Init()
{
    IDA0CN    = 0xF4;
    IDA1CN    = 0xF7;
}

void Comparator_Init()
{
    int i = 0;
    CPT0CN    = 0x8F;
    for (i = 0; i < 35; i++);  // Wait 10us for initialization
    CPT0CN    &= ~0x30;
    CPT0MX    = 0x78;
    CPT0MD    = 0x80;
}

void Voltage_Reference_Init()
{
    REF0CN    = 0x13;
}

void Port_IO_Init()
{
    // P0.0  -  SCK  (SPI0), Open-Drain, Analog
    // P0.1  -  MISO (SPI0), Open-Drain, Analog
    // P0.2  -  MOSI (SPI0), Push-Pull,  Digital
    // P0.3  -  Unassigned,  Push-Pull,  Digital
    // P0.4  -  Unassigned,  Open-Drain, Digital
    // P0.5  -  Unassigned,  Open-Drain, Digital
    // P0.6  -  Skipped,     Push-Pull,  Digital
    // P0.7  -  Skipped,     Push-Pull,  Digital

    // P1.0  -  Unassigned,  Open-Drain, Analog
    // P1.1  -  Unassigned,  Open-Drain, Analog
    // P1.2  -  Unassigned,  Open-Drain, Digital
    // P1.3  -  Skipped,     Push-Pull,  Digital
    // P1.4  -  Unassigned,  Open-Drain, Digital
    // P1.5  -  Unassigned,  Open-Drain, Digital
    // P1.6  -  Unassigned,  Open-Drain, Digital
    // P1.7  -  Unassigned,  Push-Pull,  Digital

    // P2.0  -  Unassigned,  Open-Drain, Analog
    // P2.1  -  Skipped,     Open-Drain, Digital
    // P2.2  -  Unassigned,  Push-Pull,  Digital
    // P2.3  -  Unassigned,  Open-Drain, Digital
    // P2.4  -  Unassigned,  Open-Drain, Digital
    // P2.5  -  Unassigned,  Open-Drain, Digital
    // P2.6  -  Unassigned,  Open-Drain, Digital
    // P2.7  -  Unassigned,  Open-Drain, Digital

    P0MDIN    = 0xFC;
    P1MDIN    = 0xFC;
    P2MDIN    = 0xFE;
    P0MDOUT   = 0xCC;
    P1MDOUT   = 0x88;
    P2MDOUT   = 0x04;
    P0SKIP    = 0x3F;
    P1SKIP    = 0xF7;
    P2SKIP    = 0xFD;
    XBR0      = 0x02;
    XBR1      = 0x40;
}

void Oscillator_Init()
{
    int i = 0;
    PFE0CN    &= ~0x20;
    FLSCL     = 0x10;
    PFE0CN    |= 0x20;
    P1        |= 0x03;
    OSCXCN    = 0x67;
    for (i = 0; i < 3000; i++);  // Wait 1ms for initialization
    //while ((OSCXCN & 0x80) == 0);
    CLKMUL    = 0x81;
    for (i = 0; i < 20; i++);    // Wait 5us for initialization
    CLKMUL    |= 0xC0;
    while ((CLKMUL & 0x20) == 0);
    CLKSEL    = 0x02;
    OSCICN    = 0x07;
}

void Interrupts_Init()
{
    IP        = 0x20;
    IT01CF    = 0x76;
    IE        = 0x20;
}

// Initialization function for device,
// Call Init_Device() from your main program
void Init_Device(void)
{
    PCA_Init();
    Timer_Init();
    UART_Init();
    SPI_Init();
    ADC_Init();
    DAC_Init();
    Comparator_Init();
    Voltage_Reference_Init();
    Port_IO_Init();
    Oscillator_Init();
    Interrupts_Init();
}
