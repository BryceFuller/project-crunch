import os
import sys
from shutil import copyfile
import subprocess
from fbs_runtime.application_context import ApplicationContext
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                            QMessageBox, QInputDialog, QLineEdit, QFileDialog,
                           QDialogButtonBox, QMainWindow, QLabel)
from PyQt5.QtCore import QObjectCleanupHandler

class AppContext(ApplicationContext):
    """
    The AppContext holds the installer application. It serves to set up the
    main application, and wraps several bash scripts.

    The installer is a series of nested push-button functions, starting with
    first_page. The user is prompted for several bits of information, with 
    each information request leading to a new input dialog page. After all
    the information is collected, the exec_install function performs the core
    of the installation. Adding or modifying a step in the installation 
    process should occur within this exec_install function. If more information
    is required from the user, an input dialog function can be chained to the 
    end of the current chain.

    A similar chain of events happens for the ssh config button, prompting the
    user, then the core action happens inside #TODO function.
    """
    
    password = None
    install_dir = None
    catkin_dir = None
    current_computer_is_base = None
    use_default_net_config = None
    robot_username = None
    robot_password = None
    robot_hostname = None
    
    def run(self):
        # Set up window
        self.window = QWidget()
        self.window.setLayout(self.first_page())
        self.window.resize(250,150)
        self.window.show()
        
        # Set default params
        self.ip_configs = {
            "robot_ip": "10.0.0.2",
            "base_ip": "10.0.0.1",
            "robot_hostname": "robot",
            "base_hostname": "base"
        }
        self.use_default_net_config = True
        return self.app.exec_()
    
    def first_page(self):
        """
        Create layout of the first page.
        """
        layout = QVBoxLayout()
        install_button = QPushButton('Install Project Crunch')
        install_button.clicked.connect(self.on_install_push)
        ssh_config_button = QPushButton('Configure SSH Keys')
        ssh_config_button.clicked.connect(self.on_ssh_config_push)
        exit_button = QPushButton('Exit')
        exit_button.clicked.connect(self.on_exit_push)

        # Add buttons 
        layout.addWidget(install_button)
        layout.addWidget(ssh_config_button)
        layout.addWidget(exit_button)
        return layout

    def on_exit_push(self):
        sys.exit()        

    def on_install_push(self): 
        """
        Prompt user for password.
        """
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        text, ok = dialog.getText(
                QWidget(), 
                'Administrative Privileges Needed!', 
                'Please enter the password for the admin (root) user.', 
                QLineEdit.Password, 
                ""
        ) 
        if ok:
            self.password = str(text)
            if self.is_password_correct():
                self.select_comp()
            else:
                self.password_incorrect()    
        else:
            self.password = None
            self.first_page()
        return layout 

    def is_password_correct(self):
        """
        This function tries the password assigned to self to run a test sudo 
        command. If the password is correct, the command makes a harmless echo
        and the function returns true. If incorrect, subprocess throws an 
        exception and we return false. Warning this has not been checked for
        security vulnerabilities.
        """
        try:
            out = subprocess.Popen(
                    ['echo', self.password], stdout=subprocess.PIPE)
            subprocess.check_output(
                    ['sudo', '-S', 'echo','testing', 'password'], stdin=out.stdout) 
            out.wait()
        except subprocess.CalledProcessError:
            return False
        return True

    def password_incorrect(self):
        """
        This function tells the user they put in the wrong password and asks
        them to try again. It returns the user to the password input screen.
        """
        QMessageBox.about(self.window, "Incorrect Password", "The password entered was incorrect.\n" +
                "Please try again.")
        self.on_install_push()

    def select_comp(self):
        """
        Prompt user for whether they are on robot or base computer.

        Assigns result to boolean class variable.
        """
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        item, ok = dialog.getItem(
                     QWidget(),
                     'Select Computer: Robot or Base',
                     "Which computer are you installing from?",
                     ['Robot','Base'],
        )
        if ok:
            if str(item).lower() == "base":
                self.current_computer_is_base = True
            elif str(item).lower() == "robot":
                self.current_computer_is_base = False
            # We only need the install directory if the user is on the robot
            if self.current_computer_is_base is False:
                self.install_directory()
            else:
                self.catkin_directory()
        else:
            self.first_page()
        return layout
    
    def install_directory(self):
        """
        Prompt user for directory to install app.
        
        Assigns the install directory to self as a full path.
        """
        layout = QVBoxLayout()
        dialog = QFileDialog()
        layout.addWidget(dialog)
        text = dialog.getExistingDirectory(
                QWidget(), 
                'Please choose the directory where you wish to install Project Crunch.' 
        )
        if text == "":
            self.install_directory() # TODO Where should this go? What triggers this event?
        else:    
            self.install_dir = str(text)
            self.catkin_directory() # change to dialog box
        return layout

    def install_info(self):
        """
        This is a dialog box to warn the user. If you are on the robot, you are 
        prompted for the install directory, although we can't actually move the
        application to the install directory for you. We tell the user this, and
        let them know they will have to move the application to this directory
        at the end of the process. 
        """
        #TODO make note of this in the FAQ- moving into wrong dir could break the app
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        item, ok = dialog.getItem(
                     QWidget(),
                     'Chosen Install Directory',
                     'Once the install process has finished, you must copy the application over into its final destination, which you just chose. Be sure to write it down if needed, the install process can take up to twenty minutes on a clean machine.\nThe install directory you chose is:\n{}'.format(self.install_directory),
                     ['OK'],
        )
        if ok:
            self.catkin_directory()
        return layout

    def catkin_directory(self):
        """
        Prompt user for catkin workspace.

        Assigns the catkin directory to self as a full path.
        """
        layout = QVBoxLayout()
        dialog = QFileDialog()
        layout.addWidget(dialog)
        text = QFileDialog.getExistingDirectory(
                QWidget(), 
                'Please choose the directory where you wish to create your catkin workspace.', 
        )
        if text == "":
            self.catkin_directory() # TODO Where should this go? What triggers this event?
        else:
            self.catkin_dir = str(text)
            self.catkin_info()
        return layout

    def catkin_info(self):
        """
        This function lets the user confirm the catkin directoryp that they selected.
        """
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        item, ok = dialog.getItem(
                     QWidget(),
                     'Chosen Catkin Directory',
                     'The catkin directory you chose is:\n{}\nIf this is incorrect, please hit cancel to select a different directory.'.format(self.catkin_directory),
                     ['OK'],
        )
        if ok:
            self.configure_ip()
        else:
            self.catkin_directory()
        return layout
   
    def configure_ip(self):
        """
        Prompt user for whether they want custom IP and hostnames.

        If yes, next window is called and gets them. Else we execute
        the install process.
        """
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        item, ok = dialog.getItem(
                     QWidget(),
                     'Configuring IPs',
                     'Do you have custom IP configurations you would like to enter?',
                     ['No', 'Yes'],
        )
        if ok:
            if str(item).lower() == "yes":
                self.get_custom_ip_settings()
            elif str(item).lower() == "no":
                self.exec_install()
        else:
            self.first_page()
        return layout

    def get_custom_ip_settings(self):
        """
        Prompt user for whether they want custom IP and hostnames.

        """
        #TODO validate ip add
        # https://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python	
        widget = QWidget()
        base_ip_dialog = QInputDialog()
        robot_ip_dialog = QInputDialog()
        base_hostname_dialog = QInputDialog()
        robot_hostname_dialog = QInputDialog()
        base_ip, ok_1 = base_ip_dialog.getText(
                widget,
                '',
                'Enter the desired IP for the base station.\n\
                        Leave this field blank to use the defaults.', 
                QLineEdit.Normal, 
                '' 
        )#TODO does this work?? 
        if ok_1:
            robot_ip, ok_2 = robot_ip_dialog.getText(
                    widget,
                    '',
                    'Enter the desired IP for the robot station.\n\
                            Leave this field blank to use the defaults.', 
                    QLineEdit.Normal, 
                    '' 
            )
            if ok_2:
                self.ip_configs['base_ip'] = base_ip
                self.ip_configs['robot_ip'] = robot_ip
                self.exec_install()
        else:
            self.password = None
            self.first_page()
    
    def exec_install(self):
        """
        Install process on press of install button.
        
        This executes the core functionality of the install process. In a
        nutshell, the steps are as follows:

          1. Export necessary environment variables to bashrc that are 
             needed for the main app.
          2. Run a bash script to set up a catkin workspace, install 
             dependencies via apt, and set up all the source code for the 
             catkin workspace.
          3. Copy over any necessary configuration and launch files into
             the catkin workspace.
          4. Run a bash script to set up the network configurations.

        """
        
        # Tell the user not to worry about the program appearing to crash.
        # Note: this will halt the code here until the 'OK' button in the message box is clicked.
        # This will solve the problem for now but should have a better solution in the future.
        QMessageBox.about(self.window, "Installing", "This process can take up to 20 min. The window may appear" +
            "to stop responding, but we are installing in the background. Click 'OK' to begin.")

        # Export environment variables no matter what machine we are on (robot
        # or base.) We collect the envs from the opposite machine when the
        # user runs ssh config. Envs are written to the bashrc. Ideally they
        # are pruned at some point, but for now they just add new ones. This 
        # is OK because the new var is written to the end of the bashrc and 
        # so the definition overwrites any previous one. We need to check the 
        # current computer because the catkin workspace could be different.
        path_to_bashrc = os.path.join(os.path.expanduser('~'), '.bashrc')
        if self.current_computer_is_base is False:
            with open(path_to_bashrc, "a") as f:
                f.write("export ROBOT_CATKIN_PATH={}\n".format(self.catkin_dir))
                f.write("export ROBOT_PROJECT_CRUNCH_PATH={}\n"\
                    .format(self.install_dir)) 
        else:        
            with open(path_to_bashrc, "a") as f:
                f.write("export BASE_CATKIN_PATH={}\n".format(self.catkin_dir)) 

        # Determine which computer we are on 
        if self.current_computer_is_base == True:
            is_base = "y"
        else:
            is_base = "n"

        # Set up catkin workspace and install dependencies.
        # Script also sets up local hardware configurations for
        # Vive and OpenHMD.
        # Bash arguments are passed in via a dictionary and must match the
        # command line arguments of the script.
        # We pass in is_base to skip the OpenHMD installation if we are on
        # the robot computer.
        install_args = [
            '-c', '{}'.format(self.catkin_dir), 
            '-p', '{}'.format(self.password),
            '--is_base', is_base,
            '--openhmdrules', '{}'.format(self.get_resource('50-openhmd.rules')),
            '--viveconf', '{}'.format(self.get_resource('50-Vive.conf'))
        ]
        subprocess.run(
                [
                    'bash', 
                    self.get_resource('install.sh'), 
                    *install_args
                ], 
                check=True
        )

        # Copy over necessary configuration files
        # Still need openhmd file ## TODO fix last launch file #TODO 4/4/19 are these comments still accurate?
        single_cam_launch = 'single-cam.launch'
        dual_cam_launch = 'dual-cam.launch'
        vive_launch = 'vive.launch'
        opencv_dir = 'video_stream_opencv'
        txtsphere_dir = 'rviz_textured_sphere'

        txtsphere_dest_dir = os.path.join(self.catkin_dir, 'src', txtsphere_dir, 'launch')
        opencv_dest_dir = os.path.join(self.catkin_dir, 'src', opencv_dir, 'launch')

        # Copy single cam launch
        file_dest = os.path.join(opencv_dest_dir, single_cam_launch)
        if not os.path.isfile(file_dest):
            copyfile(self.get_resource(single_cam_launch), file_dest) 
        
        # Copy dual cam launch
        file_dest = os.path.join(opencv_dest_dir, dual_cam_launch)
        if not os.path.isfile(file_dest):
            copyfile(self.get_resource(dual_cam_launch), file_dest)
        
        # Copy rviz launch file
        file_dest = os.path.join(txtsphere_dest_dir, vive_launch)
        if not os.path.isfile(file_dest):
            copyfile(self.get_resource(vive_launch), file_dest)

        ip_args = [
            '--is_base', is_base,
            '--robot_ip', self.ip_configs['robot_ip'], 
            '--base_ip', self.ip_configs['base_ip'], 
            '--robot_hostname', self.ip_configs['robot_hostname'],
            '--base_hostname', self.ip_configs['base_hostname'], 
            '--password', '{}'.format(self.password)
        ]
        subprocess.run(
                [
                    'bash', 
                    self.get_resource('configure_network.sh'), 
                    *ip_args
                ], 
                check=True
        )
        
        # TODO catkin build /make
        # Set up icons?

        self.install_finished()

    def install_finished(self):
        """
        Lets the user know that they are finished with the install.

        """
        # TODO LOOK AT THIS COOL BOX I FOUND
        # We can use this to pop up the install done message
        #QMessageBox.about(self.window, "Install Complete", "The installation is complete!\n"+
        #    "Next you must restart the computer and configure SSH keys before launching.")
 
        layout = QVBoxLayout()
        dialog = QInputDialog()
        layout.addWidget(dialog)
        item, ok = dialog.getItem(
                     QWidget(),
                     'Install Complete!',
                     'You have completed the install process! Copy the Project-Crunch directory to the location of your choosing. You can run ' +
                     'Project Crunch by navigating to {} and clicking on the ' +
                     'FIX ME icon.\n\n You must restart your computer and ' + #TODO
                     'configure SSH keys before the application is fully ' +
                     'functional.',
                     ['OK'],
        )
        if ok:
            self.first_page()
        return layout
   
    def wrong_password(self):
        """
        Tells the user they input the wrong password and sends them back to the password screen.
        """
        QMessageBox.about(self.window, "Incorrect Password", "The password you entered was not correct.\n" +
                "Please try again.")
        self.on_install_push()
        pass

    def on_ssh_config_push(self):
        """
        This function begins execution of the SSH Key configuration chain of 
        events. The user is informed of assumptions, then is prompted for the
        robot username and password, as well as any custom hostname. The 
        configuration happens in the final step in exec_ssh_config().
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(
                "The installation must have already been run on both the robot " +
                "and the base station.\n\nBoth computers should have been restarted." +
		"\n\nThe two computers must be connected " +
                "with a crossover ethernet cable, and you will need the username " +
                "and password for the robot, as well as any custom hostname it " +
                "may have been assigned. This must be run from the base station."
        )
        msg.setWindowTitle("SSH key configuration")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        #These are macros for the return values for StandardButtons
        #https://www.tutorialspoint.com/pyqt/pyqt_qmessagebox.htm
        CANCEL_BUTTON = 0x00400000
        OK_BUTTON =  0x00000400
        
        # If user cancels we return, if they choose OK we ask for information and then
        # execute the configuration.
        retval = msg.exec_()
        if retval == CANCEL_BUTTON:
            return
        elif retval == OK_BUTTON:
            self.get_robot_username()
   
    def get_robot_username(self):
        """
        Prompt user for robot username.
        """
        dialog = QInputDialog()
        text, ok = dialog.getText(
                QWidget(),
                'SSH Key Configuration',
                'Please enter the username for the robot. This is the same'\
                + ' username that you log into Ubuntu with.',
                QLineEdit.Normal,
                ""
        )
        if ok:
            self.robot_username = str(text)
            self.get_robot_password()
        else:
            self.robot_username = None
            # TODO what should the Default be? Empty username will crash program
            self.first_page()
    
    def get_robot_password(self):
        """
        Prompt user for robot password.
        """
        dialog = QInputDialog()
        text, ok = dialog.getText(
                QWidget(),
                'SSH Key Configuration',
                'Please enter the password for the robot.',
                QLineEdit.Password,
                ""
        )
        if ok:
            self.robot_password = str(text)
            self.get_robot_hostname()
        else:
            self.robot_password = None
            self.first_page()

    def get_robot_hostname(self):
        """
        Prompt user for robot hostname for SSH key configuration. If there
        is none, the user should input an empty string.
        """
        dialog = QInputDialog()
        text, ok = dialog.getText(
                QWidget(),
                'SSH Key Configuration',
                'If you installed with custom IP configurations, enter the '\
                + 'robot hostname now. Otherwise leave this entry blank.',
                QLineEdit.Normal,
                ""
        )
        if ok:
            if str(text) == "":
                self.robot_hostname = self.ip_configs['robot_hostname']
            else:
                self.robot_hostname = str(text)
            self.exec_ssh_config()
        else:
            self.robot_hostname = None
            self.first_page()
    
    def exec_ssh_config(self):
        """
        This function takes the previously robot password, username, and 
        hostname and executes a bash script to complete the actual 
        configuration steps.
        """
        ssh_config_args = [
            '--password', '{}'.format(self.robot_password),
            '--username', '{}'.format(self.robot_username),
            '--hostname', '{}'.format(self.robot_hostname)
        ]
        subprocess.run(
                [
                    'bash', 
                    self.get_resource('configure_ssh_keys.sh'), 
                    *ssh_config_args
                ], 
                check=True
        )
        

if __name__ == "__main__":
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)
