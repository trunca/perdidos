from Screens.InfoBar import InfoBar
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Console import Console
from enigma import eConsoleAppContainer
from os import path, listdir, mkdir
from shutil import copyfile

class MultibootGigablue(ConfigListScreen, Screen):

	skin = """
	<screen name="MultibootGigablue" position="center,center" size="500,200"  flags="wfNoBorder" title="MultiBoot STARTUP Selector" backgroundColor="transparent">
		<eLabel name="b" position="0,0" size="500,200" backgroundColor="#00ffffff" zPosition="-2" />
		<eLabel name="a" position="1,1" size="498,198" backgroundColor="#00000000" zPosition="-1" />
		<widget source="Title" render="Label" position="10,10" foregroundColor="#00ffffff" size="480,50" halign="center" font="Regular; 35" backgroundColor="#00000000" />
		<eLabel name="line" position="1,69" size="498,1" backgroundColor="#00ffffff" zPosition="1" />
		<widget source="config" render="Label" position="10,90" size="480,60" halign="center" font="Regular; 30" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_red" render="Label" position="35,162" size="170,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_green" render="Label" position="228,162" size="170,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<eLabel position="25,159" size="6,40" backgroundColor="#00e61700" />
		<eLabel position="216,159" size="6,40" backgroundColor="#0061e500" />
	</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("MultiBoot Selector")
		self.list = []

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["config"] = StaticText(_("Select Image: STARTUP_1"))
		self.selection = 0

		self.checkMount()

		self["actions"] = ActionMap(["WizardActions", "SetupActions", "ColorActions"],
		{
			"left": self.left,
			"right": self.right,
			"green": self.save,
			"red": self.cancel,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.title)

	def checkMount(self):
		if not path.ismount("/media/mmc") or not path.isfile("/media/mmc/STARTUP"):
			try:
				mkdir("/media/mmc")
			except OSError:
				pass
			self.console = Console()
			self.console.ePopen("mount -t vfat /dev/mmcblk0p1 /media/mmc", self.getext4devices)
			return
		self.getext4devices()

	def setList(self):
		self.list = self.list_files("/media/mmc/")
		self.startup()

	def startup(self):
		self["config"].setText(_("Select Image: %s") %self.list[self.selection])

	def save(self):
		print "[MultiBootStartup] selected new startup: ", self.list[self.selection]
		copyfile("/media/mmc/%s" %self.list[self.selection], "/media/mmc/STARTUP") 
		restartbox = self.session.openWithCallback(self.restartBOX,MessageBox,_("Do you want to reboot now with selected image?"), MessageBox.TYPE_YESNO)

	def cancel(self):
		self.close()

	def left(self):
		self.selection = self.selection - 1
		if self.selection == -1:
			self.selection = len(self.list) - 1
		self.startup()

	def right(self):
		self.selection = self.selection + 1
		if self.selection == len(self.list):
			self.selection = 0
		self.startup()

	def read_startup(self, FILE):
		self.file = FILE
		with open(self.file, 'r') as myfile:
			data=myfile.read().replace('\n', '')
		myfile.close()
		return data

	def getext4devices(self, str = "", retval = None, extra_args = None):
		self.ext4devices = []
		self.blkid_out = ""
		if not retval or retval == 0:
			self.container = eConsoleAppContainer()
			cmd = "/usr/bin/blkid -t TYPE=ext4 -o device"
			self.container.appClosed.append(self.getext4devicesFinished)
			self.container.dataAvail.append(self.getext4devicesData)
			if self.container.execute(cmd):
				self.getext4devicesFinished(-1)

	def getext4devicesFinished(self, retval):
		if retval != -1:
			out = self.blkid_out.replace('\n', ',').rstrip(",")
			if out != "":
				self.ext4devices = [x.strip() for x in out.split(",")]
		self.setList()

	def getext4devicesData(self, data):
		self.blkid_out += data

	def restartBOX(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()

	def list_files(self, PATH):
		files = []
		self.path = PATH
		for name in listdir(self.path):
			if path.isfile(path.join(self.path, name)) and not name == "STARTUP":
				cmdline = self.read_startup("/media/mmc/" + name).split(" ")
				for c in cmdline:
					if "root=" in c:
						if c.split("=")[1] in self.ext4devices:
							files.append(name)
		return files

