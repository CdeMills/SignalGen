from PIL import Image as PILImage
from random import randint
import time
import gi
import io
from io import BytesIO

gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('Gtk', '3.0')

# noinspection PyUnresolvedReferences
from gi.repository import GObject, Gst, Gtk

GObject.threads_init()
Gst.init(None)


class SenderImages:
	def __init__(self):
		# Control if it is allowed push buffer in queue using "need-data" and "enough-data" signals
		self.is_push_buffer_allowed = None

		self._mainloop = GObject.MainLoop()
		auto_video_sink_pipeline = "appsrc name=source ! image/jpeg,framerate=(fraction)30/1  ! decodebin ! videoscale ! capsfilter caps=video/x-raw,width=1280,height=720,pixel-aspect-ratio=(fraction)1/1  ! queue ! autovideosink"
		self._pipeline = Gst.parse_launch(auto_video_sink_pipeline)

		self._src = self._pipeline.get_by_name('source')
		self._src.connect('need-data', self.start_feed)
		self._src.connect('enough-data', self.stop_feed)

		self._src.set_property('format', 'time')
		self._src.set_property('do-timestamp', True)

	def start_feed(self, src, length):
		print('======================> need data length: %s' % length)
		self.is_push_buffer_allowed = True

	def stop_feed(self, src):
		print('======================> enough_data')
		self.is_push_buffer_allowed = False

	def play(self):
		self._pipeline.set_state(Gst.State.PLAYING)

	def stop(self):
		self._pipeline.set_state(Gst.State.NULL)

	def run(self):
		""" Run - blocking. """
		self._mainloop.run()

	def push(self):
		""" Push a buffer into the source. """
		if self.is_push_buffer_allowed:
			image_number = randint(1, 4)
			filename = 'images/%s.jpg' % image_number
			# open file in binary read mode
			handle = open(filename, "rb");
			data = handle.read()
			handle.close()
			# Allocate GstBuffer
			buf = Gst.Buffer.new_allocate(None, len(data), None)
			buf.fill(0, data)
			# Create GstSample
			sample = Gst.Sample.new(buf, Gst.caps_from_string("image/jpeg,framerate=(fraction)30/1"), None, None)
			# Push Sample on appsrc
			gst_flow_return = self._src.emit('push-sample', sample)

			if gst_flow_return != Gst.FlowReturn.OK:
				print('We got some error, stop sending data')

		else:
			print('It is enough data for buffer....')


sender = SenderImages()
sender.play()

index = 0
while index < 1000:
	print('========================= Showing picture...')
	time.sleep(1)
	sender.push()
	
index += 1
