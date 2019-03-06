# -*- coding: utf-8 -*-
"""Generate samples with Gstreamer 'appsrc' element in 'push' mode"""

# source is https://gist.github.com/thomasfillon/a63553d85f010bc75b86

# equivalent effect:
# gst-launch-1.0 filesrc location=bird-calls.wav ! wavparse \
# ! audioconvert ! audioresample ! alsasink

# gst-launch-1.0 filesrc location=file.pcm ! audio/x-raw,format=S16BE,channels=2,rate=48000 \
# ! audioconvert ! audioresample ! autoaudiosink
import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('Gtk', "3.0")
from gi.repository import GObject, GLib, Gst

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


class Appsrc():
    # pipeline = Gst.Pipeline.new("pipeline")
    PIPELINE_SIMPLE = "appsrc name=appsrc do-timestamp=true ! audio/x-raw,format=S16BE,channels=2,rate=48000 ! audioconvert ! audioresample ! autoaudiosink"

    def __init__(self):
        self.pipeline = Gst.parse_launch(self.PIPELINE_SIMPLE)

        self.buffer_size = 4096
        self.num_buffer = 10
        self.array = ((2**28-1)*numpy.random.randn(self.num_buffer
                                                   * self.buffer_size, 1)).astype('<i4')
        self.needs_update = None
        self.the_buf = 0

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self._on_eos_cb)
        bus.connect("message::error", self._on_error_cb)

        # appsrc = Gst.ElementFactory.make('appsrc', 'appsrc')
        self.appsrc = self.pipeline.get_by_name("appsrc")
        self.appsrc.connect('need-data', self._on_need_buffer)

        self.buffer = None
        self.buffer = Gst.Buffer.new_allocate(None, self.buffer_size * 4, None)
        self.needs_update = True
        self.time = 0

    def start(self):
        """ zut """
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        """ flute """
        self.pipeline.set_state(Gst.State.PAUSED)

    def _on_need_buffer(self, source, arg0):
        """ Fichtre """
        if self.needs_update:
            self.needs_update = self.the_buf < self.num_buffer
            print('push %d/%d' % (self.the_buf, self.num_buffer))
            toto = self.array[self.the_buf*self.buffer_size:(self.the_buf+1)*self.buffer_size]
            self.buffer.fill(0, toto.tobytes())
            source.emit("push-buffer", self.buffer)
            self.the_buf += 1

    def _on_eos_cb(self, bus, msg):
        """Calback on End-Of-Stream message"""
        # mainloop.quit()
        self.pipeline.set_state(Gst.State.NULL)

    def _on_error_cb(self, bus, msg):
        """Calback on Error message"""
        err, debug_info = msg.parse_error()
        print("Error received from element %s: %s" % (msg.src.get_name(),
                                                      err))
        print("Debugging information: %s" % debug_info)
        # mainloop.quit()

if __name__ == "__main__":
    Gst.init(sys.argv)
    GObject.threads_init()
    appsrc = Appsrc()

    loop = GObject.MainLoop()
    appsrc.start()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
    appsrc.stop()
