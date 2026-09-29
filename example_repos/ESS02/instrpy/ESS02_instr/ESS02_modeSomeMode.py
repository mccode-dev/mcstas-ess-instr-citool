#!/usr/bin/env python3
# Automatically generated file. 
# Format:    Python script code
# McStas <http://www.mcstas.org>
# Instrument: ESS02_modeSomeMode.instr (ESS02_modeSomeMode)
# File:       ESS02_modeSomeMode.py

import mcstasscript as ms
import argparse

# Python McStas instrument description
def make(input_path=None):
    instr = ms.McStas_instr("ESS02_modeSomeMode", author = "McCode Py-Generator", origin = "ESS DMSC", input_path=input_path)
    
# Add collected DEPENDENCY strings
    instr.set_dependency('')

    # *****************************************************************************
    # * Start of instrument 'ESS02_modeSomeMode' generated code
    # *****************************************************************************


    # *****************************************************************************
    # * instrument 'ESS02_modeSomeMode' and components DECLARE
    # *****************************************************************************

    # Instrument parameters:

    sector = instr.add_parameter('string', 'sector', value='"S"', comment='Parameter type (string) added by McCode py-generator')
    beamline = instr.add_parameter('int', 'beamline', value=2, comment='Parameter type (int) added by McCode py-generator')
    Lmin = instr.add_parameter('double', 'Lmin', value=0.2, comment='Parameter type (double) added by McCode py-generator')
    Lmax = instr.add_parameter('double', 'Lmax', value=20, comment='Parameter type (double) added by McCode py-generator')
    c_performance = instr.add_parameter('double', 'c_performance', value=1, comment='Parameter type (double) added by McCode py-generator')
    t_performance = instr.add_parameter('double', 't_performance', value=1, comment='Parameter type (double) added by McCode py-generator')
    index = instr.add_parameter('int', 'index', value=0, comment='Parameter type (int) added by McCode py-generator')
    dist = instr.add_parameter('double', 'dist', value=2, comment='Parameter type (double) added by McCode py-generator')
    cold = instr.add_parameter('double', 'cold', value=0.5, comment='Parameter type (double) added by McCode py-generator')
    Yheight = instr.add_parameter('double', 'Yheight', value=0.03, comment='Parameter type (double) added by McCode py-generator')
    delta = instr.add_parameter('double', 'delta', value=0, comment='Parameter type (double) added by McCode py-generator')
    n_pulses = instr.add_parameter('int', 'n_pulses', value=1, comment='Parameter type (int) added by McCode py-generator')
    allmons = instr.add_parameter('int', 'allmons', value=0, comment='Parameter type (int) added by McCode py-generator')

    component_definition_metadata = {
    }
    instr.append_declare(r'''
    double calcAlpha(double length, double radius) {
    // calculate angle of arm after curved guide
    return RAD2DEG * length/radius;
  }

  double calcX(double length, double radius) {
    // calculate position and angle of arm after curved guide
    double alpha = DEG2RAD * calcAlpha(length, radius);
    return radius*(1.0-cos(alpha));
  }

  double calcZ(double length, double radius) {
    // calculate position and angle of arm after curved guide
    double alpha = DEG2RAD * calcAlpha(length, radius);
    return radius*sin(alpha);
  }

  double XW, YH;
  char options1[256],options2[256],options3[256],options4[256];
  char srcdef[128];
  double WidthC=0.072,WidthT=0.108;
  double lambdamin, lambdamax;
  double TCollmin;
  double TCollmax;
  #pragma acc declare create(TCollmin,TCollmax)
  double EminTh=20, EmaxTh=100, EminC=0, EmaxC=20;
  #pragma acc declare create(EminTh,EmaxTh,EminC,EmaxC)
  /* 10 beamlines in sector N and E  - plus one location added for drawing */
  double iBeamlinesN[] = { 30.0,  36.0,  42.0,  48.0,  54.0,  60.0,  66.0,  72.0,  78.0,  84.0,  90.0};
  double iBeamlinesE[] = {-30.0, -36.0, -42.0, -48.0, -54.0, -60.0, -66.0, -72.0, -78.0, -84.0, -90.0};
  /* 11 beamlines in sector S and W - plus one location added for drawing */
  double iBeamlinesW[] = { 150.0,  144.7,  138.0,  132.7,  126.0,  120.7,  114.0,  108.7,  102.0,  96.7,  90.0,  84.0};
  double iBeamlinesS[] = {-150.0, -144.7, -138.0, -132.7, -126.0, -120.7, -114.0, -108.7, -102.0, -96.7, -90.0, -84.0};
  double* iBeamlines;
  double ANGLE;
  double DeltaX,DeltaZ;
    ''')


    instr.append_initialize(r'''
  lambdamin=Lmin;
  lambdamax=Lmax;
  XW=1.05*(WidthC+2*WidthT);
  YH=1.05*Yheight;
  sprintf(options1,"user1 bins=201 limits=[-%g,%g]",XW/2,XW/2);
  sprintf(options4,"user1 bins=201 limits=[-%g,%g]",YH/2,YH/2);
  sprintf(options2,"user1 bins=201 limits=[-%g,%g], user2 bins=201 limits=[-%g,%g]",XW/2,XW/2,YH/2,YH/2);
  sprintf(options3,"user1 bins=201 limits=[-%g,%g], user2 bins=201 limits=[-%g,%g]",1.05*(WidthC/2),1.05*(WidthC/2),1.05*Yheight/2,1.05*Yheight/2);
  sprintf(srcdef,"2015");
  if (beamline==1) {
    TCollmin=0;
    TCollmax=0.058;
  } else if (beamline==2) {
    TCollmin=0;
    TCollmax=0.06;
  }
  else {
    TCollmin=0.011;
    TCollmax=0.071;
  }
  #pragma acc update device(TCollmin,TCollmax)
  if (strcasestr(sector,"N")) {
    iBeamlines=iBeamlinesN;
    DeltaX=-0.0585; DeltaZ=0.0925;
  } else if (strcasestr(sector,"W")) {
    iBeamlines=iBeamlinesW;
    DeltaX=0.0585; DeltaZ=0.0925;
  } else if (strcasestr(sector,"S")) {
    iBeamlines=iBeamlinesS;
    DeltaX=0.0585; DeltaZ=-0.0925;
  } else if (strcasestr(sector,"E")) {
    iBeamlines=iBeamlinesE;
    DeltaX=-0.0585; DeltaZ=-0.0925;
  }
  ANGLE=iBeamlines[beamline-1]-90;
  #pragma acc update device(EminTh,EmaxTh,EminC,EmaxC)
    ''')


    uv_IsCold = instr.add_user_var("int ", "IsCold", comment="USERVAR added by McCode py-generator")
    uv_SrcX = instr.add_user_var("double ", "SrcX", comment="USERVAR added by McCode py-generator")
    uv_SrcY = instr.add_user_var("double ", "SrcY", comment="USERVAR added by McCode py-generator")
    uv_SrcZ = instr.add_user_var("double ", "SrcZ", comment="USERVAR added by McCode py-generator")
    uv_E_min = instr.add_user_var("double ", "E_min", comment="USERVAR added by McCode py-generator")
    uv_E_max = instr.add_user_var("double ", "E_max", comment="USERVAR added by McCode py-generator")
    uv_Eneutron = instr.add_user_var("double ", "Eneutron", comment="USERVAR added by McCode py-generator")
    uv_T0 = instr.add_user_var("double ", "T0", comment="USERVAR added by McCode py-generator")
    uv_L0 = instr.add_user_var("double ", "L0", comment="USERVAR added by McCode py-generator")
    # *****************************************************************************
    # * instrument 'ESS02_modeSomeMode' TRACE
    # *****************************************************************************
    
    # Comp instance Origin, placement and parameters
    Origin = instr.add_component('Origin','Progress_bar')
    
    Origin.profile = '"NULL"'
    Origin.percent = '10'
    Origin.flag_save = '0'
    Origin.minutes = '0'
    
    # Comp instance vinROT2, placement and parameters
    vinROT2 = instr.add_component('vinROT2','Arm', AT=['0', '0', '0'], AT_RELATIVE='Origin', ROTATED=['0', '-90', '0'], ROTATED_RELATIVE='Origin')
    
    
    # Comp instance vinROT1, placement and parameters
    vinROT1 = instr.add_component('vinROT1','Arm', AT=['0', '0', '0'], AT_RELATIVE='vinROT2', ROTATED=['-90', '0', '0'], ROTATED_RELATIVE='vinROT2')
    
    
    # Comp instance vin, placement and parameters
    vin = instr.add_component('vin','Arm', AT=['0', '0', '0'], AT_RELATIVE='vinROT1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='vinROT1')
    
    
    # Comp instance Source, placement and parameters
    Source = instr.add_component('Source','ESS_butterfly', AT=['DeltaX', '0', 'DeltaZ'], ROTATED=['0', 'ANGLE', '0'])
    
    Source.sector = 'sector'
    Source.beamline = 'beamline'
    Source.yheight = 'Yheight'
    Source.cold_frac = 'cold'
    Source.target_index = 'index'
    Source.dist = 'dist'
    Source.focus_xw = '0.12'
    Source.focus_yh = '0.12'
    Source.c_performance = 'c_performance'
    Source.t_performance = 't_performance'
    Source.Lmin = 'Lmin'
    Source.Lmax = 'Lmax'
    Source.tmax_multiplier = '3'
    Source.n_pulses = 'n_pulses'
    Source.acc_power = '5'
    Source.tfocus_dist = '0'
    Source.tfocus_time = '0'
    Source.tfocus_width = '0'
    
    # Comp instance Sphere0, placement and parameters
    Sphere0 = instr.add_component('Sphere0','PSD_monitor_4PI', AT=['0', '0', '0'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( allmons ) at Sphere0
    Sphere0.set_WHEN('( allmons )')
    
    Sphere0.nx = '90'
    Sphere0.ny = '90'
    Sphere0.filename = '"rotated"'
    Sphere0.nowritefile = '! allmons'
    Sphere0.radius = '2.2'
    Sphere0.restore_neutron = '1'
    
    # Comp instance BackTrace, placement and parameters
    BackTrace = instr.add_component('BackTrace','Shape', AT=['0', '0', '0.08'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # EXTEND at BackTrace
    BackTrace.append_EXTEND(r'''
  double myL = (2*PI/V2K)/sqrt(vx*vx + vy*vy + vz*vz);

  /* Measure location and energy for later use */
  SrcX=x;SrcY=y;SrcZ=z;
  Eneutron=VS2E*(vx*vx + vy*vy + vz*vz);
  if (Eneutron>EminTh) {
    E_min=EminC;E_max=EmaxC;
    IsCold=0;
  } else {
    E_min=EminTh;E_max=EmaxTh;
    IsCold=1;
  }
  T0=t;
  L0=myL;
    ''')


    
    BackTrace.geometry = '0'
    BackTrace.radius = '0'
    BackTrace.xwidth = '0.3'
    BackTrace.yheight = '0.3'
    BackTrace.zdepth = '0'
    BackTrace.thickness = '0'
    BackTrace.nx = '0'
    BackTrace.ny = '1'
    BackTrace.nz = '0'
    BackTrace.center = '1'
    
    # Comp instance POSTATSource, placement and parameters
    POSTATSource = instr.add_component('POSTATSource','PSD_monitor', AT=['0', '0', '0'], AT_RELATIVE='BackTrace', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='BackTrace')
    
    POSTATSource.nx = '90'
    POSTATSource.ny = '90'
    POSTATSource.filename = '0'
    POSTATSource.xmin = '-0.05'
    POSTATSource.xmax = '0.05'
    POSTATSource.ymin = '-0.05'
    POSTATSource.ymax = '0.05'
    POSTATSource.xwidth = '0.31'
    POSTATSource.yheight = '0.31'
    POSTATSource.restore_neutron = '0'
    POSTATSource.nowritefile = '0'
    
    # Comp instance Arm1, placement and parameters
    Arm1 = instr.add_component('Arm1','Arm', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    
    # Comp instance Arm2, placement and parameters
    Arm2 = instr.add_component('Arm2','Arm', AT=['0', '0', '3.5'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    
    # Comp instance AutoTOFL0, placement and parameters
    AutoTOFL0 = instr.add_component('AutoTOFL0','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='BackTrace', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='BackTrace')
    
    AutoTOFL0.user0 = '""'
    AutoTOFL0.user1 = '"T0"'
    AutoTOFL0.user2 = '"L0"'
    AutoTOFL0.user3 = '""'
    AutoTOFL0.user4 = '""'
    AutoTOFL0.user5 = '""'
    AutoTOFL0.user6 = '""'
    AutoTOFL0.user7 = '""'
    AutoTOFL0.user8 = '""'
    AutoTOFL0.user9 = '""'
    AutoTOFL0.xwidth = 'XW'
    AutoTOFL0.yheight = 'YH'
    AutoTOFL0.zdepth = '0'
    AutoTOFL0.xmin = '0'
    AutoTOFL0.xmax = '0'
    AutoTOFL0.ymin = '0'
    AutoTOFL0.ymax = '0'
    AutoTOFL0.zmin = '0'
    AutoTOFL0.zmax = '0'
    AutoTOFL0.bins = '0'
    AutoTOFL0.min = '-1e40'
    AutoTOFL0.max = '1e40'
    AutoTOFL0.restore_neutron = '1'
    AutoTOFL0.radius = '0'
    AutoTOFL0.options = '"user1 limits=[0 5e-3] bins=51, user2 limits=[0.1 20] bins=41"'
    AutoTOFL0.filename = '"AutoTOFL0"'
    AutoTOFL0.geometry = '"NULL"'
    AutoTOFL0.nowritefile = '0'
    AutoTOFL0.nexus_bins = '0'
    AutoTOFL0.username0 = '"NULL"'
    AutoTOFL0.username1 = '"NULL"'
    AutoTOFL0.username2 = '"NULL"'
    AutoTOFL0.username3 = '"NULL"'
    AutoTOFL0.username4 = '"NULL"'
    AutoTOFL0.username5 = '"NULL"'
    AutoTOFL0.username6 = '"NULL"'
    AutoTOFL0.username7 = '"NULL"'
    AutoTOFL0.username8 = '"NULL"'
    AutoTOFL0.username9 = '"NULL"'
    
    # Comp instance AutoTOF0, placement and parameters
    AutoTOF0 = instr.add_component('AutoTOF0','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='AutoTOFL0', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='AutoTOFL0')
    
    AutoTOF0.user0 = '""'
    AutoTOF0.user1 = '"T0"'
    AutoTOF0.user2 = '""'
    AutoTOF0.user3 = '""'
    AutoTOF0.user4 = '""'
    AutoTOF0.user5 = '""'
    AutoTOF0.user6 = '""'
    AutoTOF0.user7 = '""'
    AutoTOF0.user8 = '""'
    AutoTOF0.user9 = '""'
    AutoTOF0.xwidth = 'XW'
    AutoTOF0.yheight = 'YH'
    AutoTOF0.zdepth = '0'
    AutoTOF0.xmin = '0'
    AutoTOF0.xmax = '0'
    AutoTOF0.ymin = '0'
    AutoTOF0.ymax = '0'
    AutoTOF0.zmin = '0'
    AutoTOF0.zmax = '0'
    AutoTOF0.bins = '0'
    AutoTOF0.min = '-1e40'
    AutoTOF0.max = '1e40'
    AutoTOF0.restore_neutron = '1'
    AutoTOF0.radius = '0'
    AutoTOF0.options = '"user1 limits=[0 5e-3] bins=51"'
    AutoTOF0.filename = '"AutoTOF0"'
    AutoTOF0.geometry = '"NULL"'
    AutoTOF0.nowritefile = '0'
    AutoTOF0.nexus_bins = '0'
    AutoTOF0.username0 = '"NULL"'
    AutoTOF0.username1 = '"NULL"'
    AutoTOF0.username2 = '"NULL"'
    AutoTOF0.username3 = '"NULL"'
    AutoTOF0.username4 = '"NULL"'
    AutoTOF0.username5 = '"NULL"'
    AutoTOF0.username6 = '"NULL"'
    AutoTOF0.username7 = '"NULL"'
    AutoTOF0.username8 = '"NULL"'
    AutoTOF0.username9 = '"NULL"'
    
    # Comp instance AutoL0, placement and parameters
    AutoL0 = instr.add_component('AutoL0','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='AutoTOF0', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='AutoTOF0')
    
    AutoL0.user0 = '""'
    AutoL0.user1 = '"L0"'
    AutoL0.user2 = '""'
    AutoL0.user3 = '""'
    AutoL0.user4 = '""'
    AutoL0.user5 = '""'
    AutoL0.user6 = '""'
    AutoL0.user7 = '""'
    AutoL0.user8 = '""'
    AutoL0.user9 = '""'
    AutoL0.xwidth = 'XW'
    AutoL0.yheight = 'YH'
    AutoL0.zdepth = '0'
    AutoL0.xmin = '0'
    AutoL0.xmax = '0'
    AutoL0.ymin = '0'
    AutoL0.ymax = '0'
    AutoL0.zmin = '0'
    AutoL0.zmax = '0'
    AutoL0.bins = '0'
    AutoL0.min = '-1e40'
    AutoL0.max = '1e40'
    AutoL0.restore_neutron = '1'
    AutoL0.radius = '0'
    AutoL0.options = '"user1 limits=[0.1 20] bins=41"'
    AutoL0.filename = '"AutoL0"'
    AutoL0.geometry = '"NULL"'
    AutoL0.nowritefile = '0'
    AutoL0.nexus_bins = '0'
    AutoL0.username0 = '"NULL"'
    AutoL0.username1 = '"NULL"'
    AutoL0.username2 = '"NULL"'
    AutoL0.username3 = '"NULL"'
    AutoL0.username4 = '"NULL"'
    AutoL0.username5 = '"NULL"'
    AutoL0.username6 = '"NULL"'
    AutoL0.username7 = '"NULL"'
    AutoL0.username8 = '"NULL"'
    AutoL0.username9 = '"NULL"'
    
    # Comp instance PSD0, placement and parameters
    PSD0 = instr.add_component('PSD0','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='AutoL0', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='AutoL0')
    
    PSD0.user0 = '""'
    PSD0.user1 = '"SrcX"'
    PSD0.user2 = '"SrcY"'
    PSD0.user3 = '""'
    PSD0.user4 = '""'
    PSD0.user5 = '""'
    PSD0.user6 = '""'
    PSD0.user7 = '""'
    PSD0.user8 = '""'
    PSD0.user9 = '""'
    PSD0.xwidth = '0.2'
    PSD0.yheight = '0.2'
    PSD0.zdepth = '0'
    PSD0.xmin = '0'
    PSD0.xmax = '0'
    PSD0.ymin = '0'
    PSD0.ymax = '0'
    PSD0.zmin = '0'
    PSD0.zmax = '0'
    PSD0.bins = '0'
    PSD0.min = '-1e40'
    PSD0.max = '1e40'
    PSD0.restore_neutron = '1'
    PSD0.radius = '0'
    PSD0.options = '"user1 limits=[-0.1 0.1] bins=90, user2 limits=[-0.1 0.1] bins=90,"'
    PSD0.filename = '"flat"'
    PSD0.geometry = '"NULL"'
    PSD0.nowritefile = '0'
    PSD0.nexus_bins = '0'
    PSD0.username0 = '"NULL"'
    PSD0.username1 = '"NULL"'
    PSD0.username2 = '"NULL"'
    PSD0.username3 = '"NULL"'
    PSD0.username4 = '"NULL"'
    PSD0.username5 = '"NULL"'
    PSD0.username6 = '"NULL"'
    PSD0.username7 = '"NULL"'
    PSD0.username8 = '"NULL"'
    PSD0.username9 = '"NULL"'
    
    # Comp instance PSD1, placement and parameters
    PSD1 = instr.add_component('PSD1','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='PSD0', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='PSD0')
    # WHEN ( Eneutron < EminTh ) at PSD1
    PSD1.set_WHEN('( Eneutron < EminTh )')
    
    PSD1.user0 = '""'
    PSD1.user1 = '"SrcX"'
    PSD1.user2 = '"SrcY"'
    PSD1.user3 = '""'
    PSD1.user4 = '""'
    PSD1.user5 = '""'
    PSD1.user6 = '""'
    PSD1.user7 = '""'
    PSD1.user8 = '""'
    PSD1.user9 = '""'
    PSD1.xwidth = '0.2'
    PSD1.yheight = '0.2'
    PSD1.zdepth = '0'
    PSD1.xmin = '0'
    PSD1.xmax = '0'
    PSD1.ymin = '0'
    PSD1.ymax = '0'
    PSD1.zmin = '0'
    PSD1.zmax = '0'
    PSD1.bins = '0'
    PSD1.min = '-1e40'
    PSD1.max = '1e40'
    PSD1.restore_neutron = '1'
    PSD1.radius = '0'
    PSD1.options = '"user1 limits=[-0.1 0.1] bins=90, user2 limits=[-0.1 0.1] bins=90,"'
    PSD1.filename = '"flatC"'
    PSD1.geometry = '"NULL"'
    PSD1.nowritefile = '0'
    PSD1.nexus_bins = '0'
    PSD1.username0 = '"NULL"'
    PSD1.username1 = '"NULL"'
    PSD1.username2 = '"NULL"'
    PSD1.username3 = '"NULL"'
    PSD1.username4 = '"NULL"'
    PSD1.username5 = '"NULL"'
    PSD1.username6 = '"NULL"'
    PSD1.username7 = '"NULL"'
    PSD1.username8 = '"NULL"'
    PSD1.username9 = '"NULL"'
    
    # Comp instance PSD2, placement and parameters
    PSD2 = instr.add_component('PSD2','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='PSD1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='PSD1')
    # WHEN ( Eneutron >= EminTh ) at PSD2
    PSD2.set_WHEN('( Eneutron >= EminTh )')
    
    PSD2.user0 = '""'
    PSD2.user1 = '"SrcX"'
    PSD2.user2 = '"SrcY"'
    PSD2.user3 = '""'
    PSD2.user4 = '""'
    PSD2.user5 = '""'
    PSD2.user6 = '""'
    PSD2.user7 = '""'
    PSD2.user8 = '""'
    PSD2.user9 = '""'
    PSD2.xwidth = '0.16'
    PSD2.yheight = '0.16'
    PSD2.zdepth = '0'
    PSD2.xmin = '0'
    PSD2.xmax = '0'
    PSD2.ymin = '0'
    PSD2.ymax = '0'
    PSD2.zmin = '0'
    PSD2.zmax = '0'
    PSD2.bins = '0'
    PSD2.min = '-1e40'
    PSD2.max = '1e40'
    PSD2.restore_neutron = '1'
    PSD2.radius = '0'
    PSD2.options = '"user1 limits=[-0.1 0.1] bins=90, user2 limits=[-0.1 0.1] bins=90,"'
    PSD2.filename = '"flatT"'
    PSD2.geometry = '"NULL"'
    PSD2.nowritefile = '0'
    PSD2.nexus_bins = '0'
    PSD2.username0 = '"NULL"'
    PSD2.username1 = '"NULL"'
    PSD2.username2 = '"NULL"'
    PSD2.username3 = '"NULL"'
    PSD2.username4 = '"NULL"'
    PSD2.username5 = '"NULL"'
    PSD2.username6 = '"NULL"'
    PSD2.username7 = '"NULL"'
    PSD2.username8 = '"NULL"'
    PSD2.username9 = '"NULL"'
    
    # Comp instance MonND1, placement and parameters
    MonND1 = instr.add_component('MonND1','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    MonND1.user0 = '""'
    MonND1.user1 = '"SrcX"'
    MonND1.user2 = '""'
    MonND1.user3 = '""'
    MonND1.user4 = '""'
    MonND1.user5 = '""'
    MonND1.user6 = '""'
    MonND1.user7 = '""'
    MonND1.user8 = '""'
    MonND1.user9 = '""'
    MonND1.xwidth = 'XW'
    MonND1.yheight = 'YH'
    MonND1.zdepth = '0'
    MonND1.xmin = '0'
    MonND1.xmax = '0'
    MonND1.ymin = '0'
    MonND1.ymax = '0'
    MonND1.zmin = '0'
    MonND1.zmax = '0'
    MonND1.bins = '0'
    MonND1.min = '-1e40'
    MonND1.max = '1e40'
    MonND1.restore_neutron = '1'
    MonND1.radius = '0'
    MonND1.options = 'options1'
    MonND1.filename = '"MonND1"'
    MonND1.geometry = '"NULL"'
    MonND1.nowritefile = '0'
    MonND1.nexus_bins = '0'
    MonND1.username0 = '"NULL"'
    MonND1.username1 = '"Horizontal position / [m]"'
    MonND1.username2 = '"NULL"'
    MonND1.username3 = '"NULL"'
    MonND1.username4 = '"NULL"'
    MonND1.username5 = '"NULL"'
    MonND1.username6 = '"NULL"'
    MonND1.username7 = '"NULL"'
    MonND1.username8 = '"NULL"'
    MonND1.username9 = '"NULL"'
    
    # Comp instance CWidth, placement and parameters
    CWidth = instr.add_component('CWidth','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( Eneutron <= EmaxC && Eneutron >= EminC ) at CWidth
    CWidth.set_WHEN('( Eneutron <= EmaxC && Eneutron >= EminC )')
    
    CWidth.user0 = '""'
    CWidth.user1 = '"SrcX"'
    CWidth.user2 = '""'
    CWidth.user3 = '""'
    CWidth.user4 = '""'
    CWidth.user5 = '""'
    CWidth.user6 = '""'
    CWidth.user7 = '""'
    CWidth.user8 = '""'
    CWidth.user9 = '""'
    CWidth.xwidth = 'XW'
    CWidth.yheight = 'YH'
    CWidth.zdepth = '0'
    CWidth.xmin = '0'
    CWidth.xmax = '0'
    CWidth.ymin = '0'
    CWidth.ymax = '0'
    CWidth.zmin = '0'
    CWidth.zmax = '0'
    CWidth.bins = '0'
    CWidth.min = '-1e40'
    CWidth.max = '1e40'
    CWidth.restore_neutron = '1'
    CWidth.radius = '0'
    CWidth.options = 'options1'
    CWidth.filename = '"CWidth"'
    CWidth.geometry = '"NULL"'
    CWidth.nowritefile = '0'
    CWidth.nexus_bins = '0'
    CWidth.username0 = '"NULL"'
    CWidth.username1 = '"Horizontal position / [m]"'
    CWidth.username2 = '"NULL"'
    CWidth.username3 = '"NULL"'
    CWidth.username4 = '"NULL"'
    CWidth.username5 = '"NULL"'
    CWidth.username6 = '"NULL"'
    CWidth.username7 = '"NULL"'
    CWidth.username8 = '"NULL"'
    CWidth.username9 = '"NULL"'
    
    # Comp instance TWidth, placement and parameters
    TWidth = instr.add_component('TWidth','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( Eneutron <= EmaxTh && Eneutron >= EminTh ) at TWidth
    TWidth.set_WHEN('( Eneutron <= EmaxTh && Eneutron >= EminTh )')
    
    TWidth.user0 = '""'
    TWidth.user1 = '"SrcX"'
    TWidth.user2 = '""'
    TWidth.user3 = '""'
    TWidth.user4 = '""'
    TWidth.user5 = '""'
    TWidth.user6 = '""'
    TWidth.user7 = '""'
    TWidth.user8 = '""'
    TWidth.user9 = '""'
    TWidth.xwidth = 'XW'
    TWidth.yheight = 'YH'
    TWidth.zdepth = '0'
    TWidth.xmin = '0'
    TWidth.xmax = '0'
    TWidth.ymin = '0'
    TWidth.ymax = '0'
    TWidth.zmin = '0'
    TWidth.zmax = '0'
    TWidth.bins = '0'
    TWidth.min = '-1e40'
    TWidth.max = '1e40'
    TWidth.restore_neutron = '1'
    TWidth.radius = '0'
    TWidth.options = 'options1'
    TWidth.filename = '"TWidth"'
    TWidth.geometry = '"NULL"'
    TWidth.nowritefile = '0'
    TWidth.nexus_bins = '0'
    TWidth.username0 = '"NULL"'
    TWidth.username1 = '"Horizontal position / [m]"'
    TWidth.username2 = '"NULL"'
    TWidth.username3 = '"NULL"'
    TWidth.username4 = '"NULL"'
    TWidth.username5 = '"NULL"'
    TWidth.username6 = '"NULL"'
    TWidth.username7 = '"NULL"'
    TWidth.username8 = '"NULL"'
    TWidth.username9 = '"NULL"'
    
    # Comp instance MonND2, placement and parameters
    MonND2 = instr.add_component('MonND2','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( IsCold ) at MonND2
    MonND2.set_WHEN('( IsCold )')
    
    MonND2.user0 = '""'
    MonND2.user1 = '"SrcY"'
    MonND2.user2 = '""'
    MonND2.user3 = '""'
    MonND2.user4 = '""'
    MonND2.user5 = '""'
    MonND2.user6 = '""'
    MonND2.user7 = '""'
    MonND2.user8 = '""'
    MonND2.user9 = '""'
    MonND2.xwidth = 'XW'
    MonND2.yheight = 'YH'
    MonND2.zdepth = '0'
    MonND2.xmin = '0'
    MonND2.xmax = '0'
    MonND2.ymin = '0'
    MonND2.ymax = '0'
    MonND2.zmin = '0'
    MonND2.zmax = '0'
    MonND2.bins = '0'
    MonND2.min = '-1e40'
    MonND2.max = '1e40'
    MonND2.restore_neutron = '1'
    MonND2.radius = '0'
    MonND2.options = 'options4'
    MonND2.filename = '"MonND2"'
    MonND2.geometry = '"NULL"'
    MonND2.nowritefile = '0'
    MonND2.nexus_bins = '0'
    MonND2.username0 = '"NULL"'
    MonND2.username1 = '"Vertical position COLD / [m]"'
    MonND2.username2 = '"NULL"'
    MonND2.username3 = '"NULL"'
    MonND2.username4 = '"NULL"'
    MonND2.username5 = '"NULL"'
    MonND2.username6 = '"NULL"'
    MonND2.username7 = '"NULL"'
    MonND2.username8 = '"NULL"'
    MonND2.username9 = '"NULL"'
    
    # Comp instance MonND2_2, placement and parameters
    MonND2_2 = instr.add_component('MonND2_2','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( ! IsCold ) at MonND2_2
    MonND2_2.set_WHEN('( ! IsCold )')
    
    MonND2_2.user0 = '""'
    MonND2_2.user1 = '"SrcY"'
    MonND2_2.user2 = '""'
    MonND2_2.user3 = '""'
    MonND2_2.user4 = '""'
    MonND2_2.user5 = '""'
    MonND2_2.user6 = '""'
    MonND2_2.user7 = '""'
    MonND2_2.user8 = '""'
    MonND2_2.user9 = '""'
    MonND2_2.xwidth = 'XW'
    MonND2_2.yheight = 'YH'
    MonND2_2.zdepth = '0'
    MonND2_2.xmin = '0'
    MonND2_2.xmax = '0'
    MonND2_2.ymin = '0'
    MonND2_2.ymax = '0'
    MonND2_2.zmin = '0'
    MonND2_2.zmax = '0'
    MonND2_2.bins = '0'
    MonND2_2.min = '-1e40'
    MonND2_2.max = '1e40'
    MonND2_2.restore_neutron = '1'
    MonND2_2.radius = '0'
    MonND2_2.options = 'options4'
    MonND2_2.filename = '"MonND2_2"'
    MonND2_2.geometry = '"NULL"'
    MonND2_2.nowritefile = '0'
    MonND2_2.nexus_bins = '0'
    MonND2_2.username0 = '"NULL"'
    MonND2_2.username1 = '"Vertical position THERMAL/ [m]"'
    MonND2_2.username2 = '"NULL"'
    MonND2_2.username3 = '"NULL"'
    MonND2_2.username4 = '"NULL"'
    MonND2_2.username5 = '"NULL"'
    MonND2_2.username6 = '"NULL"'
    MonND2_2.username7 = '"NULL"'
    MonND2_2.username8 = '"NULL"'
    MonND2_2.username9 = '"NULL"'
    
    # Comp instance MonND3, placement and parameters
    MonND3 = instr.add_component('MonND3','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    MonND3.user0 = '""'
    MonND3.user1 = '"SrcX"'
    MonND3.user2 = '"SrcY"'
    MonND3.user3 = '""'
    MonND3.user4 = '""'
    MonND3.user5 = '""'
    MonND3.user6 = '""'
    MonND3.user7 = '""'
    MonND3.user8 = '""'
    MonND3.user9 = '""'
    MonND3.xwidth = 'XW'
    MonND3.yheight = 'YH'
    MonND3.zdepth = '0'
    MonND3.xmin = '0'
    MonND3.xmax = '0'
    MonND3.ymin = '0'
    MonND3.ymax = '0'
    MonND3.zmin = '0'
    MonND3.zmax = '0'
    MonND3.bins = '0'
    MonND3.min = '-1e40'
    MonND3.max = '1e40'
    MonND3.restore_neutron = '1'
    MonND3.radius = '0'
    MonND3.options = 'options2'
    MonND3.filename = '"MonND3"'
    MonND3.geometry = '"NULL"'
    MonND3.nowritefile = '0'
    MonND3.nexus_bins = '0'
    MonND3.username0 = '"NULL"'
    MonND3.username1 = '"Horizontal position / [m]"'
    MonND3.username2 = '"Vertical position / [m]"'
    MonND3.username3 = '"NULL"'
    MonND3.username4 = '"NULL"'
    MonND3.username5 = '"NULL"'
    MonND3.username6 = '"NULL"'
    MonND3.username7 = '"NULL"'
    MonND3.username8 = '"NULL"'
    MonND3.username9 = '"NULL"'
    
    # Comp instance MonND4, placement and parameters
    MonND4 = instr.add_component('MonND4','Monitor_nD', AT=['0', '0', '1'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    MonND4.user0 = '""'
    MonND4.user1 = '"SrcX"'
    MonND4.user2 = '"SrcZ"'
    MonND4.user3 = '""'
    MonND4.user4 = '""'
    MonND4.user5 = '""'
    MonND4.user6 = '""'
    MonND4.user7 = '""'
    MonND4.user8 = '""'
    MonND4.user9 = '""'
    MonND4.xwidth = 'XW'
    MonND4.yheight = 'YH'
    MonND4.zdepth = '0'
    MonND4.xmin = '0'
    MonND4.xmax = '0'
    MonND4.ymin = '0'
    MonND4.ymax = '0'
    MonND4.zmin = '0'
    MonND4.zmax = '0'
    MonND4.bins = '0'
    MonND4.min = '-1e40'
    MonND4.max = '1e40'
    MonND4.restore_neutron = '1'
    MonND4.radius = '0'
    MonND4.options = '"user1 bins=201 limits=[-0.3,0.3], user2 bins=201 limits=[-0.3,0.3]"'
    MonND4.filename = '"MonND4"'
    MonND4.geometry = '"NULL"'
    MonND4.nowritefile = '0'
    MonND4.nexus_bins = '0'
    MonND4.username0 = '"NULL"'
    MonND4.username1 = '"Emission position / [m]"'
    MonND4.username2 = '"Z-component of position / [m]"'
    MonND4.username3 = '"NULL"'
    MonND4.username4 = '"NULL"'
    MonND4.username5 = '"NULL"'
    MonND4.username6 = '"NULL"'
    MonND4.username7 = '"NULL"'
    MonND4.username8 = '"NULL"'
    MonND4.username9 = '"NULL"'
    
    # Comp instance AutoTOFL, placement and parameters
    AutoTOFL = instr.add_component('AutoTOFL','Monitor_nD', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    AutoTOFL.user0 = '""'
    AutoTOFL.user1 = '""'
    AutoTOFL.user2 = '""'
    AutoTOFL.user3 = '""'
    AutoTOFL.user4 = '""'
    AutoTOFL.user5 = '""'
    AutoTOFL.user6 = '""'
    AutoTOFL.user7 = '""'
    AutoTOFL.user8 = '""'
    AutoTOFL.user9 = '""'
    AutoTOFL.xwidth = '0.1'
    AutoTOFL.yheight = '0.1'
    AutoTOFL.zdepth = '0'
    AutoTOFL.xmin = '0'
    AutoTOFL.xmax = '0'
    AutoTOFL.ymin = '0'
    AutoTOFL.ymax = '0'
    AutoTOFL.zmin = '0'
    AutoTOFL.zmax = '0'
    AutoTOFL.bins = '0'
    AutoTOFL.min = '-1e40'
    AutoTOFL.max = '1e40'
    AutoTOFL.restore_neutron = '1'
    AutoTOFL.radius = '0'
    AutoTOFL.options = '"tof limits=[0 15e-3] bins=51, lambda limits=[0.1 20] bins=41"'
    AutoTOFL.filename = '"AutoTOFL"'
    AutoTOFL.geometry = '"NULL"'
    AutoTOFL.nowritefile = '0'
    AutoTOFL.nexus_bins = '0'
    AutoTOFL.username0 = '"NULL"'
    AutoTOFL.username1 = '"NULL"'
    AutoTOFL.username2 = '"NULL"'
    AutoTOFL.username3 = '"NULL"'
    AutoTOFL.username4 = '"NULL"'
    AutoTOFL.username5 = '"NULL"'
    AutoTOFL.username6 = '"NULL"'
    AutoTOFL.username7 = '"NULL"'
    AutoTOFL.username8 = '"NULL"'
    AutoTOFL.username9 = '"NULL"'
    
    # Comp instance BrillmonCOLD, placement and parameters
    BrillmonCOLD = instr.add_component('BrillmonCOLD','Brilliance_monitor', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( allmons && IsCold ) at BrillmonCOLD
    BrillmonCOLD.set_WHEN('( allmons && IsCold )')
    
    BrillmonCOLD.nlam = '101'
    BrillmonCOLD.nt = '101'
    BrillmonCOLD.nowritefile = '! allmons'
    BrillmonCOLD.lambda_0 = 'lambdamin'
    BrillmonCOLD.lambda_1 = 'lambdamax'
    BrillmonCOLD.restore_neutron = '1'
    BrillmonCOLD.Freq = '14'
    BrillmonCOLD.tofcuts = '0'
    BrillmonCOLD.toflambda = '1'
    BrillmonCOLD.xwidth = '0.1'
    BrillmonCOLD.yheight = '0.1'
    BrillmonCOLD.source_dist = '2'
    BrillmonCOLD.filename = '"brillCOLD"'
    BrillmonCOLD.t_0 = '-1000'
    BrillmonCOLD.t_1 = '4e4'
    BrillmonCOLD.srcarea = '( 100 * 0.072 * 100 * Yheight )'
    
    # Comp instance BrillmonCOLD_COLL, placement and parameters
    BrillmonCOLD_COLL = instr.add_component('BrillmonCOLD_COLL','Brilliance_monitor', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( fabs ( SrcY ) < Yheight / 2.5 && SrcX < ( 0.071 + delta ) && SrcX > ( 0.011 + delta ) ) at BrillmonCOLD_COLL
    BrillmonCOLD_COLL.set_WHEN('( fabs ( SrcY ) < Yheight / 2.5 && SrcX < ( 0.071 + delta ) && SrcX > ( 0.011 + delta ) )')
    
    BrillmonCOLD_COLL.nlam = '101'
    BrillmonCOLD_COLL.nt = '101'
    BrillmonCOLD_COLL.nowritefile = '0'
    BrillmonCOLD_COLL.lambda_0 = 'lambdamin'
    BrillmonCOLD_COLL.lambda_1 = 'lambdamax'
    BrillmonCOLD_COLL.restore_neutron = '1'
    BrillmonCOLD_COLL.Freq = '14'
    BrillmonCOLD_COLL.tofcuts = '0'
    BrillmonCOLD_COLL.toflambda = '1'
    BrillmonCOLD_COLL.xwidth = '0.1'
    BrillmonCOLD_COLL.yheight = '0.1'
    BrillmonCOLD_COLL.source_dist = '2'
    BrillmonCOLD_COLL.filename = '"brillCOLD_COLL"'
    BrillmonCOLD_COLL.t_0 = '0'
    BrillmonCOLD_COLL.t_1 = '4e4'
    BrillmonCOLD_COLL.srcarea = '( 100 * 0.06 * 100 * 2 * Yheight / 2.5 )'
    
    # Comp instance BrillmonTHRM, placement and parameters
    BrillmonTHRM = instr.add_component('BrillmonTHRM','Brilliance_monitor', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( allmons && ! IsCold ) at BrillmonTHRM
    BrillmonTHRM.set_WHEN('( allmons && ! IsCold )')
    
    BrillmonTHRM.nlam = '101'
    BrillmonTHRM.nt = '101'
    BrillmonTHRM.nowritefile = '! allmons'
    BrillmonTHRM.lambda_0 = 'lambdamin'
    BrillmonTHRM.lambda_1 = 'lambdamax'
    BrillmonTHRM.restore_neutron = '1'
    BrillmonTHRM.Freq = '14'
    BrillmonTHRM.tofcuts = '0'
    BrillmonTHRM.toflambda = '1'
    BrillmonTHRM.xwidth = '0.1'
    BrillmonTHRM.yheight = '0.1'
    BrillmonTHRM.source_dist = '2'
    BrillmonTHRM.filename = '"brillTHRM"'
    BrillmonTHRM.t_0 = '-1000'
    BrillmonTHRM.t_1 = '4e4'
    BrillmonTHRM.srcarea = '( 100 * 0.108 * 100 * Yheight )'
    
    # Comp instance BrillmonTHRM_COLL, placement and parameters
    BrillmonTHRM_COLL = instr.add_component('BrillmonTHRM_COLL','Brilliance_monitor', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    # WHEN ( fabs ( SrcY ) < Yheight / 2.5 && - SrcX > ( TCollmin + delta ) && - SrcX < ( TCollmax + delta ) ) at BrillmonTHRM_COLL
    BrillmonTHRM_COLL.set_WHEN('( fabs ( SrcY ) < Yheight / 2.5 && - SrcX > ( TCollmin + delta ) && - SrcX < ( TCollmax + delta ) )')
    
    BrillmonTHRM_COLL.nlam = '101'
    BrillmonTHRM_COLL.nt = '101'
    BrillmonTHRM_COLL.nowritefile = '0'
    BrillmonTHRM_COLL.lambda_0 = 'lambdamin'
    BrillmonTHRM_COLL.lambda_1 = 'lambdamax'
    BrillmonTHRM_COLL.restore_neutron = '1'
    BrillmonTHRM_COLL.Freq = '14'
    BrillmonTHRM_COLL.tofcuts = '0'
    BrillmonTHRM_COLL.toflambda = '1'
    BrillmonTHRM_COLL.xwidth = '0.1'
    BrillmonTHRM_COLL.yheight = '0.1'
    BrillmonTHRM_COLL.source_dist = '2'
    BrillmonTHRM_COLL.filename = '"brillTHRM_COLL"'
    BrillmonTHRM_COLL.t_0 = '-1000'
    BrillmonTHRM_COLL.t_1 = '4e4'
    BrillmonTHRM_COLL.srcarea = '( 100 * 0.06 * 100 * 2 * Yheight / 2.5 )'
    
    # Comp instance PSD0x, placement and parameters
    PSD0x = instr.add_component('PSD0x','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='BrillmonTHRM_COLL', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='BrillmonTHRM_COLL')
    
    PSD0x.user0 = '""'
    PSD0x.user1 = '"SrcX"'
    PSD0x.user2 = '"SrcY"'
    PSD0x.user3 = '""'
    PSD0x.user4 = '""'
    PSD0x.user5 = '""'
    PSD0x.user6 = '""'
    PSD0x.user7 = '""'
    PSD0x.user8 = '""'
    PSD0x.user9 = '""'
    PSD0x.xwidth = '0.1'
    PSD0x.yheight = '0.1'
    PSD0x.zdepth = '0'
    PSD0x.xmin = '0'
    PSD0x.xmax = '0'
    PSD0x.ymin = '0'
    PSD0x.ymax = '0'
    PSD0x.zmin = '0'
    PSD0x.zmax = '0'
    PSD0x.bins = '0'
    PSD0x.min = '-1e40'
    PSD0x.max = '1e40'
    PSD0x.restore_neutron = '1'
    PSD0x.radius = '0'
    PSD0x.options = '"user1 limits=[-0.08 0.08] bins=90, user2 limits=[-0.08 0.08] bins=90,"'
    PSD0x.filename = '"flat_x"'
    PSD0x.geometry = '"NULL"'
    PSD0x.nowritefile = '0'
    PSD0x.nexus_bins = '0'
    PSD0x.username0 = '"NULL"'
    PSD0x.username1 = '"NULL"'
    PSD0x.username2 = '"NULL"'
    PSD0x.username3 = '"NULL"'
    PSD0x.username4 = '"NULL"'
    PSD0x.username5 = '"NULL"'
    PSD0x.username6 = '"NULL"'
    PSD0x.username7 = '"NULL"'
    PSD0x.username8 = '"NULL"'
    PSD0x.username9 = '"NULL"'
    
    # Comp instance PSD1x, placement and parameters
    PSD1x = instr.add_component('PSD1x','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='PSD0x', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='PSD0x')
    # WHEN ( Eneutron < EminTh ) at PSD1x
    PSD1x.set_WHEN('( Eneutron < EminTh )')
    
    PSD1x.user0 = '""'
    PSD1x.user1 = '"SrcX"'
    PSD1x.user2 = '"SrcY"'
    PSD1x.user3 = '""'
    PSD1x.user4 = '""'
    PSD1x.user5 = '""'
    PSD1x.user6 = '""'
    PSD1x.user7 = '""'
    PSD1x.user8 = '""'
    PSD1x.user9 = '""'
    PSD1x.xwidth = '0.1'
    PSD1x.yheight = '0.1'
    PSD1x.zdepth = '0'
    PSD1x.xmin = '0'
    PSD1x.xmax = '0'
    PSD1x.ymin = '0'
    PSD1x.ymax = '0'
    PSD1x.zmin = '0'
    PSD1x.zmax = '0'
    PSD1x.bins = '0'
    PSD1x.min = '-1e40'
    PSD1x.max = '1e40'
    PSD1x.restore_neutron = '1'
    PSD1x.radius = '0'
    PSD1x.options = '"user1 limits=[-0.08 0.08] bins=90, user2 limits=[-0.08 0.08] bins=90,"'
    PSD1x.filename = '"flatC_x"'
    PSD1x.geometry = '"NULL"'
    PSD1x.nowritefile = '0'
    PSD1x.nexus_bins = '0'
    PSD1x.username0 = '"NULL"'
    PSD1x.username1 = '"NULL"'
    PSD1x.username2 = '"NULL"'
    PSD1x.username3 = '"NULL"'
    PSD1x.username4 = '"NULL"'
    PSD1x.username5 = '"NULL"'
    PSD1x.username6 = '"NULL"'
    PSD1x.username7 = '"NULL"'
    PSD1x.username8 = '"NULL"'
    PSD1x.username9 = '"NULL"'
    
    # Comp instance PSD2x, placement and parameters
    PSD2x = instr.add_component('PSD2x','Monitor_nD', AT=['0', '0', '0.001'], AT_RELATIVE='PSD1x', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='PSD1x')
    # WHEN ( Eneutron >= EminTh ) at PSD2x
    PSD2x.set_WHEN('( Eneutron >= EminTh )')
    
    PSD2x.user0 = '""'
    PSD2x.user1 = '"SrcX"'
    PSD2x.user2 = '"SrcY"'
    PSD2x.user3 = '""'
    PSD2x.user4 = '""'
    PSD2x.user5 = '""'
    PSD2x.user6 = '""'
    PSD2x.user7 = '""'
    PSD2x.user8 = '""'
    PSD2x.user9 = '""'
    PSD2x.xwidth = '0.1'
    PSD2x.yheight = '0.1'
    PSD2x.zdepth = '0'
    PSD2x.xmin = '0'
    PSD2x.xmax = '0'
    PSD2x.ymin = '0'
    PSD2x.ymax = '0'
    PSD2x.zmin = '0'
    PSD2x.zmax = '0'
    PSD2x.bins = '0'
    PSD2x.min = '-1e40'
    PSD2x.max = '1e40'
    PSD2x.restore_neutron = '1'
    PSD2x.radius = '0'
    PSD2x.options = '"user1 limits=[-0.08 0.08] bins=90, user2 limits=[-0.08 0.08] bins=90,"'
    PSD2x.filename = '"flatT_x"'
    PSD2x.geometry = '"NULL"'
    PSD2x.nowritefile = '0'
    PSD2x.nexus_bins = '0'
    PSD2x.username0 = '"NULL"'
    PSD2x.username1 = '"NULL"'
    PSD2x.username2 = '"NULL"'
    PSD2x.username3 = '"NULL"'
    PSD2x.username4 = '"NULL"'
    PSD2x.username5 = '"NULL"'
    PSD2x.username6 = '"NULL"'
    PSD2x.username7 = '"NULL"'
    PSD2x.username8 = '"NULL"'
    PSD2x.username9 = '"NULL"'
    
    # Comp instance Flux_incoming, placement and parameters
    Flux_incoming = instr.add_component('Flux_incoming','Monitor_nD', AT=['0', '0', '2'], AT_RELATIVE='Source', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Source')
    
    Flux_incoming.user0 = '""'
    Flux_incoming.user1 = '""'
    Flux_incoming.user2 = '""'
    Flux_incoming.user3 = '""'
    Flux_incoming.user4 = '""'
    Flux_incoming.user5 = '""'
    Flux_incoming.user6 = '""'
    Flux_incoming.user7 = '""'
    Flux_incoming.user8 = '""'
    Flux_incoming.user9 = '""'
    Flux_incoming.xwidth = '0.05'
    Flux_incoming.yheight = '0.1'
    Flux_incoming.zdepth = '0'
    Flux_incoming.xmin = '0'
    Flux_incoming.xmax = '0'
    Flux_incoming.ymin = '0'
    Flux_incoming.ymax = '0'
    Flux_incoming.zmin = '0'
    Flux_incoming.zmax = '0'
    Flux_incoming.bins = '100'
    Flux_incoming.min = '-1e40'
    Flux_incoming.max = '1e40'
    Flux_incoming.restore_neutron = '0'
    Flux_incoming.radius = '0'
    Flux_incoming.options = '"x, y pr cm2"'
    Flux_incoming.filename = '"Flux_incoming"'
    Flux_incoming.geometry = '"NULL"'
    Flux_incoming.nowritefile = '0'
    Flux_incoming.nexus_bins = '0'
    Flux_incoming.username0 = '"NULL"'
    Flux_incoming.username1 = '"NULL"'
    Flux_incoming.username2 = '"NULL"'
    Flux_incoming.username3 = '"NULL"'
    Flux_incoming.username4 = '"NULL"'
    Flux_incoming.username5 = '"NULL"'
    Flux_incoming.username6 = '"NULL"'
    Flux_incoming.username7 = '"NULL"'
    Flux_incoming.username8 = '"NULL"'
    Flux_incoming.username9 = '"NULL"'
    
    # Comp instance GuideStraight, placement and parameters
    GuideStraight = instr.add_component('GuideStraight','Guide', AT=['0', '0', '0'], AT_RELATIVE='Flux_incoming', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Flux_incoming')
    
    GuideStraight.reflect = '0'
    GuideStraight.w1 = '0.05'
    GuideStraight.h1 = '0.1'
    GuideStraight.w2 = '0'
    GuideStraight.h2 = '0'
    GuideStraight.l = '10'
    GuideStraight.R0 = '0.99'
    GuideStraight.Qc = '0.0219'
    GuideStraight.alpha = '6.07'
    GuideStraight.m = '2'
    GuideStraight.W = '0.003'
    
    # Comp instance Flux_mid, placement and parameters
    Flux_mid = instr.add_component('Flux_mid','Monitor_nD', AT=['0', '0', '10'], AT_RELATIVE='GuideStraight', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='GuideStraight')
    
    Flux_mid.user0 = '""'
    Flux_mid.user1 = '""'
    Flux_mid.user2 = '""'
    Flux_mid.user3 = '""'
    Flux_mid.user4 = '""'
    Flux_mid.user5 = '""'
    Flux_mid.user6 = '""'
    Flux_mid.user7 = '""'
    Flux_mid.user8 = '""'
    Flux_mid.user9 = '""'
    Flux_mid.xwidth = '0.05'
    Flux_mid.yheight = '0.1'
    Flux_mid.zdepth = '0'
    Flux_mid.xmin = '0'
    Flux_mid.xmax = '0'
    Flux_mid.ymin = '0'
    Flux_mid.ymax = '0'
    Flux_mid.zmin = '0'
    Flux_mid.zmax = '0'
    Flux_mid.bins = '100'
    Flux_mid.min = '-1e40'
    Flux_mid.max = '1e40'
    Flux_mid.restore_neutron = '0'
    Flux_mid.radius = '0'
    Flux_mid.options = '"x, y pr cm2"'
    Flux_mid.filename = '"Flux_mid"'
    Flux_mid.geometry = '"NULL"'
    Flux_mid.nowritefile = '0'
    Flux_mid.nexus_bins = '0'
    Flux_mid.username0 = '"NULL"'
    Flux_mid.username1 = '"NULL"'
    Flux_mid.username2 = '"NULL"'
    Flux_mid.username3 = '"NULL"'
    Flux_mid.username4 = '"NULL"'
    Flux_mid.username5 = '"NULL"'
    Flux_mid.username6 = '"NULL"'
    Flux_mid.username7 = '"NULL"'
    Flux_mid.username8 = '"NULL"'
    Flux_mid.username9 = '"NULL"'
    
    # Comp instance GuideR, placement and parameters
    GuideR = instr.add_component('GuideR','Guide_curved', AT=['0', '0', '0.001'], AT_RELATIVE='Flux_mid', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Flux_mid')
    
    GuideR.w1 = '0.05'
    GuideR.h1 = '0.1'
    GuideR.l = '50'
    GuideR.R0 = '0.995'
    GuideR.Qc = '0.0218'
    GuideR.alpha = '4.38'
    GuideR.m = '2'
    GuideR.W = '0.003'
    GuideR.curvature = '3000'
    
    # Comp instance RArm, placement and parameters
    RArm = instr.add_component('RArm','Arm', AT=['0.416657', '0', '50.002'], AT_RELATIVE='GuideR', ROTATED=['0', 'calcAlpha ( 50 , 3000 )', '0'], ROTATED_RELATIVE='GuideR')
    
    
    # Comp instance RArm2, placement and parameters
    RArm2 = instr.add_component('RArm2','Arm', AT=['calcX ( 50 , 3000 )', '0', 'calcZ ( 50 , 3000 )'], AT_RELATIVE='GuideR', ROTATED=['0', 'calcAlpha ( 50 , 3000 )', '0'], ROTATED_RELATIVE='GuideR')
    
    
    # Comp instance Monitor2_xy1, placement and parameters
    Monitor2_xy1 = instr.add_component('Monitor2_xy1','Monitor_nD', AT=['0', '0', '0.05'], AT_RELATIVE='RArm', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='RArm')
    
    Monitor2_xy1.user0 = '""'
    Monitor2_xy1.user1 = '""'
    Monitor2_xy1.user2 = '""'
    Monitor2_xy1.user3 = '""'
    Monitor2_xy1.user4 = '""'
    Monitor2_xy1.user5 = '""'
    Monitor2_xy1.user6 = '""'
    Monitor2_xy1.user7 = '""'
    Monitor2_xy1.user8 = '""'
    Monitor2_xy1.user9 = '""'
    Monitor2_xy1.xwidth = '0.12'
    Monitor2_xy1.yheight = '0.12'
    Monitor2_xy1.zdepth = '0'
    Monitor2_xy1.xmin = '0'
    Monitor2_xy1.xmax = '0'
    Monitor2_xy1.ymin = '0'
    Monitor2_xy1.ymax = '0'
    Monitor2_xy1.zmin = '0'
    Monitor2_xy1.zmax = '0'
    Monitor2_xy1.bins = '0'
    Monitor2_xy1.min = '-1e40'
    Monitor2_xy1.max = '1e40'
    Monitor2_xy1.restore_neutron = '0'
    Monitor2_xy1.radius = '0'
    Monitor2_xy1.options = '"x limits=[-0.06 0.06] bins=51, y limits=[-0.06 0.06] bins=51,"'
    Monitor2_xy1.filename = '"Monitor2_xy1"'
    Monitor2_xy1.geometry = '"NULL"'
    Monitor2_xy1.nowritefile = '0'
    Monitor2_xy1.nexus_bins = '0'
    Monitor2_xy1.username0 = '"NULL"'
    Monitor2_xy1.username1 = '"NULL"'
    Monitor2_xy1.username2 = '"NULL"'
    Monitor2_xy1.username3 = '"NULL"'
    Monitor2_xy1.username4 = '"NULL"'
    Monitor2_xy1.username5 = '"NULL"'
    Monitor2_xy1.username6 = '"NULL"'
    Monitor2_xy1.username7 = '"NULL"'
    Monitor2_xy1.username8 = '"NULL"'
    Monitor2_xy1.username9 = '"NULL"'
    
    # Comp instance Monitor_X, placement and parameters
    Monitor_X = instr.add_component('Monitor_X','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Monitor_X.user0 = '""'
    Monitor_X.user1 = '""'
    Monitor_X.user2 = '""'
    Monitor_X.user3 = '""'
    Monitor_X.user4 = '""'
    Monitor_X.user5 = '""'
    Monitor_X.user6 = '""'
    Monitor_X.user7 = '""'
    Monitor_X.user8 = '""'
    Monitor_X.user9 = '""'
    Monitor_X.xwidth = '0.12'
    Monitor_X.yheight = '0.12'
    Monitor_X.zdepth = '0'
    Monitor_X.xmin = '0'
    Monitor_X.xmax = '0'
    Monitor_X.ymin = '0'
    Monitor_X.ymax = '0'
    Monitor_X.zmin = '0'
    Monitor_X.zmax = '0'
    Monitor_X.bins = '0'
    Monitor_X.min = '-1e40'
    Monitor_X.max = '1e40'
    Monitor_X.restore_neutron = '0'
    Monitor_X.radius = '0'
    Monitor_X.options = '"x limits=[-0.06 0.06] bins=51"'
    Monitor_X.filename = '"Monitor_X"'
    Monitor_X.geometry = '"NULL"'
    Monitor_X.nowritefile = '0'
    Monitor_X.nexus_bins = '0'
    Monitor_X.username0 = '"NULL"'
    Monitor_X.username1 = '"NULL"'
    Monitor_X.username2 = '"NULL"'
    Monitor_X.username3 = '"NULL"'
    Monitor_X.username4 = '"NULL"'
    Monitor_X.username5 = '"NULL"'
    Monitor_X.username6 = '"NULL"'
    Monitor_X.username7 = '"NULL"'
    Monitor_X.username8 = '"NULL"'
    Monitor_X.username9 = '"NULL"'
    
    # Comp instance Monitor_Y, placement and parameters
    Monitor_Y = instr.add_component('Monitor_Y','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Monitor_Y.user0 = '""'
    Monitor_Y.user1 = '""'
    Monitor_Y.user2 = '""'
    Monitor_Y.user3 = '""'
    Monitor_Y.user4 = '""'
    Monitor_Y.user5 = '""'
    Monitor_Y.user6 = '""'
    Monitor_Y.user7 = '""'
    Monitor_Y.user8 = '""'
    Monitor_Y.user9 = '""'
    Monitor_Y.xwidth = '0.12'
    Monitor_Y.yheight = '0.12'
    Monitor_Y.zdepth = '0'
    Monitor_Y.xmin = '0'
    Monitor_Y.xmax = '0'
    Monitor_Y.ymin = '0'
    Monitor_Y.ymax = '0'
    Monitor_Y.zmin = '0'
    Monitor_Y.zmax = '0'
    Monitor_Y.bins = '0'
    Monitor_Y.min = '-1e40'
    Monitor_Y.max = '1e40'
    Monitor_Y.restore_neutron = '0'
    Monitor_Y.radius = '0'
    Monitor_Y.options = '"y limits=[-0.06 0.06] bins=51"'
    Monitor_Y.filename = '"Monitor_Y"'
    Monitor_Y.geometry = '"NULL"'
    Monitor_Y.nowritefile = '0'
    Monitor_Y.nexus_bins = '0'
    Monitor_Y.username0 = '"NULL"'
    Monitor_Y.username1 = '"NULL"'
    Monitor_Y.username2 = '"NULL"'
    Monitor_Y.username3 = '"NULL"'
    Monitor_Y.username4 = '"NULL"'
    Monitor_Y.username5 = '"NULL"'
    Monitor_Y.username6 = '"NULL"'
    Monitor_Y.username7 = '"NULL"'
    Monitor_Y.username8 = '"NULL"'
    Monitor_Y.username9 = '"NULL"'
    
    # Comp instance Monitor_divH, placement and parameters
    Monitor_divH = instr.add_component('Monitor_divH','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Monitor_divH.user0 = '""'
    Monitor_divH.user1 = '""'
    Monitor_divH.user2 = '""'
    Monitor_divH.user3 = '""'
    Monitor_divH.user4 = '""'
    Monitor_divH.user5 = '""'
    Monitor_divH.user6 = '""'
    Monitor_divH.user7 = '""'
    Monitor_divH.user8 = '""'
    Monitor_divH.user9 = '""'
    Monitor_divH.xwidth = '0.12'
    Monitor_divH.yheight = '0.12'
    Monitor_divH.zdepth = '0'
    Monitor_divH.xmin = '0'
    Monitor_divH.xmax = '0'
    Monitor_divH.ymin = '0'
    Monitor_divH.ymax = '0'
    Monitor_divH.zmin = '0'
    Monitor_divH.zmax = '0'
    Monitor_divH.bins = '0'
    Monitor_divH.min = '-1e40'
    Monitor_divH.max = '1e40'
    Monitor_divH.restore_neutron = '0'
    Monitor_divH.radius = '0'
    Monitor_divH.options = '"hdiv limits=[-1.5 1.5] bins=51"'
    Monitor_divH.filename = '"Monitor_divH"'
    Monitor_divH.geometry = '"NULL"'
    Monitor_divH.nowritefile = '0'
    Monitor_divH.nexus_bins = '0'
    Monitor_divH.username0 = '"NULL"'
    Monitor_divH.username1 = '"NULL"'
    Monitor_divH.username2 = '"NULL"'
    Monitor_divH.username3 = '"NULL"'
    Monitor_divH.username4 = '"NULL"'
    Monitor_divH.username5 = '"NULL"'
    Monitor_divH.username6 = '"NULL"'
    Monitor_divH.username7 = '"NULL"'
    Monitor_divH.username8 = '"NULL"'
    Monitor_divH.username9 = '"NULL"'
    
    # Comp instance Monitor_divV, placement and parameters
    Monitor_divV = instr.add_component('Monitor_divV','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Monitor_divV.user0 = '""'
    Monitor_divV.user1 = '""'
    Monitor_divV.user2 = '""'
    Monitor_divV.user3 = '""'
    Monitor_divV.user4 = '""'
    Monitor_divV.user5 = '""'
    Monitor_divV.user6 = '""'
    Monitor_divV.user7 = '""'
    Monitor_divV.user8 = '""'
    Monitor_divV.user9 = '""'
    Monitor_divV.xwidth = '0.12'
    Monitor_divV.yheight = '0.12'
    Monitor_divV.zdepth = '0'
    Monitor_divV.xmin = '0'
    Monitor_divV.xmax = '0'
    Monitor_divV.ymin = '0'
    Monitor_divV.ymax = '0'
    Monitor_divV.zmin = '0'
    Monitor_divV.zmax = '0'
    Monitor_divV.bins = '0'
    Monitor_divV.min = '-1e40'
    Monitor_divV.max = '1e40'
    Monitor_divV.restore_neutron = '0'
    Monitor_divV.radius = '0'
    Monitor_divV.options = '"vdiv limits=[-1.5 1.5] bins=51"'
    Monitor_divV.filename = '"Monitor_divV"'
    Monitor_divV.geometry = '"NULL"'
    Monitor_divV.nowritefile = '0'
    Monitor_divV.nexus_bins = '0'
    Monitor_divV.username0 = '"NULL"'
    Monitor_divV.username1 = '"NULL"'
    Monitor_divV.username2 = '"NULL"'
    Monitor_divV.username3 = '"NULL"'
    Monitor_divV.username4 = '"NULL"'
    Monitor_divV.username5 = '"NULL"'
    Monitor_divV.username6 = '"NULL"'
    Monitor_divV.username7 = '"NULL"'
    Monitor_divV.username8 = '"NULL"'
    Monitor_divV.username9 = '"NULL"'
    
    # Comp instance Monitor_t, placement and parameters
    Monitor_t = instr.add_component('Monitor_t','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Monitor_t.user0 = '""'
    Monitor_t.user1 = '""'
    Monitor_t.user2 = '""'
    Monitor_t.user3 = '""'
    Monitor_t.user4 = '""'
    Monitor_t.user5 = '""'
    Monitor_t.user6 = '""'
    Monitor_t.user7 = '""'
    Monitor_t.user8 = '""'
    Monitor_t.user9 = '""'
    Monitor_t.xwidth = '0.12'
    Monitor_t.yheight = '0.12'
    Monitor_t.zdepth = '0'
    Monitor_t.xmin = '0'
    Monitor_t.xmax = '0'
    Monitor_t.ymin = '0'
    Monitor_t.ymax = '0'
    Monitor_t.zmin = '0'
    Monitor_t.zmax = '0'
    Monitor_t.bins = '0'
    Monitor_t.min = '-1e40'
    Monitor_t.max = '1e40'
    Monitor_t.restore_neutron = '0'
    Monitor_t.radius = '0'
    Monitor_t.options = '"t limits=[0 350e-3] bins=351"'
    Monitor_t.filename = '"Monitor_t"'
    Monitor_t.geometry = '"NULL"'
    Monitor_t.nowritefile = '0'
    Monitor_t.nexus_bins = '0'
    Monitor_t.username0 = '"NULL"'
    Monitor_t.username1 = '"NULL"'
    Monitor_t.username2 = '"NULL"'
    Monitor_t.username3 = '"NULL"'
    Monitor_t.username4 = '"NULL"'
    Monitor_t.username5 = '"NULL"'
    Monitor_t.username6 = '"NULL"'
    Monitor_t.username7 = '"NULL"'
    Monitor_t.username8 = '"NULL"'
    Monitor_t.username9 = '"NULL"'
    
    # Comp instance Flux_end, placement and parameters
    Flux_end = instr.add_component('Flux_end','Monitor_nD', AT=['0', '0', '0'], AT_RELATIVE='Monitor2_xy1', ROTATED=['0.0', '0.0', '0.0'], ROTATED_RELATIVE='Monitor2_xy1')
    
    Flux_end.user0 = '""'
    Flux_end.user1 = '""'
    Flux_end.user2 = '""'
    Flux_end.user3 = '""'
    Flux_end.user4 = '""'
    Flux_end.user5 = '""'
    Flux_end.user6 = '""'
    Flux_end.user7 = '""'
    Flux_end.user8 = '""'
    Flux_end.user9 = '""'
    Flux_end.xwidth = '0.05'
    Flux_end.yheight = '0.1'
    Flux_end.zdepth = '0'
    Flux_end.xmin = '0'
    Flux_end.xmax = '0'
    Flux_end.ymin = '0'
    Flux_end.ymax = '0'
    Flux_end.zmin = '0'
    Flux_end.zmax = '0'
    Flux_end.bins = '100'
    Flux_end.min = '-1e40'
    Flux_end.max = '1e40'
    Flux_end.restore_neutron = '0'
    Flux_end.radius = '0'
    Flux_end.options = '"x, y pr cm2"'
    Flux_end.filename = '"Flux_end"'
    Flux_end.geometry = '"NULL"'
    Flux_end.nowritefile = '0'
    Flux_end.nexus_bins = '0'
    Flux_end.username0 = '"NULL"'
    Flux_end.username1 = '"NULL"'
    Flux_end.username2 = '"NULL"'
    Flux_end.username3 = '"NULL"'
    Flux_end.username4 = '"NULL"'
    Flux_end.username5 = '"NULL"'
    Flux_end.username6 = '"NULL"'
    Flux_end.username7 = '"NULL"'
    Flux_end.username8 = '"NULL"'
    Flux_end.username9 = '"NULL"'
    
    # Comp instance DummyArm1, placement and parameters
    DummyArm1 = instr.add_component('DummyArm1','Arm', AT=['6', '0', '6'])
    
    
    # Comp instance DummyArm2, placement and parameters
    DummyArm2 = instr.add_component('DummyArm2','Arm', AT=['-6', '0', '6'])
    
    
    # Comp instance DummyArm3, placement and parameters
    DummyArm3 = instr.add_component('DummyArm3','Arm', AT=['-6', '0', '-6'])
    
    
    # Comp instance DummyArm4, placement and parameters
    DummyArm4 = instr.add_component('DummyArm4','Arm', AT=['6', '0', '-6'])
    
    
    # Comp instance DummyArm5, placement and parameters
    DummyArm5 = instr.add_component('DummyArm5','Arm', AT=['6', '0', '6'])
    
    
    # Tests corresponding to the %Example lines of the instrument. The
    # parameter values are restored afterwards, since add_test uses the
    # current parameter values:
    _parameter_values = {p: instr.parameters[p].value for p in instr.get_parameter_names()}
    instr.set_parameters({'sector': 'S', 'beamline': 2, 'cold': 0.5})
    instr.add_test('Monitor2_xy1', intensity=1.59e+11, included_pars=['sector', 'beamline', 'cold'])
    instr.set_parameters(_parameter_values)

    # Instruct McStasscript not to 'check everythng'
    instr.settings(checks=False)
    return instr


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagram', action='store_true', help='Show diagram (default False)')
    parser.add_argument('--display', action='store_true', help='Run a visualisation (default False)')
    parser.add_argument('--run', action='store_true', help='Run a simulation (default False. Default implies creation of bare .instr.)')
    parser.add_argument('--plot', action='store_true', help='Run plotter (default False and always off without --run)')
    args = parser.parse_args()

    # Always generate instr object
    instr=make()
    # Use instr.settings() to add e.g. seed=1000, ncount=1e7, mpi=8, openacc=True, force_compile=False etc.)

    # Show diagram
    if args.diagram:
        instr.show_diagram()

    # Visualise with default parameters (defaults to 'webgl-legacy' visualisation)
    if args.display:
        instr.show_instrument()

    # Generate a dataset with default parameters.
    if args.run:
        data = instr.backengine()
    else:
        instr.write_full_instrument()

    # Overview plot:
    if args.plot and args.run:
        ms.make_sub_plot(data)

    # Other useful commands follow...
    # One plot pr. window
    #ms.make_plot(data)

    # Load another dataset
    #data2 = ms.load_data('some_other_folder')

    # Adjusting a specific plot
    #ms.name_plot_options("PSD_4PI", data, log=1, colormap="hot", orders_of_mag=5)

    # Bring up the 'interface' - only relevant in Jupyter
    #%matplotlib widget
    #import mcstasscript.jb_interface as ms_widget
    #ms_widget.show(data)

    # Bring up the simulation 'interface' - only relevant in Jupyter
    #%matplotlib widget
    #import mcstasscript.jb_interface as ms_widget
    #sim_widget = ms_widget.SimInterface(instr)
    #sim_widget.show_interface()

    # Acessing data from the interface
    #data = sim_widget.get_data()


# end of generated Python code ESS02_modeSomeMode.py
