import json
import re
from os import path
from time import sleep

import PIL.ImageGrab
from colormath.color_conversions import convert_color
from colormath.color_objects import XYZColor, sRGBColor
from qhue import Bridge, QhueException, create_new_username

CONFIG_FILE_PATH = 'photon_config.json'


def get_config():
    if not path.exists(CONFIG_FILE_PATH):
        ipaddress = ''

        while not re.fullmatch('^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.?\\b){4}$', ipaddress):
            ipaddress = input("Enter bridge IP address: ")

        while True:
            try:
                username = create_new_username(ipaddress)
                break
            except QhueException as error:
                print("An error has occurred while connecting to the bridge: {}".format(error))

        with open(CONFIG_FILE_PATH, "w") as config_file:
            json.dump({'ipaddress': ipaddress, 'username': username, }, config_file)

    else:
        with open(CONFIG_FILE_PATH, "r") as config_file:
            config = json.load(config_file)
            ipaddress, username = config['ipaddress'], config['username']

    return ipaddress, username


def main():
    ipaddress, username = get_config()

    bridge = Bridge(ipaddress, username)
    lights = bridge.lights()
    groups = bridge.groups()

    print("Available lights: \n")

    for group_id in groups:
        group = groups[group_id]
        print(group['name'])
        for light_id in group['lights']:
            print("  {}: {}".format(light_id, lights[light_id]['name']))

    light_id = input("\nEnter light ID: ")

    try:
        while True:
            sleep(0.75)

            image = PIL.ImageGrab.grab()

            rs_image = image.resize((1, 1))
            average_color = rs_image.getpixel((0, 0))

            bri = int(0.2126 * average_color[0] + 0.7152 * average_color[1] + 0.0722 * average_color[2])
            rgb_color = sRGBColor(*average_color)

            xyz_color = convert_color(rgb_color, XYZColor)
            x = xyz_color.xyz_x / max((xyz_color.xyz_x + xyz_color.xyz_y + xyz_color.xyz_z), 0.05)
            y = xyz_color.xyz_y / max((xyz_color.xyz_x + xyz_color.xyz_y + xyz_color.xyz_z), 0.05)

            bridge.lights[int(light_id)].state(transitiontime=100, on=True, bri=bri, xy=[x, y])

    except QhueException as error:
        print("An error has occurred while setting the light state: {}".format(error))


if __name__ == '__main__':
    main()
