#!/usr/bin/env python3

import sys, os
os.environ['GST_PLUGIN_PATH'] = '../build'

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

import json, pprint, pdb, urllib.request, dateutil.parser

GObject.threads_init()
Gst.init()

mainloop = GObject.MainLoop()
pipeline = Gst.parse_launch("appsrc name=indat emit-signals=true ! \
                             decodebin ! \
                             video/x-raw ! \
                             appsink name=outdat emit-signals=true")

indat = pipeline.get_by_name('indat')
outdat = pipeline.get_by_name('outdat')

infile = urllib.request.urlopen("https://www.quirksmode.org/html5/videos/big_buck_bunny.webm")
infile_ts = infile.info()['Last-Modified']
infile_ts = dateutil.parser.parse(infile_ts).timestamp() * Gst.SECOND

def get_more_data(src, size=16384):
    d = infile.read(size)
    d = Gst.Buffer.new_wrapped(d)
    d.dts = infile_ts
    src.emit('push-buffer', d)
    
indat.connect('need-data', get_more_data)

def display_dat(snk):
    #pdb.set_trace()
    d = snk.emit('pull-sample')
    if type(d) == Gst.Sample:
        d = d.get_buffer()
    di = d.map(Gst.MapFlags.READ)
    pprint.pprint({'dts':d.dts, 'pts':d.dts, 'duration':d.duration})
    return Gst.FlowReturn.OK

outdat.connect('new-sample', display_dat)

pipeline.set_state(Gst.State.PLAYING)
mainloop.run()
