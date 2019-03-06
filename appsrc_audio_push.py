# -*- coding: utf-8 -*-
"""Generate samples with Gstreamer 'appsrc' element in 'push' mode"""

# source is https://gist.github.com/thomasfillon/a63553d85f010bc75b86

# equivalent effect:
# gst-launch-1.0 filesrc location=bird-calls.wav ! wavparse \  
# ! audioconvert ! audioresample ! alsasink

import gi

gi.require_version('Gst', '1.0')
gi.require_version('Gtk', "3.0")
from gi.repository import GLib, GObject, Gst, Gtk

import numpy
import threading


# Initialize gobject in a threading environment
# GObject.threads_init()
Gst.init(None)

# GStreamer main loop
# mainloop = GLib.MainLoop()

# Threading is needed to "push" buffer outside the gstreamer mainloop
mainloop_thread = threading.Thread()
mainloop = GLib.MainLoop()
mainloop_thread.mainloop = mainloop
mainloop_thread.run = mainloop_thread.mainloop.run

pipeline = Gst.Pipeline.new("pipeline")

buffer_size = 4096
num_buffer = 10
array = ((2**28-1)*numpy.random.randn(num_buffer * buffer_size, 1)).astype('<i4')
appsrc = Gst.ElementFactory.make('appsrc', 'appsrc')

capstr = """audio/x-raw-float,
            width=32,
            depth=32,
            endianness=1234,
            rate=16000,
            channels=1"""
capstr = """audio/x-raw,
        format=(string)S32LE,
        channels = (int)1,
        rate = (int)16000"""
caps = Gst.caps_from_string(capstr)
print(caps)
appsrc.set_property("caps", caps)
appsrc.set_property("emit-signals", True)

converter = Gst.ElementFactory.make('audioconvert', 'converter')
encoder = Gst.ElementFactory.make('lame', 'encoder')

filesink = Gst.ElementFactory.make('filesink', 'sink')
filesink.set_property('location', '/tmp/test.mp3')
audiosink = Gst.ElementFactory.make('autoaudiosink', 'audiosink')

# pipeline.add(appsrc, converter, encoder, filesink)
# Gst.element_link_many(appsrc, converter, encoder, filesink)
pipeline.add(appsrc)
pipeline.add(audiosink)
appsrc.link(audiosink)


def on_eos_cb(bus, msg):
    """Calback on End-Of-Stream message"""
    mainloop.quit()
    pipeline.set_state(Gst.State.NULL)


def on_error_cb(bus, msg):
    """Calback on Error message"""
    err, debug_info = msg.parse_error()
    print ("Error received from element %s: %s" % (msg.src.get_name(),
                                                   err))
    print ("Debugging information: %s" % debug_info)
    mainloop.quit()

pipeline.set_state(Gst.State.PLAYING)

bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect('message::eos', on_eos_cb)
bus.connect("message::error", on_error_cb)

mainloop_thread.start()

for k in range(1, num_buffer+1):
    print('push %d/%d' % (k, num_buffer))
    # buf = Gst.Buffer(array[k*buffer_size:(k+1)*buffer_size])
    # toto = array[k*buffer_size:(k+1)*buffer_size].view('uint8')
    toto = array[k*buffer_size:(k+1)*buffer_size].tobytes()
    # print('pushing {0} elems'.format(len(toto)))
    buf = Gst.Buffer.new_allocate(None, buffer_size, None)
    buf.fill(0, toto)
    samples =  Gst.Sample.new(buf, caps, None, None)
    # buf = Gst.Buffer.new_wrapped(array[k*buffer_size:(k+1)*buffer_size].view("uint8"))
    appsrc.emit("push-sample", samples)
