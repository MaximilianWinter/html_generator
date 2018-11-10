#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 15:21:26 2018

@author: maximilian winter
"""

import numpy as np
import time
from threading import Thread
from traits.api import HasTraits, Float, Enum, Array, Instance, Int, String, Bool, Button, List, Tuple, Dict, Directory, HTML
from traitsui.api import Handler, Tabbed, View, Item, VGroup, HGroup, CodeEditor, HTMLEditor, RangeEditor, ButtonEditor, ListStrEditor, InstanceEditor
from chaco.api import GridContainer,ArrayPlotData, ArrayDataSource, add_default_grids, PlotAxis, Legend, OverlayPlotContainer, LinearMapper, Plot, jet,LinePlot, DataRange1D
from chaco.tools.api import LineSegmentTool, PanTool, ZoomTool, BroadcasterTool, LegendTool, LegendHighlighter
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from enable.api import ComponentEditor, Component

import os
from scipy import ndimage, misc
from ftplib import FTP_TLS
import sys
import traceback

class UploadThread(Thread):
    def run(self):
        self.master.status = "establishing connection to server..."
        try:
            ftps = FTP_TLS(self.master.ftp_url,self.master.ftp_user,self.master.ftp_pw)
            ftps.cwd(self.master.ftp_dir)
            picnames = np.array(ftps.nlst())[2:]
            picnumbers = map(int,[name[0:-4] for name in picnames])
            maxnumber = max(picnumbers)
            self.master.status = "connection successful"
        except:
            traceback.print_exc()
            self.master.status = "could not establish connection"
            self.master.notuploading = True

        html_pics = ''
        pic_1 = '''<div class="responsive">
              <div class="gallery">
                      <img src="/pictures/'''
        pic_2 = '''.jpg" width="600" height="400">
                    <div class="desc"></div>
              </div>
            </div>'''
        
        

        picnumber = maxnumber + 1
        if not os.path.exists(self.master.dirpath+'/smallpics'):
            os.makedirs(self.master.dirpath+'/smallpics')

        for filename in os.listdir(self.master.dirpath):
            #print filename
            #os.rename(os.dirpath.join(dirpath,filename), os.dirpath.join(dirpath,str(picnumber)+'.jpg'))
            if filename[-4:] != ".jpg" and filename[-4:] != ".png":
                continue
            picpath = self.master.dirpath + '/' + filename#+ str(picnumber) + '.jpg'
            pic = ndimage.imread(picpath)
            fac = 1328./max(pic.shape)
            smallpic = misc.imresize(pic,fac)
            newpath = self.master.dirpath + '/smallpics/' + str(picnumber) + '.jpg'
            misc.imsave(newpath, smallpic)
    
            html_pics = html_pics + pic_1 + str(picnumber) + pic_2
    
            #upload pic
            self.master.status = "uploading picture " + newpath
            fopen = open(newpath,'r')
            storcommand = "STOR " + str(picnumber) + '.jpg'
            ftps.storbinary(storcommand, fopen)
            fopen.close()
    
            picnumber = picnumber + 1
            
        html_intro = self.master.html_intro_1 + self.master.category + self.master.html_intro_2
        full_html = html_intro + self.master.html_text + html_pics + self.master.html_end
        html_name = self.master.title + ".php"
        html_path = self.master.codedir + '/' + self.master.date + "_" + html_name
        fopen = open(html_path, "w")
        fopen.write(full_html)
        fopen.close()

        #upload
        try:
            self.master.status = "uploading html " + html_path
            fopen = open(html_path,'r')
            storcommand = "STOR " + self.master.date + '_' + html_name
            ftps.cwd('..')
            ftps.storbinary(storcommand, fopen)
            fopen.close()
            ftps.quit()
            self.master.status = "uploading succesful"
            self.master.notuploading = True
        except:
            traceback.print_exc()
            self.master.notuploading = True


class MainWindow(HasTraits):
    title = String()
    date = String()
    category = Enum(['nus','travel','pics','food'])
    dirpath = Directory()
    codedir = Directory()
    html_text = String('')
    
    status = String('no connection')
    ftp_url = String('files.000webhost.com')
    ftp_user = String('maxinsingapore')
    ftp_dir = String('public_html/pictures')
    ftp_pw = String()
    
    upload_btn = Button('Upload')
    html_preview = HTML()
    preview_btn = Button('HTML preview')
    
    uploadthread = Instance(UploadThread)
    notuploading = Bool(True)
    
    html_intro_1 = '''<!DOCTYPE html><html><head><link href="main.css" rel="stylesheet"/>
        <title>Max in Singapore</title>
        
    </head>
    <body>
        
        <?php require("ground.php"); ?>
        
        <div class = "title">
            <a href="'''
            
    html_intro_2 = '''.php"><figure><p>back</p</figure></a>
        </div>
        <div class="center">'''
    

        
    html_end = '''              </div>
            </div>

            
                    </div>
        
                    </body>
            </html>'''
    
    traits_view = View(HGroup('ftp_url','ftp_user','ftp_pw','ftp_dir'),
                       HGroup('title','date','category'),
                       HGroup(Item('html_text',editor=CodeEditor()),Item('html_preview',editor=HTMLEditor())),
                       'preview_btn',
                       Item('dirpath',label='Photo Directory'),
                       Item('codedir',label='Code Directory'), Item('status',style='readonly'),
                       Item('upload_btn',enabled_when='notuploading'))
    
    def _preview_btn_fired(self):
        html_intro = self.html_intro_1 + self.category + self.html_intro_2
        self.html_preview = html_intro + self.html_text + self.html_end
        
    def _upload_btn_fired(self):
        if self.dirpath != '' and self.codedir !='':
            self.notuploading = False
            self.uploadthread = UploadThread()
            self.uploadthread.wants_abort=False
            self.uploadthread.master=self
            self.uploadthread.start()
        else:
            self.status = "choose directories"


if __name__== '__main__':
    s=MainWindow()
    s.configure_traits()
