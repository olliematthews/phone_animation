# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 17:46:06 2020

@author: Ollie
"""
import numpy as np
import matplotlib.pyplot as plt
from draw_phone import plot_orientation
import socket, traceback, select
import multiprocessing as mp
import time

def get_orientation(lock):
    '''
    Safely get orientation from the temporary file.
    
    Parameters
    ----------
    lock : mp.Lock
        Lock used for synchronising access to the temporary file.

    Returns
    -------
    orientation : np.array of floats
        The orientation of the phone in alpha, beta, gamma.

    '''
    # Read the orientation data. Ensure the other thread has not opened the 
    # file at the same time
    lock.acquire()    
    with open('temp.txt', 'rb') as file:
        file.seek(0)
        data = file.read().decode()
    lock.release()

    # Find and read in the orientation data
    entries = np.array(data.split(',')).astype(float)
    index = np.squeeze(np.where(entries == 81))
    orientation = np.array(entries[index + 1 : index + 4])
    
    
    return orientation

def update_image(ax, lock, phone_dims):
    '''
    Update the plot according to the current orientation.

    Parameters
    ----------
    ax : plt.axis
        The axis for the plot.
    lock : mp.Lock
        Lock for synchronisation.

    Returns
    -------
    None.

    '''
    
    orientation = get_orientation(lock)
    plot_orientation(ax, orientation, phone_dims)
    
def client(lock, file_name):
    '''
    Reads a datastream from a socket. The data is sent by the "IMU + GPS 
    Stream App" for android. Writes the most recent orientation data to a file
    and writes all data into a csv file.
    
    Parameters
    ----------
    lock : mp.Lock
        Pass in a lock for synchronisation.
    file_name : string
        The file name for logging data

    Returns
    -------
    None.

    '''
    
    # Lookup data for each sensor reading. 'number' is the integer identifier
    # sent by the app before the data, 'n_col' is the number of readings for
    # the sensor (e.g. x, y, and z readings for accelerometer)
    lookup = [
        {'name' : 'Accelerometer', 'number' : 3, 'n_col' : 3},
        {'name' : 'GyroScope', 'number' : 4, 'n_col' : 3},
        {'name' : 'Magnetic Field', 'number' : 5, 'n_col' : 3},
        {'name' : 'Orientation', 'number' : 81, 'n_col' : 3}
        ]

    numbers = [sensor['number'] for sensor in lookup]
    
    # Create the header for writing to the logging file
    column_name_line = 'Time,'
    for sensor in lookup:
        for i in range(sensor['n_col']):
            column_name_line += sensor['name'] + ' ' + str(i) + ','
    column_name_line += '\n'
    
    
    # Open the csv file with write only permission
    with open(file_name, 'wb') as file:
        # Write the header to the csv
        file.write(column_name_line.encode())
        
        
        # Socket information (port needs to match port used in the app)
        host = ''
        port = 5555
        
        # Set up client
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind((host, port))
            print('Waiting to recieve data...')
            
            # Process the stream...
            read_write(s, file, numbers, 10, lock) 
            while(1):
                read_write(s, file, numbers, 1, lock)


def read_write(s, write_file, numbers, timeout, lock):
    '''
    Read in data from the socket. Write it to the write_file, and write the 
    orientation to a temporary file. Exits if there is timeout.
    
    Parameters
    ----------
    s : socket
        Socket which reads in the data from the app.
    write_file : fd
        File descriptor for the file to be written to.
    numbers : int array
        The identifiers for each sensor.
    timeout : int / float
        The maximum innactivity time from the socket before exiting.
    lock : mp.Lock
        Lock for synchronisation.

    Returns
    -------
    None.

    '''
    try:
        start_time = time.time()
        while(1):
            # Make sure recvfrom does not block other threads
            ready = select.select([s], [], [], 0.001)
            if ready[0]:
                message, address = s.recvfrom(8192)
                break
            else:
                time.sleep(0.001)
                if time.time() - start_time >= timeout:
                    print('Timeout')
                    raise SystemExit
            

        write_string = ''
        rest = message.decode() 

        while(1):
            loc = rest.find(',')
            if loc == -1:
                write_string += rest +'\n'
                break
            else:
                seg = rest[:loc]
                num = float(seg)
                rest = rest[loc + 1 :]
                
            if not num in numbers:
                write_string += seg + ','
            elif num == 81:
                lock.acquire()
                with open('temp.txt', 'wb') as temp_file:
                    temp_file.write(message)   
                lock.release()
                    
        message_line = (write_string).encode()
        write_file.write(message_line)

        print (message)
    
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        traceback.print_exc()

def animations(lock, framerate, phone_dims):
    '''
    Main thread for animations. Updates the plot at the framerate.
    Parameters
    ----------
    lock : mp.Lock
        For synchronisation.
    framerate : float
        Number of frames per second.

    Returns
    -------
    None.

    '''
    fig = plt.figure(figsize = (8,8))
    plt.ion()
    ax = fig.add_subplot(111, projection='3d')
    T = 1 / framerate
    while(1):
        update_image(ax, lock, phone_dims)
        plt.pause(T)

def main(file_name, framerate, phone_dims):
    '''
    Main function. Calls client and animation.

    Parameters
    ----------
    file_name : string
        The name of the file for the data to be saved. Should be .csv .

    Returns
    -------
    None.

    '''
    # Write in initial orientation
    text = '81,360,0,0\n'
    with open('temp.txt', 'wb') as temp_file:
        temp_file.write(text.encode())
        
    lock = mp.Lock()    
    
    client_process = mp.Process(target = client, args = (lock,file_name))
    animation_process = mp.Process(target = animations, args = (lock, framerate, phone_dims))
    animation_process.start()
    
    # Allow time for plot to generate
    plt.pause(0.5)
    
    # Start the client, kill the animation process when the client terminates.
    client_process.start()
    client_process.join()
    animation_process.terminate()
  
if __name__ == '__main__':
    file_name = 'log_file.csv'
    phone_dims = np.array([0.8,0.4,0.1])
    framerate = 10
    
    main(file_name, framerate, phone_dims)

    