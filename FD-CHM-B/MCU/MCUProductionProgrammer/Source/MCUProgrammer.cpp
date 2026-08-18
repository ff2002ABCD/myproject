// MCUProgrammer.cpp : Defines the class behaviors for the application.
//

#include "stdafx.h"
#include "MCUProgrammer.h"
#include "MCUProgrammerDlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CMCUProgrammerApp

BEGIN_MESSAGE_MAP(CMCUProgrammerApp, CWinApp)
	//{{AFX_MSG_MAP(CMCUProgrammerApp)
	//}}AFX_MSG
	ON_COMMAND(ID_HELP, CWinApp::OnHelp)
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CMCUProgrammerApp construction

CMCUProgrammerApp::CMCUProgrammerApp()
{
}

/////////////////////////////////////////////////////////////////////////////
// The one and only CMCUProgrammerApp object

CMCUProgrammerApp theApp;

/////////////////////////////////////////////////////////////////////////////
// CMCUProgrammerApp initialization

BOOL CMCUProgrammerApp::InitInstance()
{
	AfxEnableControlContainer();

	// Standard initialization
	AfxInitRichEdit();

#ifdef _AFXDLL
	Enable3dControls();			// Call this when using MFC in a shared DLL
#else
	Enable3dControlsStatic();	// Call this when linking to MFC statically
#endif

	CMCUProgrammerDlg dlg;
	m_pMainWnd = &dlg;
	int nResponse = dlg.DoModal();
	if (nResponse == IDOK)
	{
	}
	else if (nResponse == IDCANCEL)
	{
	}

	// Since the dialog has been closed, return FALSE so that we exit the
	//  application, rather than start the application's message pump.
	return FALSE;
}
