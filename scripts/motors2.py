#!/usr/bin/env python
#encoding: utf8
import sys,rospy,math
from pimouse_ros.msg import MotorFreqs
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger, TriggerResponse

class Motor():
	def __init__(self):
		if not self.set_power(False): sys.exit(1)

		rospy.on_shutdown(self.set_power)
		self.sub_raw = rospy.Subscriber('motor_raw',MotorFreqs,self.callback_raw_freq)
		self.sub_cmd_vel = rospy.Subscriber('cmd_vel',Twist,self.callback_cmd_vel)
		self.srv_on =rospy.Service('motor_on',Trigger, self.callback_on)
		self.srv_off = rospy.Service('motor_off',Trigger,self.callback_off)
		self.last_time =rospy.Time.now()
		self.using_cmd_vel = False

	def onoff_response(self,onoff):
		d = TriggerResponse()
		d.success = self.set_power(onoff)
		d.message = "ON" if self.is_on else "off"
		return d

	def callback_on(self,message): return self.onoff_response(True)
	def callback_off(self,message): return self.onoff_response(False)
	def set_power(self,onoff=False):
		en= "/dev/rtmotoren0"
		try:
			with open(en,'w') as f:
				f.write("1\n" if onoff else "0\n")
			self.is_on = onoff
			return True
		except:
			rospy.logger("cannot write to " +en)

		return False

	def set_raw_freq(self,left_hz,right_hz):
		if not self.is_on:
			rospy.logger("not enpowerd")
			return

		try:
			with open("/dev/rtmotor_raw_l0",'w') as lf,\
			     open("/dev/rtmotor_raw_r0",'w') as rf:
				lf.write(str(int(rount(left_hz)))+"\n")
				rf.write(str(int(rount(right_hz)))+"\n")
		except: rospy.logger("cannot write to rtmotor_aw_*")
	
	def callback_raw_freq(self,message):
		self.set_raw_freq(message.left_hZ,message.right_hz)

	def callback_cmd_vel(self,message):
		forward_hz = 80000.0*message.linear.x/(9*math.pi)
		rot_hz = 400.0*message.angular.z/math.pi
		self.set_raw_freq(forward_hz-rot_hz,forward_hz+rot_hz)
		self.using_cmd_vell =true
		self.last_time= rospy.Time.now()

if __name__ == '__main__':
	rospy.init_node('motors')
	m = Motor()

	rate = rospy.Rate(10)
	while not rospy.is_shutdown():
		if m.using_cmd_vel and rospy.Time.now().to_sec() - m.last_time.to_sec() >= 1.0:
			m.set_raw_freq(0,0)
			m.using_cmd_vel = False
		rate.sleep()
