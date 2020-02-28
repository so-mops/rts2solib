#!/usr/bin/python


import sys
from Tkinter import *
from astro.angles import *
from telescope import telescope, telComError;
from scottSock import scottSock
import time

buttonStyle = { "font":("Helvetica", 70, "bold")}
startButtonStyle = { "font":("Helvetica", 20, "bold")}
startEndStyle = { "font":("Helvetica", 70, "bold")}


class tcs_device(object):
	
	def request( self, rqstr ):
		conn = scottSock(self.ip, self.port, timeout=0.01)
		resp = conn.converse("{} {} 123 REQUEST {}\n".format(self.obsid, self.sysid, rqstr))
		if '123' in resp:
			return resp.split('123')[-1].strip()

		else:
			return resp

	def command(self, cmdstr ):	
		conn = scottSock(self.ip, self.port, timeout=0.01)
		resp = conn.converse("{} {} 123 COMMAND {}\n".format(self.obsid, self.sysid, cmdstr))
		if '123' in resp:
			return resp.split('123')[-1].strip()
		else:
			return resp


class mirror_cover(tcs_device):
	ip = "10.30.3.70"
	port = 5750
	obsid = "BIG61"
	sysid = "MCOVER"

	def open(self):
		return self.command("OPEN")


	def close(self):
		return self.command("CLOSE")

	def state(self):
		return self.request("STATE")

		
	
class dome_slit(tcs_device):
	ip = "10.30.3.68"
	port = 5750
	obsid = "BIG61"
	sysid = "UDOME"

	def open(self):
		return self.command("OPEN")


	def close(self):
		return self.command("CLOSE")

	def state(self):
		return self.request("STATE")
	

CLOSED = 0
OPENED = 1
OPENING = 2
CLOSING = 3
ERROR = 4



class GotoApp(Frame):
	def __init__( self, master, tel ):
		Frame.__init__( self )

		self.tel=tel
		row = 0
		column = 0
		self.enableButton = Button( self, text="Start", bg="yellow", command=self.toggleEnable, **buttonStyle )
		# we don't really need a large disable button. 

		self.winfo_toplevel().title("RTS2 Startup and Safety")
		self.mc = mirror_cover()
		self.slit = dome_slit()
		self.mc_state =None
		self.slit_state = None
		self.domestate = Button(self, text="AutoDome On", bg="green", command=self.toggleAutoDome)	
		#self.domestate.grid(row=2, column=1)
		cancelButton = Button( self, text="Cancel", bg="red", command=self.tel.comCANCEL, **buttonStyle )
		cancelButton.grid( row=1, column=2, sticky="sw", padx=10, pady=10 )

		self.mcoverButton = Button(self, text='Open Mirror Cover', command=self.toggleMC )
		self.mcoverButton.grid(row=2, column=1) 

		
		self.slitButton = Button(self, command=self.toggleSlit )
		self.slitButton.grid(row=3, column=1) 

		domeinit = Button(self, text="Init Dome", bg="green", command=lambda: self.tel.command("DOME INIT"))
		domeinit.grid(row=2, column=2)

		self.startEndButton = Button(self, text="Start Night", bg="green",  command=lambda: self.toggle_start_end(), **startEndStyle )
		self.startEndButton.grid(row=1, column=1)

		stow = Button(self, text="Stow Tel", bg="green", command=self.tel.comMOVSTOW)
		#stow.grid(row=3, column=1)	
		self.observing = False
		self.last_observing_state = False

		try:
			if self.slit.state() == "OPENED":
				self.slit_state = OPENED
				self.slitButton.configure(text="Close Dome", bg="red")
			else:
				self.slit_state = CLOSED
				self.slitButton.configure(text="Open Dome", bg="green")
		except Exception as err:
			self.slit_state = ERROR
			self.slitButton.configure(text="Dome Error", bg="gray")
			
		try:
			if self.mc.state() == "OPENED":
				self.mc_state = OPENED
				self.mcoverButton.configure(text="Close Mirror Cover", bg="red")
			else:
				self.mc_state = CLOSED
				self.mcoverButton.configure(text="Open Mirror Cover", bg="green")
		except Exception as err:
			self.mc_state == ERROR
			self.mcoverButton.configure(text="Mirror Cover Error", bg="gray")

		self.UPDATE()
	
	def toggle_start_end( self ):
		if self.observing == False:
			self.startEndButton.configure({"text":"End of Night"})
			self.tel.comENABLE()
			self.tel.command("DOME AUTO ON")
			
			self.observing = True
		
		else:
			self.tel.comMOVSTOW()
			self.startEndButton.configure({"text": "Start Night"})
			self.tel.command("DOME STOW")
			self.observing = False
		
		
	def toggleEnable( self ):
		if self.tel.reqDISABLE():
			self.tel.comENABLE()
			self.tel.comDomeAutoOn()
		else:
			self.tel.comDISABLE()

	def cancel(self)	:
		self.tel.comCANCEL()
		self.tel.comDOME("AUTO OFF")

	def toggleMC(self):
		print("TOGGLING MC")
		if self.mc_state == OPENED:
			self.mc.close()
			self.mc_state = CLOSING

		elif self.mc_state == CLOSED:
			self.mc.open()
			self.mc_state = OPENING

		
			
	def toggleSlit(self):
		print("TOGGLING slit")
		if self.slit_state == OPENED:
			self.slit.close()
			self.slit_state = CLOSING

		elif self.slit_state == CLOSED:
			self.slit.open()
			self.slit_state = OPENING

	def toggleAutoDome(self):
		dm=int(self.tel.reqDOME()["mode"])
		if dm == 1:
			self.tel.command("DOME AUTO OFF")
			self.tel.command("DOME STOW")
			self.domestate.configure(**{"text":"AutoDome On", "bg":"yellow"})
		else:
			self.tel.command("DOME AUTO ON")
			self.domestate.configure(**{"text":"AutoDome Off and Stow", "bg":"green"})

	def UPDATE( self ):

		try:
			if self.tel.reqDISABLE():
				self.enableButton.configure( **{"text":"Start", "bg":"green"} )
			else:
				self.enableButton.configure( **{"text":"STOP!!", "bg":"red"} )
			if int(self.tel.reqDOME()["mode"]) == 1:
				 self.domestate.configure(**{"text":"AutoDome Off and Stow", "bg":"green"})
			else:
				self.domestate.configure(**{"text":"AutoDome On", "bg":"yellow"})

			if self.observing is False and self.last_observing_state is not False:
				if float(self.tel.request("MOTION")) == 0:
					self.tel.comDISABLE()
					self.last_observing_state = False
			else:
				self.last_observing_state = self.observing
		except telComError:
			pass

		
		try:
			mc_cur_state = self.mc.state()
			if self.mc_state == ERROR:
				if mc_cur_state == "OPENED":
					self.mc_state = OPENED
				elif mc_cur_state == "CLOSED":
					self.mc_state = CLOSED
				
		except Exception as err:
			mc_cur_state = "ERROR"
			self.mc_state = ERROR

		
		if self.mc_state is OPENING:
			if mc_cur_state == "OPENED":
				self.mcoverButton.configure(state=NORMAL)
				self.mcoverButton.configure(text="Close Mirror Cover", bg="red")
				self.mc_state = OPENED
			else:
				self.mcoverButton.configure(state=DISABLED)
				self.mcoverButton.configure(text="Opening Mirror Cover...")

		
		elif self.mc_state is CLOSING:
			self.mcoverButton.configure(state=DISABLED)
			if mc_cur_state == "CLOSED":
				self.mcoverButton.configure(state=NORMAL)
				self.mcoverButton.configure(text="Open Mirror Cover", bg="green")
				self.mc_state = CLOSED
				
			else:
				self.mcoverButton.configure(state=DISABLED)
				self.mcoverButton.configure(text="Closing Mirror Cover...")

		try:
			slit_cur_state = self.slit.state()
			if self.slit_state == ERROR:
				if slit_cur_state == "OPENED":
					self.slit_state = OPENED
				elif slit_cur_state == "CLOSED":
					self.slit_state = CLOSED
		except Exception as err:
			self.slit_state = ERROR
			slit_cur_state = "ERROR"
			
			

		if self.slit_state is OPENING:
			if slit_cur_state == "OPENED":
				self.slitButton.configure(state=NORMAL)
				self.slitButton.configure(text="Close Dome", bg="red")
				self.slit_state = OPENED
			else:
				self.slitButton.configure(state=DISABLED)
				self.slitButton.configure(text="Opening Dome...")

		
		elif self.slit_state is CLOSING:
			self.slitButton.configure(state=DISABLED)
			if slit_cur_state == "CLOSED":
				self.slitButton.configure(state=NORMAL)
				self.slitButton.configure(text="Open Dome", bg="green")
				self.slit_state = CLOSED
				
			else:
				self.slitButton.configure(state=DISABLED)
				self.slitButton.configure(text="Closing Dome...")

			
		self.after( 500, self.UPDATE )


			
if __name__ == "__main__":
	root = Tk()
	main = Frame( root )
	main.pack()
	app = GotoApp( main, telescope("10.30.5.69", "BIG61") )
	app.pack()

	root.mainloop()
	
	
