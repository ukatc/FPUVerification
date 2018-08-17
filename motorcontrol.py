import static java.lang.System.out;
import java.io.IOException;

// somewhat frugal options parser
import org.apache.commons.cli.Options;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.ParseException;

// serial port access via rxtx library
import gnu.io.*;
import Thorlabs_Motor.Thorlabs_Motor;
import gnu.io.SerialPort;

class MotorControl{

    private static void printHelp()
        {
            out.println("Thorlabs motor control. Available commands:\n\n"
                        + "info                                    - print list of available serial devices\n"
			+ "                                          and movement units\n"
                        + "status [-D device]                      - retrieve and print status of device\n"
			+ "switchparams [-C cw_hard_mode] [ -A acw_hard_mode ] [ -c cw_soft_limit ] [-a acw_soft_limit ] [-m soft_mode]\n"
			+ "                                        - set modes of limit switch and soft limit values\n"
                        + "home [-D device] [-s speed] [-d direction={cw,acw}] [-l switch selection]- home device\n"
			+ "                                          (may require correct limit switch settings)\n"
			+ "identify [-D device]                    - identify device by flashing LED\n"
			+ "jogfw [-D device]                       - jog forward / anticlockwise\n"
			+ "jogbw [-D device]                       - jog backward / clockwise\n"
                        + "getpos [-D device]                      - get position\n" 
                        + "moveabs pos [-D device]                 - move absolute to pos\n"
                        + "moverel pos [-D device]                 - move relative to pos\n"
			+ "                                          (use \"(-x)\" for negative arguments)\n"
			+ "stop  [-D device] [-p ]                 - stop motor (with '-p': in profiled mode)\n"
                        + "setpos pos [-D device]                  - set encoder position\n"
			+ "Options:\n\n"
			+ "[-F ]                                   - send no-flash message\n"
			);
        }

    private static CommandLine parseOptions(String args[])
        {
            Options options = new Options();
            options.addOption("D", "device", true, "device name");
            options.addOption("d", "direction", true, "direction");
            options.addOption("s", "speed", true, "speed");
            options.addOption("p", "profiled", false, "profiled");
            options.addOption("h", "help", false, "help");
            options.addOption("l", "lswitch", true, "lswitch");
            options.addOption("A", "hw_acw", true, "hw_acw");
            options.addOption("C", "hw_cw", true, "hw_cw");
            options.addOption("a", "s_acw", true, "s_acw");
            options.addOption("c", "s_cw", true, "s_cw");
            options.addOption("m", "s_mode", true, "s_mode");
            options.addOption("F", "no_flash", false, "no_flash");
            
            CommandLineParser parser = new DefaultParser();
            CommandLine cl = null;
            try {
                cl = parser.parse(options, args); 
            }
            catch(ParseException pe)            
            {
                out.println("could not parse arguments!\n" + pe);
                System.exit(1);
            }
            if (cl.hasOption("h"))
            {
                printHelp();
		System.exit(0);
            }
            return cl;
        }


    private static SerialPort getDevice(String portName)
        {
            /* from the Thorlabs protocol document:
               2.3  RS-232 Interface

               The RS-232 interface uses the 9-way D-Type male connector 
               on the rear panel, marked ‘INTERCONNECT’. Communications 
               parameters are fixed at:

               115200 bits/sec
               
               8 data bits,
               1 stop bit

               No parity

               No handshake
            */

	    	    
            int baudrate =115200;
	    String appname = "ThorlabsMotorControl";
	    int timeout = 5000; // milliseconds

            try {
                
		CommPortIdentifier portIdentifier = CommPortIdentifier.getPortIdentifier(portName);
		if ( portIdentifier.isCurrentlyOwned() )
		    {
			System.out.println("Error: Port is currently in use");
			return null;			
		    }
		else
		    {
			CommPort commPort = portIdentifier.open(appname, timeout);
            
			if ( commPort instanceof SerialPort )			    {
			    SerialPort serialPort = (SerialPort) commPort;
			    serialPort.setSerialPortParams(baudrate,
							   SerialPort.DATABITS_8,
							   SerialPort.STOPBITS_1,
							   SerialPort.PARITY_NONE);

			    serialPort.setFlowControlMode(SerialPort.FLOWCONTROL_NONE);
			    return serialPort;
			}
			else			    {
			    System.out.println("Error: Only serial ports are allowed.");
			    return null;
			}
		    }                 
            }

	    catch (Throwable ex)
            {
                out.println("cannot open device '" + portName + "'- exit!\n" + ex);
		System.exit(1);
            }
	    return null;
        }


    static void listPorts()
        {
	    out.println("list of available ports:");
            java.util.Enumeration<CommPortIdentifier> portEnum = CommPortIdentifier.getPortIdentifiers();
            while ( portEnum.hasMoreElements() ) 
            {
                CommPortIdentifier portIdentifier = portEnum.nextElement();
		String port_type = getPortTypeName(portIdentifier.getPortType());
		if (port_type == "Serial")
		    {
			try {
			    CommPort thePort = portIdentifier.open("CommUtil", 50);
			    thePort.close();
			    out.println(portIdentifier.getName()  +  " - " +  port_type );
			} catch (PortInUseException e) {
			    System.out.println("Port, "  + portIdentifier.getName() + ", is in use.");
			} catch (Exception e) {
			    System.err.println("Failed to open port " +  portIdentifier.getName());
			    e.printStackTrace();
			}
		    }
		
            }        
        }
    
    static String getPortTypeName ( int portType )
        {
            switch ( portType )
            {
            case CommPortIdentifier.PORT_I2C:
                return "I2C";
            case CommPortIdentifier.PORT_PARALLEL:
                return "Parallel";
            case CommPortIdentifier.PORT_RAW:
                return "Raw";
            case CommPortIdentifier.PORT_RS485:
                return "RS485";
            case CommPortIdentifier.PORT_SERIAL:
                return "Serial";
            default:
                return "unknown type";
            }
        }
    
    public static void main(String args[])  {
        CommandLine cl = null;
        

        cl = parseOptions(args);

        int argnum = cl.getArgs().length;
	if (argnum < 1){
	    printHelp();
	    System.exit(1);
	}
        String command_name = cl.getArgs()[0].trim();
	out.println("command_name: " + command_name);
        if ( command_name.equals("setpos")
	     || command_name.equals("moveabs")
	     || command_name.equals("moverel")) {
	    if (argnum != 2) {
		out.println("this command needs an additional position argument\n\n");
		printHelp();
		System.exit(1);
	    }
	}
	else {
	    if (argnum != 1){
		out.println("needs a command as argument\n\n");
		printHelp();
		System.exit(1);
	    }
	}
	
	    
	String default_device = System.getenv("THORLABS_DEVICE");
	if (default_device == null){
	    if (System.getProperty("os.name").equals("Linux")){
		default_device = "/dev/ttyUSB0";
	    } else {
		default_device = "COM0:";
	    }
	}
	String device_name=cl.getOptionValue("D", default_device);
            
	if (command_name.equals("list") ){
	    listPorts();
	    System.exit(0);
	}
	
	out.println("device name:" + device_name);
	out.println("command: '" + command_name + "'");


        
	SerialPort device = getDevice(device_name);
	if (device == null) {
	    System.exit(1);
	}

	try {
	    Thorlabs_Motor motor = new Thorlabs_Motor(device);

	    if (cl.hasOption("F")){
		motor.sendNoFlashMsg();
	    }

	    if (command_name.equals("identify")) {
		motor.Identify();
	    }
	    else if (command_name.equals("info")) {
		int serial_number = motor.GetSerialNumber();
		out.println("Device info:\n" + motor.toString() );
		out.println("Position Unit:" + motor.GetUnits() );
	    }
	    else if (command_name.equals("status")) {
		Thorlabs_Motor.ThorlabsStatus status = motor.GetStatus();
		out.println("Motor status:\n" + status.toString() );
	    }
	    else if (command_name.equals("switchparams")) {
		short cw_hard_mode = Short.valueOf(cl.getOptionValue("C","2"));
		short acw_hard_mode = Short.valueOf(cl.getOptionValue("A","2"));
		double cw_soft_limit = Double.valueOf(cl.getOptionValue("c", "10.0"));
	        double acw_soft_limit = Double.valueOf(cl.getOptionValue("a", "10.0"));
		short soft_mode = Short.valueOf(cl.getOptionValue("m","1"));
		
		motor.SetLSwitchParams(cw_hard_mode, acw_hard_mode,
				       cw_soft_limit, acw_soft_limit, soft_mode);
	    }
	    else if (command_name.equals("home")) {
		short lswitch = Short.valueOf(cl.getOptionValue("l", "1000"));
		double speed = Double.valueOf(cl.getOptionValue("s", "0.1"));
		boolean dir= true;
		String dircode = cl.getOptionValue("d", "acw");
		if (dircode.equals("acw"))
		    {
			dir = false;
		    }
		motor.SetHomeConfig(dir, speed, lswitch);                
                
		motor.Home();
	    }
	    else if (command_name.equals("getpos")) {
		double pos = motor.GetPosition();
		out.println("current pos:" + pos + " " + motor.GetUnits());                
	    }
	    else if (command_name.equals("setpos")) {
		double pos = Double.valueOf(cl.getArgs()[1]);
		motor.SetPosition(pos);
	    }
	    else if (command_name.equals("moveabs")) {
		double pos = Double.valueOf(cl.getArgs()[1].replaceAll("[()]",""));
		motor.moveAbsolute(pos);
	    }
	    else if (command_name.equals("moverel")) {
		double pos = Double.valueOf(cl.getArgs()[1].replaceAll("[()]",""));
		motor.moveRelative(pos);
	    }
	    else if (command_name.equals("jogfw")) {
		motor.JogForward();
	    }
	    else if (command_name.equals("jogbw")) {
		motor.JogBackward();
	    }
	    else if (command_name.equals("stop")) {
		boolean profiled = cl.hasOption("p");
		motor.stop(profiled);
	    }
	    else {
		out.println("command not found");
	    }
	    device.close();
		    

	} catch (IOException ex){
	    out.println("could not get Motor:\n");
	    out.println(ex);
	    System.exit(1);
	}

            
    }
    }
